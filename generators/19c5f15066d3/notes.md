# Working notes: 19c5f15066d3

## Current decision

- Keep production `generator.py` unchanged at SHA-256 `0b2e7a6dfb1696ddd1986eef05605d17a57121115dbfa2cbde048784c22e529f` and keep canonical rule hash `1ffa1234962c` unchanged.
- Retain `workspace/parametric/` only as a **proposed, unapproved** episode-level extension. The hidden parameter is `proximity_radius` with exact integer values `0`, `1`, and `2`; canonical/default is `1`.
- Preserve the original reasoning pattern: paired blue edge markers define full rows/columns, and the parameter changes only the maximum perpendicular distance at which an entire red object is recolored blue.
- Fix one radius for a whole episode. Every retained input contains red-object witnesses at exact distances `0`, `1`, `2`, and `4`; retained episodes expose 3 demonstrations and 4 distinct queries.
- Public challenge files are answer-masked, named from exact visible bytes, emitted in public-ID order, and duplicate visible IDs are rejected before writing.

## Evidence retained

- `checks/parametric/19c5f15066d3-proximity-radius-v1/report.json`: 4 canonical pairs and 21 proposed episode pairs checked with exact Racket; all intended labels and both rival settings match the Python mirror; every demo refutes both rivals and every query changes under both rivals.
- `checks/final-task-tests-summary.json`: final staged suite, 26 total checks, no failures.
- `checks/parametric/adversarial/report.json`: bounded attack over 80 maximum-count sampler scenes plus a fresh max-seed Racket/public-boundary probe.
- The pre-existing canonical test now uses `reviewer_support.find_root` and `canonical_path`, so it survives staged relocation instead of assuming `parents[1]/data`.

## Remaining limits and next action

This work does not approve a new rule, alter the canonical authority, or admit data to training. Evidence covers the three bounded radius values and a limited seed sample, not every lawful input or every conceivable rival rule. The next useful action is independent maintainer review of the proposed parameter semantics and retained evidence before any promotion beyond task-local prototype status.

<!-- arcpuzzles-current-supplementary:start -->
## Current supplementary checks

Current source-bound ticket observations: `generators/19c5f15066d3/evidence/supplementary-current.json`. Results are reviewer-reported; blocked or unknown stays explicit. These observations do not approve a generator or variant, resolve audits, or admit data to training.
<!-- arcpuzzles-current-supplementary:end -->
