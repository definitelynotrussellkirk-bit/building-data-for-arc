# Review return — review-0d2e13441e2290ff

Source: SEND-THIS-ARCpuzzles-review(20261025-172246).zip; packet 283e14fd875413e9e121690b8f01a9eec13cab2dfc8b0290a52827a67f78e6c9.
**Needs attention: this is a partial-status return, not a completed two-parent admission.**
Both previously missing references, generators and parameterized candidates are built and executed.
`public_eval_a6f40cea` is **blocked for semantic review**, despite exact-label/preflight success.
`public_eval_67e490f4` is **reviewer-ready**, not owner-qualified or accepted.
Original protected-Racket labels: 4/4 and 3/3. Official staged tests: 21/21 per target.
Final combined suite: 82/82, including 40 helper tests; public-view checker: 32/32, zero findings.
Finite audits: 192 lessons / 1,472 pairs per target; protected boundary labels: 40 per target.
Source-bound causal replays: 55 and 6 changed cells, respectively, on substantive 30×30 inputs.
No shared authority, supplied labels, owner approvals or training-admission state was changed.

## a6f40cea — reconstruction built, stripe semantics unresolved

The reference recovers rectangular outlines from exposed fragments, reconstructs their hidden perimeter coordinates inside the largest green window, and paints the window interior. The sampler varies palettes, dimensions, position, orientation and optional smaller window distractors; its current grammar uses three or four spatially separated rectangles with all extrema exposed.

Two executable phase conventions are retained. `restart_hidden` starts each hidden striped border at its first row-major hidden coordinate with the smaller palette color and alternates by row-plus-column parity. `continue_visible` extends the phase inferred from the visible border. The former reproduces all supplied labels without looking up any supplied input or output; the latter differs on exactly eight cells of train[2].

**Why the hold is real:** in zero-based original coordinates, visible cell (13,15) is 9 while the supplied hidden answer at (13,13) is 8. They have equal parity, so a uniform period-two continuation along that row would require equal colors. The other three original labels do not distinguish the two conventions. This does not prove that the supplied answer is wrong: there may be another intended rule. It does mean that exact-label success under the restart convention is insufficient evidence of intended semantics. The restart reference is a compatibility hypothesis, not an established canonical interpretation.

`checks/public_eval_a6f40cea/phase-evidence.json` executes both programs on all four originals (eight protected evaluations). `periodic-conflict-report.json` independently reports 16 consistent visible observations and eight contradictory hidden completions under the stated periodic hypothesis. No official label was repaired or silently discarded.

The spatial dependency is independently established: shifting the reconstructed rectangle column extrema before building the hidden perimeter mask changes 55 final cells on the retained 30×30 query. This causal result does not resolve the separate phase question. Both programs and all candidate source are returned, but RESULTS deliberately has `outcome: blocked`, `parametric_work.status: blocked` and null `prototype_path`; `candidate_source_path` identifies the built adapter.

**Next owner action:** adjudicate the phase convention against the parent, or authorize a corrected semantic specification; then refresh source-bound tests/preflight and perform registration/native acceptance. Do not admit this candidate to training merely because its current reference matches the supplied labels.

## 67e490f4 — shape-conditioned frequency voting

The reference finds the large template, extracts its four-connected background holes, matches each hole to external same-color eight-connected glyphs up to all eight rotations/reflections, and constructs a separate color-frequency histogram for each shape class. It fills each hole with the most frequent matching color, counting object instances rather than pixels. The alternate `least_frequent` setting chooses the least positive count; ties choose the smallest numeric color.

The constructor varies palettes (including zero), glyph shapes, orientation, template placement and count ties. The minimum two demonstrations contain chiral matches and distinct equal-area/equal-box shapes with different winners, while preserving a four-query bank independent of the requested demonstration count. The admitted sampler grammar currently uses three shape classes and six holes; it does not claim arbitrary template generation.

The first finite audit exposed two genuine teaching gaps: rotation-only matching fit a short lesson before changing a query by eight cells, and bounding-box matching did likewise on another lesson. Both exact failures, saved Racket programs and all grids were frozen before the repair in `checks/public_eval_67e490f4/frozen-shortcuts.json`. A fresh sampler-independent replay in `frozen-replay.json` reconfirms both eight-cell failures with 12 protected evaluations. A subsequent minority-tie loophole was repaired by varying unique counts and ties across the first two demonstrations; the intermediate failed audit remains retained.

The causal witness replaces each shape-specific color histogram with global per-color object counts while retaining the same candidate palette and geometry. Six final cells change on the retained 30×30 query. Final source-specific audits reject every harmful declared rival; 96 surviving equivalent cases are explicitly reported as harmless, not suppressed.

## Executed evidence and limits

| Check | a6f40cea | 67e490f4 |
|---|---:|---:|
| Original labels, protected Racket | 4/4 | 3/3 |
| Official staged task tests | 21/21 | 21/21 |
| Finite audit lessons / pairs | 192 / 1,472 | 192 / 1,472 |
| Declared candidate policies | 10 | 13 |
| Authoring-preflight jobs | 4/4 | 4/4 |
| Additional protected boundary labels | 40 | 40 |
| Saved single-query public views | 16 | 16 |
| Source-bound handoff validation checks | 216 | 216 |
| Fresh protected causal difference | 55 cells | 6 cells |

Both samplers support 2–6 demonstrations and exactly four distinct queries, matched inputs across settings, a distributed 30×30 query, and private shuffled one-query presentation. The final combined suite is `checks/final-tests.xml` / `final-tests.txt` (82 passed). Saved public files were independently checked by the packet's `check_public_exports.py`, with zero findings (`public-exports-check.json`).

Each final handoff validator regenerated the retained finite audit, rechecked public bytes, validated the owner's witness schema and executed a fresh protected causal replay. It binds 153 files per target. `checks/final-integrity.json` additionally rehashes all 249 files in each official staged-test binding, reconciles the reference/model copies and original pairs, and checks the 82-case XML receipt.

The broad finite rival audits use explicit Python models. Original-pair, preflight, boundary, frozen-counterexample and causal evidence execute protected Racket. Finite competitor elimination is not a universal uniqueness proof. Preflight is not native qualification; no owner registration, acceptance or training admission was performed. Final review was an author self-review because no independent reviewer subagent was available.

## Reusable tools

- `checks/periodic_completion.py`: bounded periodic-consistency diagnostic with 12 regression tests; reports conflict/inconclusive/inconsistent observations instead of silently choosing a majority. Its periodic hypothesis is explicit and is not a puzzle-intent oracle.
- `checks/replay_frozen.py`: replays saved equal-demonstration/different-query counterexamples through protected Racket without calling the sampler; six regression tests and a fresh 12-evaluation integration replay.
- `checks/authoring_evidence.py`: reused and revalidated preflight-bound public export, boundary and causal builder/validator, with 12 regression tests.
- `checks/verify_source_delta.py`: reused and revalidated exact-baseline patch round-trip validator, with ten regression tests. Run it on the final returned ZIP before integration; do not overwrite a divergent live tree.

## Replay entrypoints

From the extracted outer folder:

```sh
python3 review.py task-tests public_eval_a6f40cea --phase after --timeout 180 --out ../checks/public_eval_a6f40cea/task-tests
python3 review.py task-tests public_eval_67e490f4 --phase after --timeout 180 --out ../checks/public_eval_67e490f4/task-tests
python3 review.py run python3 ../checks/replay_frozen.py ../checks/public_eval_67e490f4/frozen-shortcuts.json --out ../checks/public_eval_67e490f4/frozen-replay.json
python3 review.py run python3 ../checks/public_eval_a6f40cea/phase_evidence.py
python3 review.py run python3 -m pytest --import-mode=importlib -q generators/public_eval_a6f40cea/tests generators/public_eval_67e490f4/tests ../checks/tests
```

Final validation uses `authoring_evidence.py verify --root . --preflight ../checks/TASK/preflight/preflight.json --out ../checks/TASK/delivery --replay --report ../checks/TASK/handoff-validation.json` through `review.py run python3`. The `freeze_findings.py` script records historical creation provenance; replay the frozen file rather than trying to recreate the old failing inputs from the repaired sampler.
