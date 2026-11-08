# Binary-mask teaching repair design

## Intent

Teach the canonical rule's actual foreground semantics rather than the accidental palette convention in version 3.0.0. The authority ignores colors 0 and 9, merges cardinally touching non-background colors, and separates disconnected regions even when they share a color.

## Goals

- Every default generated pair still refutes bounding-box thickness.
- Every default pair also refutes “one component per color.”
- Every default pair contains an isolated color-9 background witness and refutes “all nonzero cells are foreground.”
- Canonical examples remain accepted and the canonical Racket program remains unchanged.
- Retain exact override behavior, dimensions, object counts, depths, irregularity, determinism, and Racket parity.
- Extend the independent probe and retain one exact counterexample for all three shortcuts.

## Non-goals

- No change to the canonical transformation or rule hash.
- No new public parameter or promotion claim.
- No arbitrary multicolor noise; generated color topology must be deterministic and legible.

## Approach

Considered: (1) add only color 9, (2) add only repeated component colors, (3) alternate two explicit color-topology witnesses and include an isolated 9 in every draw. Use (3): alternating repeated-color and mixed-component scenes teaches both directions of the binary-mask rule, while a single isolated 9 makes the background exception observable without changing geometry.

## Constraints

All edits stay under `generators/2c4efc97c37d/`. Tests are written and observed failing before implementation. The task-local Racket authority is exercised on canonical, exact-witness, boundary-override, and fresh generated inputs.
