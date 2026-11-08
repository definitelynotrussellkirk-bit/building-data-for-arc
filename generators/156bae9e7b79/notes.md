# Working notes: 156bae9e7b79

Record design decisions, hypotheses, review findings, and unresolved questions here.
Imported associated notes retain original evidence/timestamps in `evidence/associated_notes.jsonl`.
## Current reviewer considerations

Source SHA-256: `4fe3bf13651039b87a3c4643e44ecaafc855317c39144b63dfc1e42829e60fbc`.

# Decisions for review `review-3bbcebf28a02be7e`

## D1 — Fail closed at the public scalar boundary

**Choice.** Validate `seed`, `sample_index`, and `difficulty` before scheduling,
overrides, or RNG construction. Seed and sample index must be literal integers,
the index must be non-negative, and difficulty must be one of
`None`, `easy`, `medium`, or `hard`.

**Rationale.** The before battery reproduced 48 invalid calls that entered
undocumented states. Validation at the boundary fixes the source of the defect,
rather than attempting to normalize values after schedule or RNG derivation.

**Alternatives rejected.** Retaining `int(...)` coercion would continue to merge
booleans, floats, strings, and negative indices into accidental curriculum
states. Validating only inside `generate` would leave `schedule_profile` as a
second inconsistent public entry point.

**Probe and result.** Nineteen focused cases were written first, failed, and then
passed. The valid-call preservation probe compared 120 lawful calls before and
after and found identical per-call and aggregate hashes.

**Failure mode/limit.** This is intentionally strict. A downstream caller that
previously relied on coercion now receives a `TypeError` or `ValueError`; that is
the intended API correction.

## D2 — Preserve version, production distribution, and Racket authority

**Choice.** Keep generator version `3.0.0`, schedule roles, advertised axes,
canonical profiles, rule source, and `RULE_HASH=01a0d2007d61` unchanged.

**Rationale.** Fresh measurements showed the concrete blocker was call-domain
validation. Existing valid outputs, canonical support, semantic witnesses, and
lesson assembly were already healthy.

**Alternative rejected.** Bumping the version or modifying the rule would imply a
semantic/data change not supported by the defect. Reworking the schedule would
risk invalidating the already measured canonical and contrast coverage.

**Probe and result.** Valid output digest unchanged; authority sync and rule smoke
are green; profile floor is 17 exact and 48 envelope hits out of 60; the final
300-lesson census found no declared-rival ambiguity.

## D3 — Use triangle growth rate as the bounded parametric extension

**Choice.** Add a separate prototype parameter `growth_rate ∈ {1,2}`. Value `1`
is the canonical default; value `2` doubles only the per-row visible-radius
growth before the existing saturation bound.

**Rationale.** This varies one meaningful relationship while preserving the
original object roles and reasoning chain: key extraction, cyan-line detection,
center, active interval, palette, and triangular projection all remain fixed.

**Alternatives rejected.** Palette swaps are mostly cosmetic and may alter fixed
color semantics. Reversing direction, changing the anchor, or replacing the
triangle would create a different task family rather than a small parameter.
Changing several properties at once would make identification and attribution
harder.

**Failure modes/limits.** If every demonstration saturates immediately or uses a
one-row line, both settings may be observationally equivalent while a later
query differs. The prototype's retained sampler prevents this by requiring each
input to distinguish settings, but the shared admission gate should verify it
rather than trust the authoring assumption.

## D4 — Choose the hidden parameter once per episode

**Choice.** Derive the setting from a rule-only deterministic seed stream, hold it
fixed for three demonstrations and the query, and draw the input stream
independently of the setting.

**Rationale.** A single latent rule is inferable in principle, and input geometry
cannot leak which setting was selected. Resampling per pair would create
internally inconsistent supervision.

**Alternative rejected.** Choosing per pair or deriving inputs from the hidden
setting would either make the episode incoherent or let superficial input
statistics reveal the answer.

**Probe and result.** Task-local tests verify seed stability, setting-independent
inputs, public masking, exact Racket/Python parity, and every query rotation. The
retained two-episode evidence has 8/8 rival checks refuted.

## D5 — Keep the prototype proposed and separate

**Choice.** Place the extension under `workspace/parametric/` with its own tests
and evidence; do not route production generation or the selected rule through it.

**Rationale.** The assignment asks for authoring evidence, not automatic variant
approval. Separating it protects the repaired canonical distribution and makes
maintainer review explicit.

**Limit.** The evidence covers only two settings, eight inputs, and the one
alternate-setting family. It does not prove unique induction or establish a
training benefit for Qwen3.5-9B.

## D6 — Treat the previous review index as a lead, not a measurement

**Choice.** Use `review-747a092dfe8b4a46:v0001` only to understand the baseline's
review history. Do not reuse its verdict or counts.

**Rationale.** The assignment is bound to frozen source SHA
`c77fdb...69212`; only fresh before/after runs establish the state of that source
and this patch.

## D7 — Audit without editing peer targets

**Choice.** Reproduce concrete findings for `d8b498586958` and `4199aa353fa1`,
retain source hashes and counterexamples, and leave both targets unchanged.

**Rationale.** The audit contract requests adversarial review, not repair. Mixing
peer fixes into the selected-task delta would violate source scope and blur
ownership.

**Limit.** The interrupted optional `4199aa353fa1` defect-lint run is not counted
as a result. The combined audit and exact missing-anchor Racket reproduction are
the retained evidence for that target.

## 2026-10-25 native parametric build (review-b0545ca002f965c6)

- Preserved the canonical keyed triangular projection byte-for-byte as the default setting.
- Added `postprocess=highlight_projected_majority`: construct the canonical projection, select the most frequent eligible projected color (lowest color wins ties), then recolor it to 9.
- Added an executable wrong-order rule that selects from the unweighted key row before projection; retained generated cases make that choice disagree with the projected majority.
- Added strict settings/input validation, deterministic 2–6 demonstration and 1–4 query generation, four distinct private queries including a substantive 30x30 case, sequential public projection, a reusable bounded audit, protected-Racket qualification evidence, and a source-bound causal witness.
- Reviewer status is ready only. Owner native qualification/acceptance and training admission remain separate and were not performed here.
