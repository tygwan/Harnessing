# Dual-Track Operating Model

## Purpose

Harnessing will be developed through two linked tracks.

The goal is to avoid building a detached framework with no real proving ground, while also avoiding project-specific hacks from leaking into the reusable harness.

## Track 1: Proving Ground

Consumer project:

- `ontology-for-cm`

Role:

- generates real requirements
- produces real docs, decisions, tests, and troubleshooting records
- validates whether memory extraction and search are actually useful during live engineering work

## Track 2: Productization

Reusable project:

- `Harnessing`

Role:

- generalizes validated patterns
- owns the reusable memory engine
- defines ingestion rules, storage model, and output contracts
- becomes the long-term home for reusable harness capabilities

## Working Loop

```text
ontology-for-cm work
  -> real requirement appears
  -> prototype or validate in the consumer project
  -> identify reusable pattern
  -> move or re-implement generically in Harnessing
  -> use updated Harnessing back in ontology-for-cm
```

## Decision Rule

Keep work in `ontology-for-cm` when:

- it depends on Revit, DXTnavis, ontology-specific semantics, or project-local structure
- it is still being explored
- it is not yet clear that the pattern should be reused elsewhere

Move work into `Harnessing` when:

- the behavior is generic
- another project could reuse it with minimal change
- it belongs to memory ingestion, search, bundle output, or memory typing

## Immediate Plan

### Harnessing

- keep the CLI-first memory engine stable
- add transcript ingestion design
- add project integration contract
- add export format for reusable context bundles

### ontology-for-cm

- keep using docs, memento, testing, and troubleshooting as real harness inputs
- continue Revit and ontology work that creates real memory artifacts
- validate whether harness output improves actual engineering flow

## Expected Outcome

If this model is followed well, Harnessing can guide both projects more precisely over time because it will accumulate:

- project memory
- decisions
- troubleshooting history
- test procedures
- reusable context bundles

But it will only do that well if the proving-ground project keeps producing clean source artifacts.
