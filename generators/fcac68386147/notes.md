# Working notes: fcac68386147

## Current decisions

- Keep production generator `2.0.0`, canonical JSONL, and exact canonical Racket authority unchanged. The production generator remains SHA-256 `e3cb70cda6c756fd3124cc0211641e83381f144ccc3245db06653f775236c005`; normalized rule hash remains `350a34d04ac2`; canonical source SHA-256 remains `e78dc62cf0344fbef6542ba31bb4f9f50b42ab2458d9378af989e89482329eab`.
- Repair the retained task test's portable-root assumption with `reviewer_support.find_root`, `canonical_path`, and `canonical_pairs`. Compare normalized Racket programs rather than formatting-sensitive raw text because the staged base record preserves the same rule with whitespace normalization.
- Keep the parameter work in `workspace/parametric/` as a proposed, non-production extension. `row_repeat_offset` and `column_repeat_offset` are each `{0,1}`; one setting is fixed per episode. The complete source tile and modulo-residue lookup are unchanged, while the output contains `n + offset` whole copies on each axis. `(0,0)` is byte-for-byte canonical.
- Keep input sampling independent of the rule stream. Expose demonstration and query counts separately (`1..8` each, at most 16 total), reject non-integer/lookalike values, and write public challenges by exact visible-content SHA-256 with settings, programs, seeds, and query labels retained privately.

## Retained evidence

- Final selected-task run: 33 passed, 13 subtests passed, one pre-existing private-API deprecation warning; see `checks/fcac68386147/final-task-tests/`.
- Exact Racket evidence: four settings, one episode per setting, three demonstrations plus four distinct queries, 112 verifier outputs matching an independent Python mirror, all declared rivals refuted by demonstrations, and every query disagreeing with every rival; see `checks/fcac68386147/repeat-offset-evidence-v1/report.json`.
- Bounded adversarial pass: 4,096 inputs across seeds 0..255 at the 16-pair limit, a 30x30 maximum declared boundary output, four exact public/private reconstructions, and no duplicate/coupling or hidden-field leak found; see `checks/fcac68386147/adversarial-probe.json`.

## Open limits and next useful action

The prior production teaching findings remain open: undeclared color-collapse and background-border-crop rivals can still survive some ordinary production lessons. This prototype does not alter production lesson assembly and therefore does not resolve those findings. It also establishes only finite declared-rival identifiability, not unique induction, training value, variant approval, or admission. A maintainer can separately decide whether the small repeat-count family is worth promotion; any production teaching repair should declare the known rivals and require demonstrations that expose multicolor preservation and informative background borders without shrinking the lawful generator domain.
