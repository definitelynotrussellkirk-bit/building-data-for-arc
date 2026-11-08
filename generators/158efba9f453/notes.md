# Working notes: 158efba9f453

## Rule and invariants

The unchanged Racket authority (`RULE_HASH = 41cef903ecd8`) preserves the input
and mirrors every nonzero, non-marker motif cell across the vertical axis marked
by the two gray (`5`) cells.  Lawful inputs have one marker column, two markers,
one to three non-gray motifs on one source side (axis contact is allowed), and
all reflected cells in bounds.  The generator remains deterministic and keeps
its existing easy/medium/hard schedule and advertised override axes.

## R1 — strict scalar boundary

The baseline generator hash
`3d5dadfc6116a58315c54e8d73a089787e5377cbd8f1ac891e48e9cb586fadf5`
accepted invalid call scalars and let `GenCtx` coerce them.  The baseline
`defect_lint` recorded 84 `strict-scalar` findings, including boolean, float and
string seeds/indices, negative `sample_index`, and non-integral numeric override
values.

The repair validates `seed`, `sample_index`, `difficulty`, every override key,
and each override value type before schedule arithmetic. Integer schedule draws
now use `draw_int_strict`.  Exact valid calls and the production schedule are
unchanged; only previously invalid/coercible calls are rejected.

## R3 — portable selected tests

The inherited selected tests guessed a fixed parent depth for canonical data.
They now use `reviewer_support.find_root`, `canonical_pairs`, and
`load_selected_generator`, so the same tests run in the repository and copied
portable runtime.  Regression coverage includes exact scalar rejection,
canonical parity, overrides, determinism, structural impostors, lesson
identifiability, and the semantic witness/rival interface.

Prior audit leads used for this repair:

- `review-bb6472c904793673:v0001` — portable canonical-path failure;
- `review-4192ea69a383cdcd:v0001` — the same unresolved portability class.

## R2 — strongest canonical shortcut and teaching contract

All three canonical sources lie to the **left** of the marker axis.  Therefore
`left_source_only`—apply the intended mirror only to left-source inputs and
return right-source inputs unchanged—fits 3/3 canonical pairs.  It is now an
executable entry in `CANONICAL_SHORTCUTS`, `SEMANTIC_RIVALS`, and
`LESSON_COMPETITORS`.

The retained generated counterexample is
`counterexamples/left_source_only_right_source.json` (hard, seed `20261013`,
sample index `5`, exact right-source overrides).  Its Racket receipt is
`checks/repair/left_source_only/racket-final.json`: the input is valid and the
authoritative output adds the three reflected cells that the rival omits.

Descriptive coverage predicates remain in `DISTRIBUTION_WITNESSES`.  The actual
semantic contract is deliberately narrower and honest:
`SEMANTIC_WITNESSES["source_right"]` is explicitly bound through
`WITNESS_RIVALS` to `left_source_only`.

## Final measurements

Final generator SHA-256:
`ad5ddd42aaa2aee4135bdfaa91a7865d2b8b19c367170962c28b4561a2735bcf`.

- after battery: 12/12 stages green;
- selected task tests: 30/30 passed;
- rule smoke: 120/120 applications and 120/120 Python-mirror parity checks;
- profile floor: 30 exact canonical-profile hits in 60 draws, with 9/20 easy,
  10/20 medium, and 11/20 hard;
- semantic gate: right-source witness fired 277/600 draws and every checked
  witness/rival claim held (60/60);
- lesson census: 300 three-demonstration/one-query lessons, 1,200 held-out query
  rotations, zero ambiguous lessons or rotations; the declared rival was
  refuted in all 100 lessons per band;
- visible-only post-repair solve: 3/3 visible examples passed in one revision,
  with prior repair-phase exposure disclosed and no reference consulted during
  the solve.

## Limits

The census is finite and tests one declared semantic rival plus shared generic
rivals; it is not a proof of unique identifiability against every conceivable
program.  Query rotation reuses each materialized four-pair lesson and does not
enumerate every random seed or every cyclic schedule window.  No Racket rule,
canonical row, approval state, or production schedule was changed.

<!-- arcpuzzles-current-audit-assessment:start -->
## Current bounded audit assessment

Return: `review-4192ea69a383cdcd:v0001`. Disposition: **resolved**. Evidence basis: `reviewer_reported`.

Audited source SHA-256: `3d5dadfc6116a58315c54e8d73a089787e5377cbd8f1ac891e48e9cb586fadf5`. At disposition, the audited source differs from the current source; this assessment covers audited bytes only.

### Current decision

Accepted reviewer-reported repair sourcead5ddd42aaa2aee4135bdfaa91a7865d2b8b19c367170962c28b4561a2735bcf migrates the old fixed-parent canonical lookup to root-bound reviewer_support helpers. Final portable stage and fresh-patch replay each report30 tests passing. Resolves only this named test-portability finding on old generator3d5dadfc6116a58315c54e8d73a089787e5377cbd8f1ac891e48e9cb586fadf5 and test78229df06d858cc2fc6a1b9d4e338313a5ecb27572895afff020be37c03678b9; not an independent maintainer rerun or semantic completeness claim.

### Assessment or prior finding

## 158efba9f453

**A-158-001 — Reproduced portable task-test preflight failure.** Audited generator SHA-256: `3d5dadfc6116a58315c54e8d73a089787e5377cbd8f1ac891e48e9cb586fadf5`; selected-test SHA-256: `78229df06d858cc2fc6a1b9d4e338313a5ecb27572895afff020be37c03678b9`.

The selected test computes its data root from a fixed `Path(__file__).resolve().parents[1]`. In the isolated portable runtime this resolves beneath the task directory, so line 26 seeks `generators/158efba9f453/data/canonical/puzzles.jsonl`. The official task-test stage stops in preflight before pytest collection with exit code 2. This is a test portability defect, not a claim about generator semantics.

Reproduction from `packet_root`:

```text
python3 review.py run python3 -m arcpuzzles check 158efba9f453 \
  --stage task_tests --timeout 600 --phase before \
  --out ../checks/audit/158efba9f453/task-tests-current
```

Evidence: `checks/audit/158efba9f453/finding.json` and `checks/audit/158efba9f453/task-tests-current/result.json`. Suggested repair: use `reviewer_support.find_root(__file__)`, `canonical_path`, and `canonical_pairs` rather than a fixed parent depth. I did not modify the audited target.

The disposition records an explicit decision. It does not imply a fresh execution, universal correctness, closure of other findings, or training admission.

[Retained evidence](counterexamples/review-4192ea69a383cdcd-v0001/audit_assets.json), manifest SHA-256 `bc888cd3f27ef8241d1ed8aab4a2b5e2a061b7eb6e63ff57a8c12c35f4d3efad`.
<!-- arcpuzzles-current-audit-assessment:end -->
## Current reviewer considerations

Source SHA-256: `ad5ddd42aaa2aee4135bdfaa91a7865d2b8b19c367170962c28b4561a2735bcf`.

# Decisions — 158efba9f453

## D1 / R1 — validate before keyed generation

**Input evidence.** The baseline `defect_lint` found 84 accepted invalid
scalars. Representative cases were `seed=True`, `sample_index=-1`,
`grid_h="7"`, `grid_w=9.75`, and `n_motifs=3.75`.

**Choice.** Add one `_validate_generate_call` at the public boundary, require
exact `int` for `seed` and `sample_index`, require a nonnegative index, validate
difficulty and override keys, and validate exact override types. Use
`draw_int_strict` for integer axes.

**Why.** This fixes the source of coercion before schedule arithmetic or keyed
randomness and gives callers deterministic, local errors. It also prevents
booleans from passing as integers.

**Rejected alternatives.** Post-generation validation would still allow
invalid calls to influence keyed draws; silently rounding/clamping floats would
preserve the defect; changing shared `GenCtx.draw_int` would alter unrelated
tasks and exceeded the selected-task scope.

**Probe/limit.** Red/green evidence is under `checks/task-tests-red` and
`checks/final-current-task-tests`; final `defect_lint` is part of
`checks/after`. The repair intentionally rejects previously coercible calls, so
out-of-contract callers must send exact types.

## D2 / R3 — use portable public test helpers

**Choice.** Replace fixed `Path.parents[...]` and private import assumptions with
`reviewer_support.find_root`, `canonical_pairs`, and
`load_selected_generator`.

**Why.** The test must run unchanged both in the repository and in the staged
portable runtime. The helper also binds assertions to the exact selected source
hash rather than a cached alias.

**Rejected alternative.** Adjusting the parent count would only move the failure
to another layout. Copying canonical data into the task test directory would
duplicate authority and risk drift.

**Probe/limit.** The inherited path failure is retained in
`checks/task-tests-red`; the final copied-runtime run is 30/30. Canonical helpers
expose labels and are authoring-only; they were not used during the solve phase.

## D3 / R2 — choose `left_source_only` as the primary rival

**Observation.** All 3 canonical pairs have motif sources on the left of the
gray marker axis. A learner can therefore infer “mirror left-side motifs; do
nothing to right-side motifs” without contradicting a demonstration.

**Choice.** Implement that hypothesis once and expose the same callable through
`CANONICAL_SHORTCUTS`, `SEMANTIC_RIVALS`, and `LESSON_COMPETITORS`.

**Why this rival.** It is simple, canonical-perfect (3/3), domain-lawful, and
changes the answer on an ordinary generated right-source input. It is stronger
and more pedagogically relevant than identity, grid-center reflection, or
single-color-only candidates, which the existing lesson schedule already
refutes directly.

**Exact probe.** `counterexamples/left_source_only_right_source.json` records a
right-source draw and both outputs; `checks/repair/left_source_only/racket-final.json`
binds the intended output to generator hash `ad5ddd42…` and rule hash
`41cef903ecd8`.

## D4 / R2 — separate coverage facts from semantic evidence

**Choice.** Rename the broad predicate map to `DISTRIBUTION_WITNESSES`; keep only
`source_right` in `SEMANTIC_WITNESSES`; declare
`WITNESS_RIVALS = {"source_right": ["left_source_only"]}`.

**Why.** A semantic witness should be executable evidence against a named rival,
not merely a statement such as “two motifs occurred.” This lets the semantic
gate check the claim instead of crediting unrelated coverage.

**Rejected alternative.** Binding every descriptive axis to the same rival would
inflate evidence without logical support. Removing witnesses entirely would
leave the canonical ambiguity undocumented.

## D5 — preserve production support rather than reschedule

**Choice.** Do not change the valid-input schedule. Use its existing right-side
support as the counterexample and teaching signal.

**Why.** The generator already produces both sides. Final semantic measurement
found 277 right-source witnesses in 600 draws, while exact canonical-profile
support remained 9/20 easy, 10/20 medium, and 11/20 hard. A reschedule would add
risk without addressing the real missing contract.

**Rejected alternative.** Forcing every lesson or every sample to be
right-source would narrow the domain and create a new shortcut. The lesson hook
instead rejects a bundle only when the named rival survives its demonstrations
and changes the query.

## D6 — use production lessons plus every query rotation

**Choice.** Run 100 production lessons per band with three demonstrations and
one query, then hold out each of the four pairs once (`--rotate-query`).

**Why.** Ordered production success alone could hide a query-position shortcut.
The rotation pass checks all 1,200 positions across the 300 materialized
bundles while preserving the production sampler.

**Limit.** This is finite declared-rival evidence. It reuses the same bundles,
does not enumerate every seed or all cyclic schedule starts, and cannot rule out
an undeclared program.

## D7 — leave the Racket authority unchanged

**Choice.** No Racket or canonical edit.

**Why.** Canonical outputs, generated Racket outputs, and the Python mirror agree.
Final smoke applied 120 generated inputs with 0 crashes and 120/120 mirror parity.
The defects were generator boundary/testing/teaching-contract issues, not rule
semantics.

## D8 — preserve honest failed and interrupted evidence

**Choice.** Retain the baseline defect failure, TDD red runs, intermediate
semantic-contract failure, and interrupted battery attempts. Resume only when
source/settings hashes match.

**Why.** These records establish what the regressions catch and prevent a later
pass from erasing the route to the final source. The exact resume ultimately
produced the 12/12 final summary.

## D9 — audit targets remain read-only

The assigned peer targets `78645c33b002` and `1bc816e1eb99` were inspected and
reproduced but not modified. Their findings belong in `AUDIT.md`; applying fixes
there would violate the selected-task delta contract.
