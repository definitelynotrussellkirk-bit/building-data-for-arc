# Current notes: 19158f03ecb2

## Intended rule and authority

For every row, append its left-right reversal. Generator version `2.1.0` is bound
to unchanged canonical `RULE_HASH=1bf14d2f29b0`; final generator SHA-256 is
`2cba4e98ff256db67b2af11eba2e71c915badbc042c8b0e56040488445625314`.

## Current distribution

Inputs are 3–15 by 3–15 grids using 2–10 ARC colors and the declared texture
family. With no semantic override, sample indices 0–2 modulo 5 are left-right
asymmetric and indices 3–4 are symmetric. This gives standard 3-demo/1-query and
4-demo/1-query lessons asymmetric demonstrations that refute horizontal
duplication, while retaining lawful symmetric queries where both programs agree.
Canonical-profile draws remain 40% (indices 0 and 4 modulo 5 when shape/palette/
texture/noise axes are unpinned).

## Review-a1e69e9fdec20d2f decisions

- Reject coercive call arguments, invalid axis scalar types/ranges, and unknown
  override names at the public boundary.
- Treat difficulty ranges as preferences. Preserve pinned exact dimensions; if a
  coupled palette/symmetry request needs more capacity, widen only unpinned
  dimensions. Raise `OverrideIncompatibility` with `incompatible_axes` when the
  exact request is genuinely impossible.
- Declare `duplicate_input` as the primary semantic rival, with an asymmetric
  witness and a query-relevant `lesson_identifiable` hook.
- Keep canonical source and distribution shape unchanged; the repair addresses
  contracts and teaching evidence, not labels.

## Evidence

The final battery is 12/12 green and portable task tests are 20/20. A source-bound
census found 0/300 ambiguous ordered lessons and 0/1,200 ambiguous single-query
rotations against `duplicate_input`. Minimal replay cases live in
`counterexamples/review-a1e69e9fdec20d2f.json`.

## Proposed extension (not production)

`workspace/parametric/` implements a proposed episode-level
`mirror_side={right,left}` prototype. `right` is byte-exact canonical; `left`
prepends the reflection. Eight seeds × two settings yielded 16/16 identifiable
episodes and 64/64 identifiable rotations using actual Racket labels. Symmetric
inputs are an explicit unidentifiable limit and are filtered only in the
prototype.

## Known limits / open findings

Finite rival checks do not establish universal rule uniqueness. The four
canonical demonstrations are all width 3 and therefore admit a width-gated rule
that mirrors only width-3 inputs; generated wider asymmetric inputs refute it.
The prototype is not approved or integrated into the production generator API.
## Current reviewer considerations

Source SHA-256: `2cba4e98ff256db67b2af11eba2e71c915badbc042c8b0e56040488445625314`.

# Decisions — 19158f03ecb2

## D1 — Preserve the canonical rule and existing distribution shape

**Decision.** Keep the canonical transformation and `RULE_HASH=1bf14d2f29b0`
unchanged. Retain the existing input domain (3–15 rows and columns, 2–10 ARC
colors, the declared texture family) and the modulo-5 lesson schedule.

**Rationale.** Baseline rule-smoke, self-check, profile-floor, grammar, Racket
lint, and authority sync were already green. The failures concerned API contract,
exact override semantics, and missing executable teaching metadata—not output
labels. Replacing the sampler or rule would have added risk without addressing
the measured root causes.

**Alternative rejected.** Restrict generation to canonical 3×3 inputs. That would
make the generator easier to validate but would preserve a width-gated shortcut
and unnecessarily collapse useful support.

## D2 — Validate at the public boundary instead of relying on downstream coercion

**Decision.** Add `_validate_call` before constructing `gen_ctx`. Require exact
integer call arguments, finite/ranged declared axes, exact booleans where
required, known difficulty values, and no undeclared override keys.

**Rationale.** The baseline defect lint measured 63 accepted-invalid-scalar cases.
Validation at entry identifies the caller error before values are normalized by
`int(...)`, `float(...)`, or generic override plumbing.

**Alternative rejected.** Let shared helpers coerce values and patch only the
warnings observed in one stage. That would leave typoed axes and equivalent
coercions through other paths silent.

**Probe.** `test_call_arguments_reject_scalar_coercion`,
`test_declared_axes_reject_wrong_scalar_types`, and
`test_unknown_override_axis_is_rejected`.

## D3 — Treat difficulty ranges as preferences, never hidden incompatibilities

**Decision.** Resolve exact requested dimensions first. If the preferred
band-specific options cannot realize a coupled palette/symmetry request, widen
only unpinned dimensions to the full lawful 3–15 range. If no lawful pair exists,
raise `OverrideIncompatibility` with the active exact axes.

**Rationale.** `grid_h=3,palette_size=10` on the symmetric branch is feasible at
width ≥7; rejecting it merely because easy-mode defaults end at width 6 violates
exact-override semantics. Conversely, `3×4,palette_size=10,lr_asymmetric=false`
is mathematically impossible because a symmetric 3×4 grid has only six
independent cells.

**Alternatives rejected.** (1) Widen pinned axes, which violates caller intent;
(2) declare broad static incompatibility combinations, which would reject
feasible values; (3) silently reduce palette size, which falsifies the exact
control.

**Probe.** The two retained override cases in
`counterexamples/review-a1e69e9fdec20d2f.json` and the final 82,890-draw override
matrix.

## D4 — Model the strongest simple production rival explicitly

**Decision.** Declare `duplicate_input` in `SEMANTIC_RIVALS` and
`LESSON_COMPETITORS`; declare an asymmetric-grid witness; implement
`lesson_identifiable` so ambiguity is reported only when the rival fits every
demonstration *and* changes the query answer.

**Rationale.** On a left-right-symmetric input, mirroring and duplication coincide.
Asymmetric demonstrations are therefore the minimal semantic evidence. The
existing schedule already supplies them before either standard held-out branch,
so the right fix was executable metadata plus measurement, not a distribution
rewrite.

**Alternative rejected.** Require every pair, including each query, to be
asymmetric. That would remove a lawful branch and teach less about cases where
multiple programs happen to agree.

**Probe.** 300 lessons (100 per band), 1,200 production pairs, and all 1,200
single-query rotations; no ambiguity against the declared rival.

## D5 — Use mirror placement as the proposed rule parameter

**Decision.** Build the separate prototype `mirror_side={right,left}`. `right`
uses the byte-exact canonical program; `left` prepends the reflection. Choose the
parameter once per episode from a dedicated deterministic stream and keep input
streams independent of the setting.

**Rationale.** Placement changes the executed transformation while preserving the
family's core reasoning: reflect the complete grid, concatenate horizontally,
and infer placement from demonstrations. It is more meaningful than color,
size, texture, or density changes, which alter only inputs.

**Alternatives rejected.** Vertical mirroring changes the spatial composition too
far from the parent family; duplicating instead of mirroring removes the central
reflection step; choosing direction independently per pair would violate the
episode-level hidden-rule contract.

**Teaching constraint.** Every prototype input is left-right asymmetric. This is
a shared semantic filter, not a parameter-dependent sampling leak. Symmetric
inputs are explicitly documented as unidentifiable between the two settings.

**Probe.** 5/5 canonical labels, 16/16 episodes, and 64/64 rotations, all labelled
by actual isolated Racket execution. Exact hashes are in
`checks/parametric/mirror-side-seeds-0-7/report.json`.

## D6 — Preserve failures and compact counterexamples

**Decision.** Keep the initial red task-test result and the later fixture
transcription failure. Store only minimal replayable cases in the task's
`counterexamples/` directory and cover them with portable tests using
`reviewer_support.find_root`.

**Rationale.** The failed fixture run demonstrates that the retained evidence is
not decorative: it detected a one-cell omission in a hand-transcribed rival
output. Correcting the evidence rather than weakening the assertion preserves
its value for future agents.

## D7 — Audit findings remain findings, not unauthorized repairs

**Decision.** Do not edit `5c577e82a07f` or `b06d49e11f7f`.

**Rationale.** The assignment requests adversarial review only. `5c577…` has a
known ordered-curriculum boundary; `b06d…` has a reproducible semantic metadata
defect. Both are reported with source-bound evidence in `AUDIT.md`.

## Limitations

- The 300-lesson census tests the declared duplication rival and measured sampler;
  it does not prove uniqueness against every possible program.
- The width-gated canonical shortcut fits the four canonical demonstrations,
  though generated wider inputs refute it.
- The parametric prototype tests only two settings and eight seeds. It deliberately
  excludes symmetric inputs and is not wired into the production API.
- Aggregate runner interruptions seen during long stage transitions were
  operational; isolated stages passed and the resumed final battery is complete.

## Self-review

Strict validation removes only coercive and unknown inputs; it does not narrow
the documented lawful generator domain, and the override repair preserves every
pinned value while widening only unpinned dimensions. The canonical 3×3 examples
admit a width-gated mirror shortcut, but the generator's retained seed-0 width-5
asymmetric witness makes that shortcut disagree with production data.
