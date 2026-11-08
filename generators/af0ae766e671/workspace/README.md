# Occupancy coverage probe

`probe_occupancy.py` is a reusable authoring diagnostic for tasks whose inputs
are two vertically stacked, equally sized panels. It uses the public
`reviewer_support` loader, discovers the selected generator's pattern families,
and records the exact source SHA-256, draw identities, per-pattern state coverage,
validator outcomes, unique-input denominator and first complete failing input.
Canonical input summaries are included; this helper exposes canonical data and
must not be used during a visible-only solve.

From the outer packet directory:

```bash
python3 review.py run python3 generators/af0ae766e671/workspace/probe_occupancy.py --task-id af0ae766e671 --seed-count 32 --samples 4 --band easy --band medium --band hard --require-states 00,01,10,11 --out ../checks/occupancy-new.json
```

Use a new output path to retain earlier evidence. This command samples seeds
0..31 and indices 0..3 in three difficulty bands and six pattern families:
2,304 requested draws. `--band default` also supports the unpinned difficulty.
The script requires only the packet's normal authoring Python dependencies.

The required state set is an explicit task contract. Do not apply all four
states blindly to other tasks; omit `--require-states` for observation or supply
the appropriate subset after inspecting their canonical domain. This tool
measures input coverage, not Racket correctness or complete-lesson teaching.
Use `arcpuzzles apply` for source-bound labels and `lesson-census` for production
lessons and query rotations. Task-specific baseline witnesses live in
`../counterexamples/baseline_contract_failures.json`; focused tests live in
`../tests/`. Workspace code is never automatically selected as the generator.
