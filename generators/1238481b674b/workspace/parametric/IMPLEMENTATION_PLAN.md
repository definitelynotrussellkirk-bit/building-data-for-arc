# Triangle render-mode prototype implementation record

## Goal

Provide a runnable, bounded `outline|solid` rule variant for original ARC family
`training:1478ab18` without changing the approved canonical generator.

## Design

- `outline` is loaded byte-for-byte from canonical `program_solution`.
- `solid` reuses the same marker/bbox/missing-corner inference and changes only
  the rendering of the selected triangle from boundary-only to filled.
- One mode is chosen from the episode seed and retained for all five pairs.
- Four demonstrations span all four missing-corner orientations; the fifth pair
  is an unlabelled public query.
- Exact Racket execution supplies labels. A standalone Python mirror checks
  parity and is never treated as authority.

## Test-first sequence

1. Parameter contract and strict seed typing.
2. Exact canonical source, alternative source, hashes, and materialization.
3. Independent transforms and clue preservation across all orientations.
4. Complete Racket-labelled episodes and public redaction.
5. Source-bound evidence report with explicit rival outputs.

RED and GREEN command logs are retained under `WORK/checks/parametric/`.
