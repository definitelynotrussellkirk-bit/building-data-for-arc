# Current generator notes: 1b9e8a54331b

## Authority

The canonical Racket authority is unchanged and remains pinned by
`RULE_HASH = db20de981b4f`. Color 2 emits horizontal color-7 rays, color 1 emits
vertical color-8 rays, color-5 cells stop rays and remain gray, and a horizontal /
vertical ray intersection becomes color 6. Version `3.0.0` is bound to selected
source SHA-256
`6c473f114b9933795919e6cfdc01f60f9bfd54bfa73b03ff3d8454ebd128dae0`.

## Defects and root cause

Three retained source-bound reviews described the same underlying sampler
problem from different surfaces:

1. seed 7 / easy / indices 187–190 admitted a three-demo lesson with no crossing;
2. seed 1 / easy / indices 2–6 admitted a lesson where wall stopping was not
   needed to predict the query;
3. the advertised generic control surface contained ignored aliases and rejected
   documented 14×14 values.

The canonical rule was not at fault. Seeds and walls were placed independently,
so semantic coverage was accidental, while the metadata came from a broad generic
template rather than observable behavior.

## Current design

Ordinary generation is constructive rather than rejection-based. A horizontal
blocker profile uses a vertical wall with visible space beyond it; a vertical
blocker profile uses a horizontal wall with visible space beyond it. In both
profiles, the opposite ray family crosses before the blocked family stops. Thus
every ordinary draw has:

- at least one color-6 crossing;
- at least one cell where an `ignore_walls` rival disagrees;
- isolated 1–2 horizontal seeds and 1–2 vertical seeds;
- one color-5 segment of length 4–7;
- both directions and exact requested counts represented by construction.

Deterministic coordinate combinations, wall-length variation and reflections
provide replayable diversity without changing the observable controls.

## Exact public contract

The ordinary exact axes are:

- `grid_h`: every integer 7 through 14;
- `grid_w`: every integer 8 through 14;
- `horizontal_seed_count`: 1 or 2;
- `vertical_seed_count`: 1 or 2;
- `block_axis`: `horizontal` or `vertical`.

Unknown overrides fail closed. Diagnostic `texture` accepts only `no_seeds`,
`no_walls`, or `no_crossings`, and cannot be combined with ordinary semantic
axes. `observe_overrides` makes the five ordinary controls executable.

## Teaching contract

`EXAMPLES_NEEDED = 3`. `lesson_identifiable` validates demonstrations against the
pinned Python mirror and rejects a lesson when any of three explicit competitors
survives:

- `ignore_walls`;
- `horizontal_precedence_no_color6`;
- `swap_seed_directions`.

Every ordinary example independently refutes all three, so every sliding
three-demo window does as well. The two exact retained audit windows now pass the
same hook. The `no_crossings` diagnostic remains intentionally outside ordinary
strict support and produces no color 6.

## Reusable evidence tool

`workspace/semantic_contract_probe.py` is a replayable source-bound preflight for
future agents. It checks 36 ordinary samples, all eight semantic-axis boundary
combinations at 14×14, both retained audit windows, 25-sample uniqueness by band,
and emits five inputs plus independent expected outputs for protected Racket
replay.

## Measured evidence

- Seven task-local regression tests pass. They cover all five canonical pairs,
  the 14×14 contract, both retained audit windows, all sliding three-demo windows,
  the `no_crossings` degenerate, diversity, and the probe artifact.
- Repository lint, override, semantic-gate, and diversity stages pass. The
  semantic gate accepted 600/600 strict draws and 12/12 lessons with no warnings.
- The semantic-contract probe reports 36 ordinary cases, 8 boundary cases,
  2 audit windows, 5 Racket replay cases, and zero failures.
- Protected Racket executed those five representative cases at rule hash
  `db20de981b4f`; all outputs matched the independent Python mirror exactly and
  all inputs passed the generator-domain check.

An earlier lint run exposed only four unique layouts in a 25-draw window. A
failing regression was added before the placement/reflection diversification;
the final lint and diversity runs pass. One exploratory semantic-gate command
requested fixed-period enumeration even though no `LESSON_SCHEDULE_PERIOD` is
declared; that command failed on the option contract, and the correctly scoped
semantic-gate rerun passed.

## Limits and next action

The generated ordinary domain intentionally uses one blocker segment and only
isolated seeds. The three rivals are finite and do not prove unique induction
against arbitrary programs. The bounded seed probes do not exhaust all layouts,
and no model-training experiment measured downstream Qwen accuracy. The repair
improves data value by making the two load-bearing rule branches unavoidable in
every lesson, not by claiming a measured model gain.

Next useful action: maintainer replay the compact receipts and decide whether the
three retained audits can be resolved against this exact source. Packaging alone
does not grant approval or training admission.

<!-- arcpuzzles-current-audit-assessment:start -->
## Current bounded audit assessment

Return: `review-2676edcea6e7e481:v0001`. Disposition: **resolved**. Evidence basis: `reviewer_reported`.

Audited source SHA-256: `45187d684b5dd87d99b03f510b9943421912fe27a88170e4cb7b0640b7f119c3`. At disposition, the audited source differs from the current source; this assessment covers audited bytes only.

### Current decision

Accepted source-bound repair explicitly addresses this finding; focused checks and Racket parity are reviewer-reported, not a new owner battery. Current task notes and retained integration record specify scope and finite limitations.

### Assessment or prior finding

## 1b9e8a54331b

**Reproduced lesson ambiguity: wall stopping is not guaranteed in a training window.**

For easy difficulty, seed 1, sample indices 2–5, none of four consecutive examples requires rays to stop at color-5 walls. A rival that lets rays pass through walls therefore matches all four Racket-labelled demonstrations. On the next ordinary sample, index 6, the rival paints four cells beyond a blocker that the authority leaves 0.

The local ray mirror matched Racket on all five retained pairs. A separate 300-draw-per-band census found that the no-blocker rival matched 98/300 easy, 86/300 medium, and 98/300 hard ordinary examples, so lack of blocker discrimination is common enough to require scheduling rather than chance.

- Audited generator SHA-256: `45187d684b5dd87d99b03f510b9943421912fe27a88170e4cb7b0640b7f119c3`
- Executed rule hash: `db20de981b4f`
- Exact window: easy, seed 1, demos 2–5, query 6
- Reproducer: `checks/audit/1b9e8a54331b/probe.py`
- Lesson witness: `checks/audit/1b9e8a54331b/lesson_witness.json`
- Racket record: `checks/audit/1b9e8a54331b/racket_outputs.json`
- Full report: `checks/audit/1b9e8a54331b/report.json`

This finding is bounded to the documented ordinary sampler and the tested four-demo assembly. The audited source was left unchanged.

The disposition records an explicit decision. It does not imply a fresh execution, universal correctness, closure of other findings, or training admission.

[Retained evidence](counterexamples/review-2676edcea6e7e481-v0001/audit_assets.json), manifest SHA-256 `721c9168542c4bca896373ef1fece92a4d18bd430c9fe3baca6ed2513e5b1983`.
<!-- arcpuzzles-current-audit-assessment:end -->
