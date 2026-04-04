from __future__ import annotations

import argparse
import hashlib
import json
import re
import sqlite3
from dataclasses import dataclass
from datetime import datetime, timezone
from pathlib import Path
from typing import Iterable


REPO_ROOT = Path.cwd()
DB_PATH = REPO_ROOT / ".harnessing" / "memory.db"
DEFAULT_SOURCES = [
    REPO_ROOT / ".codex",
    REPO_ROOT / "docs",
    REPO_ROOT / "README.md",
]
TRANSCRIPT_EXTENSIONS = {".txt", ".md", ".log", ".jsonl"}


@dataclass
class SectionRecord:
    path: str
    kind: str
    title: str
    heading: str
    level: int
    content: str
    tags: str
    content_hash: str


@dataclass
class MemoryRecord:
    kind: str
    title: str
    summary: str
    content: str
    tags: str
    origin: str
    source_path: str
    source_heading: str
    content_hash: str
    created_at: str
    updated_at: str


@dataclass
class SearchHit:
    source_type: str
    kind: str
    path: str
    heading: str
    snippet: str
    score: float


@dataclass
class TranscriptRecord:
    path: str
    source_kind: str
    entry_kind: str
    speaker: str
    content: str
    tags: str
    block_index: int


def utc_now_iso() -> str:
    return datetime.now(timezone.utc).replace(microsecond=0).isoformat()


def normalize_search_query(query: str) -> str:
    cleaned = re.sub(r"[^\w\s]", " ", query, flags=re.UNICODE)
    normalized = " ".join(cleaned.split())
    return normalized or query


def read_text_file(path: Path) -> str:
    return path.read_text(encoding="utf-8-sig")


def ensure_parent() -> None:
    DB_PATH.parent.mkdir(parents=True, exist_ok=True)


def connect() -> sqlite3.Connection:
    ensure_parent()
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    return conn


def init_db() -> None:
    with connect() as conn:
        conn.executescript(
            """
            CREATE TABLE IF NOT EXISTS sections (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                path TEXT NOT NULL,
                kind TEXT NOT NULL,
                title TEXT NOT NULL,
                heading TEXT NOT NULL,
                level INTEGER NOT NULL,
                content TEXT NOT NULL,
                tags TEXT NOT NULL,
                content_hash TEXT NOT NULL,
                UNIQUE(path, heading, content_hash)
            );

            CREATE VIRTUAL TABLE IF NOT EXISTS sections_fts USING fts5(
                path,
                kind,
                title,
                heading,
                content,
                tags
            );

            CREATE TABLE IF NOT EXISTS memories (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                kind TEXT NOT NULL,
                title TEXT NOT NULL,
                summary TEXT NOT NULL,
                content TEXT NOT NULL,
                tags TEXT NOT NULL,
                origin TEXT NOT NULL,
                source_path TEXT NOT NULL,
                source_heading TEXT NOT NULL,
                content_hash TEXT NOT NULL,
                created_at TEXT NOT NULL,
                updated_at TEXT NOT NULL,
                UNIQUE(origin, source_path, source_heading, content_hash)
            );

            CREATE VIRTUAL TABLE IF NOT EXISTS memories_fts USING fts5(
                kind,
                title,
                summary,
                content,
                tags,
                origin,
                source_path,
                source_heading
            );
            """
        )
    print(f"initialized: {DB_PATH}")


def resolve_sources(raw_sources: list[str] | None) -> list[Path]:
    if not raw_sources:
        return DEFAULT_SOURCES
    return [Path(item).resolve() for item in raw_sources]


def iter_markdown_paths(sources: list[Path]) -> Iterable[Path]:
    for source in sources:
        if source.is_file() and source.suffix.lower() == ".md":
            yield source
        elif source.is_dir():
            yield from sorted(source.rglob("*.md"))


def classify_kind(path: Path) -> str:
    rel = path.relative_to(REPO_ROOT).as_posix()
    if rel.startswith(".codex/"):
        return "memento"
    if rel.startswith("docs/testing/"):
        return "testing"
    if rel.startswith("docs/troubleshooting/"):
        return "troubleshooting"
    if rel.startswith("docs/status/"):
        return "status"
    if rel.startswith("docs/direction/"):
        return "direction"
    if rel.startswith("docs/planning/"):
        return "planning"
    if rel.startswith("docs/decisions/"):
        return "decision"
    if rel.startswith("docs/tech-specs/"):
        return "tech-spec"
    return "root-doc"


def make_tags(path: Path, kind: str) -> str:
    rel_parts = path.relative_to(REPO_ROOT).parts
    tags = {kind}
    for part in rel_parts[:-1]:
        tags.add(part.lower())
    tags.add(path.stem.lower().replace("_", "-"))
    return ",".join(sorted(tags))


def first_nonempty_line(text: str) -> str:
    for line in text.splitlines():
        stripped = line.strip()
        if stripped:
            return stripped
    return ""


def infer_transcript_source_kind(path: Path, explicit: str | None = None) -> str:
    if explicit:
        return explicit.strip().lower()
    lowered = path.as_posix().lower()
    if "claude" in lowered:
        return "claude"
    if "codex" in lowered:
        return "codex"
    return "unknown"


def transcript_entry_kind(entry_kind: str | None, speaker: str, content: str) -> str:
    normalized = (entry_kind or "").strip().lower()
    if normalized in {
        "transcript-entry",
        "transcript-message",
        "transcript-tool",
        "transcript-decision",
        "transcript-reflection",
        "transcript-technique",
    }:
        return normalized
    marker_source = f"{speaker}\n{content}".lower()
    if "decision:" in marker_source or marker_source.startswith("decision"):
        return "transcript-decision"
    if "reflection:" in marker_source or marker_source.startswith("reflection"):
        return "transcript-reflection"
    if "technique:" in marker_source or marker_source.startswith("technique"):
        return "transcript-technique"
    if "tool:" in marker_source or "called tool" in marker_source or "request starting http" in marker_source:
        return "transcript-tool"
    if speaker or content:
        return "transcript-message"
    return "transcript-entry"


def split_transcript_blocks(text: str) -> list[str]:
    blocks: list[str] = []
    buffer: list[str] = []
    for line in text.splitlines():
        if line.strip():
            buffer.append(line.rstrip())
            continue
        if buffer:
            blocks.append("\n".join(buffer).strip())
            buffer = []
    if buffer:
        blocks.append("\n".join(buffer).strip())
    return blocks


def parse_jsonl_transcript(path: Path, source_kind: str) -> list[TranscriptRecord]:
    records: list[TranscriptRecord] = []
    for index, line in enumerate(read_text_file(path).splitlines(), start=1):
        if not line.strip():
            continue
        payload = json.loads(line)
        if not isinstance(payload, dict):
            continue
        content = str(payload.get("content") or payload.get("text") or payload.get("message") or "").strip()
        speaker = str(payload.get("speaker") or payload.get("role") or payload.get("author") or "").strip()
        kind = transcript_entry_kind(payload.get("kind"), speaker, content)
        tags = {
            "transcript",
            source_kind,
            kind,
        }
        extra_tags = payload.get("tags") or []
        if isinstance(extra_tags, str):
            extra_tags = [extra_tags]
        for tag in extra_tags:
            if tag:
                tags.add(str(tag).strip().lower())
        if not content:
            continue
        records.append(
            TranscriptRecord(
                path=str(path.relative_to(REPO_ROOT)).replace("\\", "/"),
                source_kind=source_kind,
                entry_kind=kind,
                speaker=speaker or "unknown",
                content=content,
                tags=",".join(sorted(tags)),
                block_index=index,
            )
        )
    return records


def parse_text_transcript(path: Path, source_kind: str) -> list[TranscriptRecord]:
    blocks = split_transcript_blocks(read_text_file(path))
    records: list[TranscriptRecord] = []
    for index, block in enumerate(blocks, start=1):
        lines = [line.strip() for line in block.splitlines() if line.strip()]
        if not lines:
            continue
        first_line = lines[0]
        speaker = "unknown"
        content = block.strip()
        if ":" in first_line and len(first_line.split(":", 1)[0]) <= 24:
            speaker, remainder = first_line.split(":", 1)
            speaker = speaker.strip() or "unknown"
            remainder = remainder.strip()
            content = "\n".join([remainder] + lines[1:]).strip()
        kind = transcript_entry_kind(None, speaker, content)
        if content.startswith("Decision:"):
            kind = "transcript-decision"
        elif content.startswith("Reflection:"):
            kind = "transcript-reflection"
        elif content.startswith("Technique:"):
            kind = "transcript-technique"
        elif content.startswith("Tool:"):
            kind = "transcript-tool"
        tags = ",".join(sorted({"transcript", source_kind, kind, path.stem.lower()}))
        records.append(
            TranscriptRecord(
                path=str(path.relative_to(REPO_ROOT)).replace("\\", "/"),
                source_kind=source_kind,
                entry_kind=kind,
                speaker=speaker,
                content=content,
                tags=tags,
                block_index=index,
            )
        )
    return records


def parse_transcript_file(path: Path, source_kind: str) -> list[TranscriptRecord]:
    if path.suffix.lower() == ".jsonl":
        return parse_jsonl_transcript(path, source_kind)
    return parse_text_transcript(path, source_kind)


def transcript_memory_title(record: TranscriptRecord) -> str:
    preview = first_nonempty_line(record.content)
    if len(preview) > 80:
        preview = preview[:77] + "..."
    return f"{record.source_kind}:{record.entry_kind}:{preview or 'transcript'}"


def transcript_memory_summary(record: TranscriptRecord) -> str:
    speaker = record.speaker if record.speaker else "unknown"
    return f"{speaker} | {first_nonempty_line(record.content)[:240]}"


def derive_transcript_memories(records: list[TranscriptRecord]) -> list[MemoryRecord]:
    now = utc_now_iso()
    memories: list[MemoryRecord] = []
    for record in records:
        memories.append(
            MemoryRecord(
                kind=record.entry_kind,
                title=transcript_memory_title(record),
                summary=transcript_memory_summary(record),
                content=record.content,
                tags=record.tags,
                origin="transcript",
                source_path=record.path,
                source_heading=f"{record.source_kind} #{record.block_index}",
                content_hash=hashlib.sha256(
                    f"transcript|{record.path}|{record.block_index}|{record.entry_kind}|{record.content}".encode("utf-8")
                ).hexdigest(),
                created_at=now,
                updated_at=now,
            )
        )
    return memories


def split_sections(path: Path) -> list[SectionRecord]:
    text = read_text_file(path)
    lines = text.splitlines()
    title = path.stem
    kind = classify_kind(path)
    tags = make_tags(path, kind)

    sections: list[SectionRecord] = []
    current_heading = "<document>"
    current_level = 0
    buffer: list[str] = []

    def flush() -> None:
        content = "\n".join(buffer).strip()
        if not content:
            return
        content_hash = hashlib.sha256(
            f"{path}|{current_heading}|{content}".encode("utf-8")
        ).hexdigest()
        sections.append(
            SectionRecord(
                path=str(path.relative_to(REPO_ROOT)).replace("\\", "/"),
                kind=kind,
                title=title,
                heading=current_heading,
                level=current_level,
                content=content,
                tags=tags,
                content_hash=content_hash,
            )
        )

    for line in lines:
        if line.startswith("#"):
            flush()
            buffer.clear()
            current_heading = line.lstrip("#").strip() or "<untitled>"
            current_level = len(line) - len(line.lstrip("#"))
        else:
            buffer.append(line)

    flush()
    return sections


def derived_memory_kind(section: SectionRecord) -> str | None:
    if section.path == ".codex/MEMENTO.md":
        return "project-memory"
    if section.path.endswith("docs/status/CURRENT.md"):
        heading = section.heading.lower()
        if "what is working" in heading:
            return "status-working"
        if "current risks" in heading:
            return "risk"
        if "next engineering target" in heading:
            return "next-step"
    if section.path.startswith("docs/testing/"):
        return "test-procedure"
    if section.path.startswith("docs/troubleshooting/") and section.heading[:4].isdigit():
        return "troubleshooting"
    return None


def derive_memories(sections: list[SectionRecord]) -> list[MemoryRecord]:
    now = utc_now_iso()
    items: list[MemoryRecord] = []
    for section in sections:
        kind = derived_memory_kind(section)
        if not kind:
            continue
        tags = ",".join(sorted(set(section.tags.split(",")) | {kind}))
        items.append(
            MemoryRecord(
                kind=kind,
                title=section.heading,
                summary=first_nonempty_line(section.content)[:280],
                content=section.content,
                tags=tags,
                origin="derived",
                source_path=section.path,
                source_heading=section.heading,
                content_hash=hashlib.sha256(
                    f"derived|{section.path}|{section.heading}|{section.content}".encode("utf-8")
                ).hexdigest(),
                created_at=now,
                updated_at=now,
            )
        )
    return items


def rebuild_fts(conn: sqlite3.Connection) -> None:
    conn.execute("DELETE FROM sections_fts")
    conn.execute("DELETE FROM memories_fts")
    conn.execute(
        """
        INSERT INTO sections_fts (rowid, path, kind, title, heading, content, tags)
        SELECT id, path, kind, title, heading, content, tags FROM sections
        """
    )
    conn.execute(
        """
        INSERT INTO memories_fts (rowid, kind, title, summary, content, tags, origin, source_path, source_heading)
        SELECT id, kind, title, summary, content, tags, origin, source_path, source_heading FROM memories
        """
    )


def insert_memories(conn: sqlite3.Connection, memories: list[MemoryRecord]) -> None:
    for memory in memories:
        conn.execute(
            """
            INSERT OR REPLACE INTO memories (
                kind, title, summary, content, tags, origin, source_path, source_heading,
                content_hash, created_at, updated_at
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """,
            (
                memory.kind,
                memory.title,
                memory.summary,
                memory.content,
                memory.tags,
                memory.origin,
                memory.source_path,
                memory.source_heading,
                memory.content_hash,
                memory.created_at,
                memory.updated_at,
            ),
        )


def ingest(raw_sources: list[str] | None) -> None:
    init_db()
    sources = resolve_sources(raw_sources)
    sections: list[SectionRecord] = []
    for path in iter_markdown_paths(sources):
        try:
            sections.extend(split_sections(path))
        except Exception as exc:
            print(f"skipped: {path} ({exc})")

    memories = derive_memories(sections)

    with connect() as conn:
        conn.execute("DELETE FROM sections")
        conn.execute("DELETE FROM memories WHERE origin = 'derived'")
        for section in sections:
            conn.execute(
                """
                INSERT INTO sections (path, kind, title, heading, level, content, tags, content_hash)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?)
                """,
                (
                    section.path,
                    section.kind,
                    section.title,
                    section.heading,
                    section.level,
                    section.content,
                    section.tags,
                    section.content_hash,
                ),
            )
        insert_memories(conn, memories)
        rebuild_fts(conn)

    print(f"ingested sections: {len(sections)}")
    print(f"derived memories: {len(memories)}")


def iter_transcript_paths(sources: list[Path]) -> Iterable[Path]:
    for source in sources:
        if source.is_file() and source.suffix.lower() in TRANSCRIPT_EXTENSIONS:
            yield source
        elif source.is_dir():
            for path in sorted(source.rglob("*")):
                if path.is_file() and path.suffix.lower() in TRANSCRIPT_EXTENSIONS:
                    yield path


def ingest_transcripts(raw_sources: list[str] | None, source_kind: str | None) -> None:
    init_db()
    sources = resolve_sources(raw_sources)
    records: list[TranscriptRecord] = []
    for path in iter_transcript_paths(sources):
        try:
            records.extend(parse_transcript_file(path, infer_transcript_source_kind(path, source_kind)))
        except Exception as exc:
            print(f"skipped transcript: {path} ({exc})")

    memories = derive_transcript_memories(records)

    with connect() as conn:
        insert_memories(conn, memories)
        rebuild_fts(conn)

    print(f"transcript records: {len(records)}")
    print(f"transcript memories: {len(memories)}")


def capture_memory(kind: str, title: str, summary: str, content: str, tags: str) -> None:
    init_db()
    now = utc_now_iso()
    merged_tags = ",".join(sorted({item.strip() for item in tags.split(",") if item.strip()} | {kind}))
    record = MemoryRecord(
        kind=kind,
        title=title,
        summary=summary,
        content=content or summary,
        tags=merged_tags,
        origin="manual",
        source_path="",
        source_heading="",
        content_hash=hashlib.sha256(
            f"manual|{kind}|{title}|{summary}|{content}".encode("utf-8")
        ).hexdigest(),
        created_at=now,
        updated_at=now,
    )
    with connect() as conn:
        insert_memories(conn, [record])
        rebuild_fts(conn)
    print(f"captured memory: {title}")


def query_hits(conn: sqlite3.Connection, query: str, limit: int) -> list[SearchHit]:
    normalized_query = normalize_search_query(query)
    memory_rows = conn.execute(
        """
        SELECT memories.kind, memories.title, memories.source_path, snippet(memories_fts, 3, '[', ']', ' ... ', 16) AS snippet, bm25(memories_fts) AS score
        FROM memories_fts
        JOIN memories ON memories.id = memories_fts.rowid
        WHERE memories_fts MATCH ?
        ORDER BY score
        LIMIT ?
        """,
        (normalized_query, limit),
    ).fetchall()
    section_rows = conn.execute(
        """
        SELECT sections.path, sections.kind, sections.heading, snippet(sections_fts, 4, '[', ']', ' ... ', 16) AS snippet, bm25(sections_fts) AS score
        FROM sections_fts
        JOIN sections ON sections.id = sections_fts.rowid
        WHERE sections_fts MATCH ?
        ORDER BY score
        LIMIT ?
        """,
        (normalized_query, limit),
    ).fetchall()
    hits = [
        SearchHit("memory", row["kind"], row["source_path"] or "<manual>", row["title"], row["snippet"], row["score"])
        for row in memory_rows
    ] + [
        SearchHit("doc", row["kind"], row["path"], row["heading"], row["snippet"], row["score"])
        for row in section_rows
    ]
    hits.sort(key=lambda item: (item.score, item.source_type != "memory"))
    return hits[:limit]


def cmd_search(query: str, limit: int) -> None:
    with connect() as conn:
        hits = query_hits(conn, query, limit)
    if not hits:
        print("no matches")
        return
    for index, hit in enumerate(hits, start=1):
        print(f"{index}. [{hit.source_type}:{hit.kind}] {hit.path} :: {hit.heading}")
        print(f"   {hit.snippet}")


def cmd_context(query: str, limit: int) -> None:
    with connect() as conn:
        hits = query_hits(conn, query, limit)
        if not hits:
            print("no context matches")
            return
        for hit in hits:
            if hit.source_type == "memory":
                row = conn.execute(
                    """
                    SELECT kind, title, summary, content, tags, origin, source_path
                    FROM memories
                    WHERE kind = ? AND title = ? AND (source_path = ? OR (? = '<manual>' AND source_path = ''))
                    ORDER BY updated_at DESC
                    LIMIT 1
                    """,
                    (hit.kind, hit.heading, hit.path, hit.path),
                ).fetchone()
                print(f"### memory | {row['kind']} | {row['title']} | {row['origin']} | {row['source_path'] or '<manual>'}")
                print(f"Summary: {row['summary']}")
                print(f"Tags: {row['tags']}")
                print(row["content"])
                print()
            else:
                row = conn.execute(
                    """
                    SELECT path, kind, heading, content
                    FROM sections
                    WHERE path = ? AND heading = ?
                    LIMIT 1
                    """,
                    (hit.path, hit.heading),
                ).fetchone()
                print(f"### doc | {row['kind']} | {row['path']} | {row['heading']}")
                print(row["content"])
                print()


def cmd_bundle(query: str, limit: int) -> None:
    print("# Harness Context Bundle\n")
    print(f"- Query: {query}")
    print(f"- GeneratedAtUtc: {utc_now_iso()}\n")
    cmd_context(query, limit)


def cmd_memories(limit: int) -> None:
    with connect() as conn:
        rows = conn.execute(
            """
            SELECT kind, title, origin, source_path, updated_at
            FROM memories
            ORDER BY updated_at DESC
            LIMIT ?
            """,
            (limit,),
        ).fetchall()
    if not rows:
        print("no memories")
        return
    for index, row in enumerate(rows, start=1):
        print(f"{index}. [{row['origin']}:{row['kind']}] {row['title']} :: {row['source_path'] or '<manual>'} :: {row['updated_at']}")


def cmd_stats() -> None:
    with connect() as conn:
        section_count = conn.execute("SELECT COUNT(*) FROM sections").fetchone()[0]
        memory_count = conn.execute("SELECT COUNT(*) FROM memories").fetchone()[0]
    print(f"db: {DB_PATH}")
    print(f"sections: {section_count}")
    print(f"memories: {memory_count}")


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="Harnessing CLI")
    subparsers = parser.add_subparsers(dest="command", required=True)

    subparsers.add_parser("init")
    ingest_parser = subparsers.add_parser("ingest")
    ingest_parser.add_argument("--source", action="append", dest="sources")
    subparsers.add_parser("stats")

    transcript_parser = subparsers.add_parser("transcript")
    transcript_subparsers = transcript_parser.add_subparsers(dest="transcript_command", required=True)
    transcript_ingest_parser = transcript_subparsers.add_parser("ingest")
    transcript_ingest_parser.add_argument("--source", action="append", dest="sources")
    transcript_ingest_parser.add_argument("--source-kind", default=None)

    search_parser = subparsers.add_parser("search")
    search_parser.add_argument("query")
    search_parser.add_argument("--limit", type=int, default=8)

    context_parser = subparsers.add_parser("context")
    context_parser.add_argument("query")
    context_parser.add_argument("--limit", type=int, default=5)

    bundle_parser = subparsers.add_parser("bundle")
    bundle_parser.add_argument("query")
    bundle_parser.add_argument("--limit", type=int, default=5)

    capture_parser = subparsers.add_parser("capture")
    capture_parser.add_argument("--kind", required=True)
    capture_parser.add_argument("--title", required=True)
    capture_parser.add_argument("--summary", required=True)
    capture_parser.add_argument("--content", default="")
    capture_parser.add_argument("--tags", default="")

    memories_parser = subparsers.add_parser("memories")
    memories_parser.add_argument("--limit", type=int, default=20)

    return parser


def main() -> None:
    parser = build_parser()
    args = parser.parse_args()
    if args.command == "init":
        init_db()
    elif args.command == "ingest":
        ingest(args.sources)
    elif args.command == "stats":
        cmd_stats()
    elif args.command == "transcript" and args.transcript_command == "ingest":
        ingest_transcripts(args.sources, args.source_kind)
    elif args.command == "search":
        cmd_search(args.query, args.limit)
    elif args.command == "context":
        cmd_context(args.query, args.limit)
    elif args.command == "bundle":
        cmd_bundle(args.query, args.limit)
    elif args.command == "capture":
        capture_memory(args.kind, args.title, args.summary, args.content, args.tags)
    elif args.command == "memories":
        cmd_memories(args.limit)


if __name__ == "__main__":
    main()



