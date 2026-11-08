# Working notes: 5c577e82a07f

Record design decisions, hypotheses, review findings, and unresolved questions here.
Imported associated notes retain original evidence/timestamps in `evidence/associated_notes.jsonl`.
## Current reviewer considerations

Source SHA-256: `4ca19b6bba81335a3774646ab3a6e294597eb7042abb66e9e15e6840e7018340`.

# Decisions for `5c577e82a07f`

## D1 / R1 — Treat color-count scope as the highest-priority missing distinction

**Measured problem.** The four canonical demonstrations all contain two rectangle colors. Therefore “complete only the two lowest-valued colors” fits every canonical pair. In the baseline sampler, concrete medium lesson windows could show three two-color demonstrations and then ask a three-color query.

**Decision.** Add an executable `first_two_colors_only` rival to `SEMANTIC_RIVALS`, `LESSON_COMPETITORS`, and `CANONICAL_SHORTCUTS`; add a `three_colors_completed` witness claim; and keep an exact per-shortcut counterexample test.

**Why this rival.** It is more plausible and harder to refute than “first color only”: it is fully consistent with all canonical pairs and changes only the unobserved third-color branch. The exact witness and Racket output are in `checks/shortcut-witness/witness.json`.

**Rejected alternatives.** Merely documenting the risk would leave ordinary lessons ambiguous. Adding only a one-off test input would protect the code path but not the lesson distribution. Editing canonical rows or the Racket rule was rejected because the authority is correct and outside the defect.

## D2 / R1 — Use a deterministic one-in-three count schedule

**Decision.** For easy and medium, generate three rectangles when `(seed + sample_index) % 3 == 1`, otherwise two. Hard remains three rectangles except when a preserved canonical anchor supplies two.

**Rationale.** A three-consecutive-demonstration lesson then necessarily includes a three-color witness in any cyclic start. Canonical anchors are restricted to residue 0 modulo 6, so they cannot replace the residue-1 witness. The schedule is cheap to reason about and exhaustively test over its period.

**Rejected alternatives.** Randomly choosing two or three rectangles preserves the original failure with nonzero probability. Making all easy/medium examples three-color over-restricts the domain and removes useful two-color variety. Adding the witness only to medium or hard left easy lessons semantically under-specified; the intermediate failed battery and red regression are preserved in `checks/after-failed-band-witness/` and `checks/tdd-red-easy-witness/`.

**Known trade-off.** Rectangle count is now correlated with `(seed + sample_index) mod 3`. This is intentional curriculum structure. Geometry profile continues to cycle independently through thick, thin-horizontal, and thin-vertical cases; canonical anchors and two-color cases remain present.

## D3 / R2 — Normalize `None` overrides once at the public boundary

**Decision.** Build `active_overrides = {key: value for key, value in overrides.items() if value is not None}` immediately after validation and use it for `gen_ctx`, anchor eligibility, bounds, profile routing, and accounting.

**Rationale.** The task contract already defined `None` as absence. One normalization point prevents split semantics between validation and generation and keeps non-`None` behavior unchanged.

**Rejected alternatives.** Repeating `value is not None` checks at each branch would be error-prone. Changing shared `gen_ctx` would expand the patch beyond the selected task and could alter other generators. Rejecting `None` outright would contradict the existing validator and portable test convention.

## D4 / R3 — Preserve failing iterations and strengthen exact shortcut witnesses

**Decision.** Keep both red test runs and the intermediate semantic-gate failure. Replace the old assertion that one thin-horizontal example defeats every canonical shortcut with a name-to-witness mapping, so each declared shortcut must have its own exact counterexample.

**Rationale.** Different shortcuts require different distinguishing inputs. A shared witness can silently become irrelevant as the shortcut set grows.

## D5 — Build a source-bound reusable probe, not a report-only script

**Decision.** Add `workspace/probe_first_two_shortcut.py` and document it in the task workspace. It imports the selected generator by path, reads `CANONICAL_SHORTCUTS["first_two_colors_only"]`, verifies canonical fit, and scans consecutive windows.

**Rationale.** Future agents can rerun it after schedule changes without copying generator logic or a stale rival-name list. The report records source hash, seed/start ranges, count signatures, first witnesses by status, and finite-census limits.

## D6 — Preserve authority and existing geometry curriculum

The Racket source and canonical data were left unchanged. The selected rule hash remains `486ca16c83e1`. The prior three-profile geometry cycle was retained because it already rejects thin-horizontal and thin-vertical shortcuts; the new repair adds an orthogonal color-count schedule rather than replacing that curriculum.

## D7 — Interpret the rotation census as a diagnostic limitation

The final production census is clean, while 448/1,200 optional query rotations are ambiguous because rotating the sole witness out of the demonstrations changes the lesson policy. I did not redesign every four-pair set to make all four holdouts identifiable: production uses three consecutive demos plus one query, and forcing four-way leave-one-out identifiability would materially constrain the generator. The limitation is explicit in `REVIEW.md` and `checks/lesson-census.json`.

## D8 — Compress, do not discard, large evidence

Four exhaustive JSON files were gzip-compressed to stay below the return’s 25 MiB expanded-size budget. `checks/compressed-evidence-manifest.json` preserves each original path, size, SHA-256, compressed path/hash, and restoration command. The decisive final lesson census remains directly readable.

## D9 — Audit-only targets remain unmodified

The two adversarial audit findings are concrete and reproduced, but no source under `80b1344c17c8` or `ec13292333b9` was changed because the assignment permits edits only to the selected generator component. Findings and limitations are recorded in `AUDIT.md` and under `checks/audit/`.

<!-- arcpuzzles-current-audit-assessment:start -->
## Current bounded audit assessment

Return: `review-a1e69e9fdec20d2f:v0001`. Disposition: **no_issue**. Evidence basis: `reviewer_reported`.

Audited source SHA-256: `4ca19b6bba81335a3774646ab3a6e294597eb7042abb66e9e15e6840e7018340`. At disposition, audited bytes match the current source.

### Current decision

Reviewer-reported on unchanged source 4ca19b6bba81335a3774646ab3a6e294597eb7042abb66e9e15e6840e7018340. Documented ordered-curriculum boundary reproduced, with no new source defect: 12 tests and the semantic gate pass, and 30 production lessons have zero ambiguity. Diagnostic arbitrary query rotations have 46/120 ambiguities. The easy seed=2311497931/index=0/query=1 witness lets ignore_thin_horizontal fit the other three demonstrations. Retain the limitation; this is not an arbitrary-rotation approval or resolution of other reports. Retain source-bound evidence: `checks/audit/5c577e82a07f-combined.console.log` `checks/audit/5c577e82a07f-combined/RUNTIME_MANIFEST.json` `checks/audit/5c577e82a07f-combined/checks/5c577e82a07f_audit_battery_summary.json` `checks/audit/5c577e82a07f-combined/checks/5c577e82a07f_audit_commands.jsonl` `checks/audit/5c577e82a07f-combined/checks/5c577e82a07f_audit_semantic_gate.json` `checks/audit/5c577e82a07f-combined/checks/5c577e82a07f_audit_semantic_gate.log` `checks/audit/5c577e82a07f-combined/checks/5c577e82a07f_audit_semantic_gate.ok` `checks/audit/5c577e82a07f-combined/checks/5c577e82a07f_audit_semantic_gate.receipt` `checks/audit/5c577e82a07f-combined/checks/5c577e82a07f_audit_summary.json` `checks/audit/5c577e82a07f-combined/checks/task_tests.xml` `checks/audit/5c577e82a07f-combined/progress.log` `checks/audit/5c577e82a07f-combined/result.json` `checks/audit/5c577e82a07f-rotation-census.console.log` `checks/audit/5c577e82a07f-rotation-census.json` `checks/audit/5c577e82a07f-rotation-census.summary.json` `checks/audit/5c577e82a07f-rotation-witness.json`

### Assessment or prior finding

## 5c577e82a07f

**Finding type: documented domain limitation reproduced; no new source defect.**

The isolated audit preset passed: 12/12 task tests and a green semantic gate on
generator SHA-256
`4ca19b6bba81335a3774646ab3a6e294597eb7042abb66e9e15e6840e7018340`
(`checks/audit/5c577e82a07f-combined/result.json`). A separate source-bound
rotation census materialized 30 ordered production lessons (10 per band):
0/30 production lessons were ambiguous and 0/120 labelled production pairs were
ambiguous.

Arbitrary query rotation is not supported by this curriculum. When every pair
was held out once under diagnostic policy, 46/120 rotations were ambiguous. The
first exact witness is easy-band seed `2311497931`, sample index `0`, query index
`1`, with train indices `[0,2,3]`: the rival `ignore_thin_horizontal` fits all
three remaining demonstrations but predicts a different output for the held-out
thin-horizontal pair. The input, canonical output, rival output, demonstrations,
source hashes, and warning are retained in
`checks/audit/5c577e82a07f-rotation-witness.json`; the complete census is
`checks/audit/5c577e82a07f-rotation-census.json`.

The target already documents ordered-curriculum semantics and does not claim
arbitrary rotation support, so this is a verified boundary rather than a repair
request. No target source was changed.

The disposition records an explicit decision. It does not imply a fresh execution, universal correctness, closure of other findings, or training admission.
<!-- arcpuzzles-current-audit-assessment:end -->

## D10 — Native two-setting family preserves the approved default

**Decision.** Add task-local `enclosure_policy` with `borders_only` and
`largest_enclosure`. The default returns the exact canonical Racket source
byte-for-byte (SHA-256
`486ca16c83e15864e35f8c366a80e1370c46ef77022e9d549af3cf4268193553`).
The approved production generator remains unchanged at SHA-256
`4ca19b6bba81335a3774646ab3a6e294597eb7042abb66e9e15e6840e7018340`.

**Alternate behavior.** First complete every inferred rectangle border, then
recompute 4-connected zero regions on the completed grid, discard regions that
touch the boundary, and paint only the unique largest enclosed region with
color 8. Nested rectangles make the selected region an input-dependent annulus
or pocket instead of a direct original-rectangle fill.

## D11 — Constructive curriculum and finite adversarial bank

The native adapter independently supports 2–6 demonstrations and 1–4 queries,
keeps four stored queries distinct, preserves identical visible inputs across
settings for matching seeds, and reveals one masked query at a time without a
total-count hint. The first demonstrations include thin horizontal, thin
vertical, and nested cases. The fourth query is a 30×30 triple-nested stress
scene spanning every boundary and quadrant.

`workspace/parametric/audit.py` attacks declared executable rivals (identity,
partial-border, direct-fill, all/smallest/first/last enclosure, original-box,
skip-completion, and wrong-color variants), checks parameter/input parity and
public projection, executes selected labels through protected Racket, and emits
content-addressed public challenges. Its finite rival result is not a universal
identifiability proof.

## D12 — Source-bound sequential dependency retained

A protected-Racket causal witness binds the qualified source. Step A completes
the borders. The intermediate recomputes enclosed zero regions and retains the
unique largest. Step B paints that retained region. On the 30×30 query, border
completion creates enclosed regions of sizes `[256, 297, 99]`; the correct
middle annulus has 297 cells. Replacing it with the smallest-region
intermediate changes the final output, so B cannot be computed from the raw
corner grid alone under the declared algorithm.

Evidence: `checks/5c577e82a07f/causal/witness.json` and
`checks/5c577e82a07f/causal/final-replay.json`.

## D13 — Qualification result and remaining owner step

Native qualification passed four jobs (both settings, seeds 0 and 17, three
demonstrations, four queries) with 40 protected-Racket evaluations. The final
50-seed/all-count audit passed 2,000 episodes and 13,000 labelled pairs, including
1,000 matched-input comparisons, 200 query-prefix checks, 13,000 topology checks,
800 rival checks, and 42 protected-Racket labels. The focused staged suite is
19/19 green and two saved public challenges pass strict masking/identity checks.

This reviewer return is **ready**, not accepted. Owner exact-source integration,
fresh native acceptance replay, and any training admission remain pending;
`training_admitted` is false. Optional peer checks `5aa2b1bf7760` and
`55993f4c12af` were not run after MAIN was completed and adversarially checked.

