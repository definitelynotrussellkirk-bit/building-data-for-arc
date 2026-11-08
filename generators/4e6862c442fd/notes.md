# Current notes: 4e6862c442fd

## Intended rule and curriculum

A source marker and target marker each define an ordered local coordinate frame. A sparse signed motif expressed in the source frame is copied into the target frame while the source motif remains in place. The production curriculum uses three demonstrations followed by one query, a seed-phased eight-profile schedule over D4 frame relations, and a finite asymmetric motif catalog so declared translation, axis, sign, fixed-motif, and bounding-box rivals are refuted.

## Review decisions

- **R4E-1 — strict scalar contract.** The prior generator used coercing integer draws and did not validate `seed` or `sample_index`, so booleans, floats, strings, and negative indices could enter the public API. The new choice requires Python integers (excluding booleans), requires a nonnegative `sample_index`, and uses strict integer draws for every integer override. Focused regression coverage is in `tests/test_review_regressions.py`.
- **R4E-2 — declaration semantics.** The prior choice put seven partial heuristics in both `LESSON_COMPETITORS` and `CANONICAL_SHORTCUTS`. Measured against the three labeled canonical pairs, six fit 0/3 and `fixed_motif_zero` fit 1/3. The new choice keeps all seven as lesson competitors/semantic rivals but declares no canonical shortcut. See `counterexamples/review-18970a2504c4bc81-v0001/contract-counterexamples.json`.
- **Distribution preserved.** No valid generated output was changed: 1,408 valid before/after calls had zero mismatches and the same aggregate SHA-256. `VERSION` remains `3.0.0` because the output curriculum did not change.
- **Authority preserved.** The Racket rule and `RULE_HASH = 1e279b7f949b` were not edited; rule smoke and strict authority synchronization pass on the final source.

## Assumptions and known limits

The curriculum intentionally stays sparse and zero-background because that matches the authority. The finite semantic check covers the seven declared competitors, 12 ordered production lessons (three demos plus one query), and 48 diagnostic query rotations; it is not a proof against undeclared hypotheses or every seed. No 100-per-band lesson census was run because no declared canonical shortcut survived the corrected canonical-fit requirement; wider undeclared-rival ambiguity remains unknown.

The inherited frozen test `tests/test_generator_4e6862c442fd.py` still guesses a fixed `__file__.parents[...]` path and fails the portable task-test preflight before pytest. It was deliberately left unchanged under the packet contract; the maintainer owns migration to `reviewer_support.find_root`, `canonical_path`, and `canonical_pairs`. The new portable regression file passes directly (34/34).

## Evidence provenance

Associated return `external-local-random:097872a97795` / assignment copy `local-random-097872a97795` was used only as a lead for the seed-phased schedule, asymmetric catalog, strict teaching contract, sparse-background limitation, and authority-sync rationale. All claims above were remeasured on baseline SHA-256 `13f568eb70880ef9e0e59869c2f33189f1c559322fc57debc1c09ae1ff000041` and final SHA-256 `7dc70c5bd0b0658235b73b9802bccd54610f1dfcd1b6f848e878f1795f95828b`.
## Current reviewer considerations

Source SHA-256: `7dc70c5bd0b0658235b73b9802bccd54610f1dfcd1b6f848e878f1795f95828b`.

# Decisions for review-18970a2504c4bc81

## D1 — Preserve the existing v3 distribution

**Choice.** Keep the seed-phased eight-profile schedule, asymmetric signed motif catalog, three-demonstration ordered lesson assembly, sparse zero background, and strict structural validator.

**Original rationale.** The current source does not carry an inline history, so the original rationale is not independently known. Associated notes from `external-local-random:097872a97795` say the schedule was seed-phased so production episodes starting at sample index zero cover all D4 relations, and the finite asymmetric catalog was selected to refute translation, axis-swap, sign-dropping, fixed-motif, and bounding-box rivals. I used those statements only as leads.

**Probe.** The immutable before battery already passed self-check, rule smoke, distribution, profile floor, diversity, overrides, grammar, Racket lint, and authority synchronization. The final parity probe compared 1,408 lawful calls and found zero changed grids.

**Rejected alternative.** A broad motif, palette, or texture rewrite. It was unnecessary for the measured failures and could introduce noncanonical semantics or new shortcuts.

**Failure modes and limits.** Sparse zero-background examples may still permit undeclared family-level shortcuts. The finite battery and declared-rival checks do not prove universal identifiability.

## D2 — Enforce strict integer API inputs (R4E-1)

**Choice.** Require `type(seed) is int`; require `type(sample_index) is int` and `sample_index >= 0`; use `ctx.draw_int_strict` for `grid_h`, `grid_w`, `source_basis`, `target_basis`, and `motif_id` whether defaulted or overridden.

**Rationale.** The public generator contract advertises integer controls. Coercing `True`, `12.75`, or `"12"` creates hidden aliases, can mask bad upstream data, and caused the required defect lint to fail.

**Alternatives.** Continue coercion and document it; normalize only numeric strings; or reject only booleans. Those choices retain ambiguous call semantics and do not satisfy the strict public contract.

**Probe.** `tests/test_review_regressions.py` exercises 32 invalid scalar/index cases. Thirty-three assertions failed against the baseline test run (including the declaration test); the final focused run passes 34/34.

**Failure modes and limits.** This is intentionally a breaking change for callers relying on undocumented coercion. Negative `seed` values remain legal because no task requirement or measured defect justified restricting them.

## D3 — Correct canonical-shortcut declarations (R4E-2)

**Choice.** Set `CANONICAL_SHORTCUTS` to an empty typed dictionary. Keep all seven functions in `SEMANTIC_RIVALS` and `LESSON_COMPETITORS`.

**Prior choice.** The baseline declared the same seven functions as both competitors and canonical shortcuts.

**Reason for reversal.** A canonical shortcut must reproduce every usable labeled canonical pair. Measured fit counts were: global translation 0/3, ignore-source-basis 0/3, swap-local-axes 0/3, absolute-offsets 0/3, bbox-fill 0/3, fixed-motif-zero 1/3, and positive-quadrant-only 0/3. They are valuable wrong hypotheses, but not canonical-equivalent functions.

**Alternatives.** Delete the functions entirely, or weaken the checker. Deletion would remove useful lesson pressure; weakening the checker would preserve false metadata. The chosen separation retains both utility and truthfulness.

**Probe.** The focused test requires every declared canonical shortcut to fit every labeled canonical pair. The final semantic gate reports `CANONICAL_SHORTCUTS=[]`, all seven lesson competitors present, 12/12 ordered lessons identifiable, and no invalid declarations.

**Failure modes and limits.** An empty canonical-shortcut set is not evidence that no unknown shortcut fits the authority. It means no current declared function has earned that stronger label.

## D4 — Keep generator version 3.0.0

**Choice.** Do not increment `VERSION`.

**Rationale.** Lawful generation is byte-identical over 1,408 tested calls. The patch tightens invalid-call handling and fixes declaration metadata without changing the generated curriculum.

**Rejected alternative.** Incrementing to 3.0.1 would be defensible for API rejection semantics, but it would suggest a content distribution revision that did not occur. The final source hash provides exact identity.

**Limit.** Consumers that version error behavior rather than data output may prefer a patch bump; this repository's retained generator version appears centered on curriculum behavior, so I chose stability and documented the API change explicitly.

## D5 — Leave Racket authority unchanged

**Choice.** Do not edit shared/canonical Racket source; retain `RULE_HASH = 1e279b7f949b`.

**Rationale and probe.** The measured defects were in Python API/declaration contracts. Rule smoke, Racket lint, and authority synchronization are green in the final battery. Changing the authority would expand scope without evidence.

**Failure mode.** Historical associated notes mention a synchronized selected rule and archival textual variants; those old claims were not substituted for current checks. Current authority evidence is the final battery.

## D6 — Use the required semantic battery; do not claim a large census

**Choice.** Report the final 600-draw semantic check, 12 ordered lessons, and 48 diagnostic rotations. Do not run or claim the optional 100-lessons-per-band census.

**Rationale.** After correcting declarations, no declared canonical shortcut fits every canonical pair; the seven plausible rivals remain explicitly tested as lesson competitors. The required final battery is green and gives direct evidence for the actual production assembly.

**Rejected alternative.** Treat “no declared canonical shortcuts” as proof of identifiability, or run a large census and overstate finite evidence as universal. The first is invalid; the second would still not cover undeclared rules.

**Limit.** Wider ambiguity against undeclared competitors remains unknown. Diagnostic rotation success does not convert the ordered curriculum into a proven arbitrary-query curriculum.

## D7 — Do not alter the frozen inherited fixture (R4E-3)

**Choice.** Preserve `tests/test_generator_4e6862c442fd.py` exactly at baseline hash `b9fd8780b243e408b4fa2b288fecc2ec7a836c0faae00582be8f44d29fc8d62c` and report blocked completion.

**Rationale.** The packet explicitly forbids patching the baseline root fixture and assigns migration to the maintainer when portable preflight fails.

**Alternative.** Replacing the fixed-depth path with reviewer helpers would probably unblock aggregate pytest, but doing so here would violate scope and erase the exact inherited failure.

**Probe.** `checks/task-tests-final/result.json` records dependency preflight success followed by `fixed_depth_canonical_path` at line 18 before pytest. The new reviewer-owned test file separately passes 34/34.

## D8 — Keep audit work source-bound and non-invasive

**Choice.** Reproduce one actionable coverage witness for each assigned target and leave both targets unchanged.

**Rationale.** Audit duties require evidence, not repairs. `c1fd38e5812b` has a mixed-axis span witness; `b3c48865ed63` has a nonrectangular ring-plus-arm witness separating true enclosed-hole filling from bounding-box filling.

**Limits.** The first is one accepted witness revalidating a prior lead, not a repeated population census. The second includes 5 canonical pairs and 30 generated draws, but that finite sample does not prove every seed is rectangular.
