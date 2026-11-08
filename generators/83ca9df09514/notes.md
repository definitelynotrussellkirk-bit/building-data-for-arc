# Working notes: 83ca9df09514

## 2026-10-12 review repair

Baseline generator SHA-256 `7d068dc1322ff083685edefd22448d319d52fcc3d056b51a6793c639dba92277` advertised controls it did not honor, accepted unknown controls, produced invalid negative textures, matched none of the five canonical profiles in 60 profile-floor draws, and declared no semantic teaching contract. The baseline battery was 6 green / 2 advisory / 4 failed; the override checker retained 19,708 findings.

Selected generator version `3.0.1`, SHA-256 `70db137b815d1463c9b759c9258749291aef361633d91fbf64e7c72c8d6f2233`, replaces that surface with six fully constructive axes and no texture modes. Its ten-sample cycle emits the five exact canonical profiles first and five contrastive widths second. Strict request validation rejects unknown, mistyped, out-of-range, and `None` overrides.

Three shortcuts fit all ten canonical labelled pairs: read only the first three columns, assume exactly two template groups, and assume the template is row one. Generated samples deliberately refute all three. The lesson contract additionally refutes unchanged sparse rows, one destination color per row, and reuse of the first key mapping. Retained witness: `counterexamples/semantic_shortcuts.json`.

The selected canonical Racket program was not changed. Two selected base-solution `target_code` fields were synchronized byte-for-byte to that canonical program while both archival `raw_code` fields were preserved. The source-hash-pinned, pointer-limited plan and receipt are in `workspace/manual_authority_sync_plan.json` and `workspace/manual_authority_sync_receipt.json`.

Final evidence: 12/12 battery stages green; 62/62 task-local tests; 48,690/48,690 override draws accepted with zero findings; 300/300 lessons and all 1,200 hold-one-out query rotations unambiguous against six unique declared rivals. These finite rival checks do not prove universal identifiability.

No prior return was treated as evidence for the repair; current selected source, canonical data, current battery output, and fresh probes were used. Imported associated notes remain in `evidence/associated_notes.jsonl`.
## Current reviewer considerations

Source SHA-256: `70db137b815d1463c9b759c9258749291aef361633d91fbf64e7c72c8d6f2233`.

# Decisions for 83ca9df09514

## D1 — Replace the generator surface instead of patching individual symptoms

The baseline failures shared one root cause: its public contract described more controllable structure than the implementation could construct. Keeping that architecture would have required special-case rejections, hidden coercions, or inert controls. I replaced it with a smaller truthful surface and retained the unchanged canonical rule.

Rejected alternative: keep `texture`, `anchor_corner`, `palette_size`, and other historical knobs while selectively ignoring or forbidding combinations. That would preserve the defect class the override checker exposed and make future joint-axis reasoning harder.

## D2 — Six constructive axes, no texture modes

The selected axes are `grid_h` 6–16, `grid_w` 8–18, `n_keys` 1–4, `n_groups` 2–4, `template_position` in `{top,middle,bottom,random}`, and `key_layout` in `{prefix,shifted,scattered}`. Every legal Cartesian product is constructive; no incompatible-combination table is needed. Requests are strict: booleans are not integers, `None` is not a default, unknown axes fail, and out-of-range values fail.

This makes exact-control provenance observable through `observe_overrides` and allows the exhaustive shared override gate to test the entire declared surface. The final gate accepted 48,690/48,690 draws with no findings.

## D3 — Canonical anchors plus contrastive widths

The default ten-sample cycle is deterministic. Slots 0–4 emit the five exact canonical `(height,width,palette-size)` profiles:

`(6,8,5)`, `(10,8,5)`, `(10,8,7)`, `(12,8,8)`, `(14,10,7)`.

Slots 5–9 preserve the corresponding height/palette anchors while using widths `(18,15,12,9,17)`. This choice fixes the baseline's zero canonical-profile support without making the declared width range override-only. The schedule is global-RNG-pure and fresh-copy deterministic.

Rejected alternative: sample every dimension uniformly. It would improve envelope diversity but make exact canonical support probabilistic and weak, especially for palette size. Canonical anchors are more valuable for this task; explicit overrides still cover the full legal dimension range.

## D4 — Preserve the actual template/key semantics

The template is the unique nonzero full row. It contains 2–4 repeated template-color groups. Each key row is sparse but reveals a destination for every group; group zero is deliberately revealed twice, and each template group has at least two members. The output expands the row-specific mapping over all columns in each template group.

I did not add distractor objects or noise because they would create a different parsing task and could invalidate the selected Racket program. Variation comes from dimensions, group count, key count, template position, reveal layout, colors, and column assignments.

## D5 — Treat canonical ambiguity as a curriculum requirement

All ten labelled canonical pairs are also solved by three wrong rules: use only the first three columns, assume exactly two template groups, or assume row one is the template. The generator declares these in `CANONICAL_SHORTCUTS` and deliberately refutes each in every generated sample.

Three additional lesson competitors cover other plausible errors: leave sparse rows unchanged, fill one destination color per row, and reuse the first key row's mapping. Each competitor has a named semantic witness and a retained disagreement example. A lesson is accepted only when every rival that changes the query is contradicted by the demonstrations.

## D6 — Three demonstrations, one query, arbitrary holdout rotation

`EXAMPLES_NEEDED = 3`. The actual lesson assembly uses four consecutive labelled pairs: three demonstrations and one query. This curriculum supports arbitrary query placement, so required rotation—not diagnostic rotation—was used. The smoke gate checked 12 materialized lessons and 48 rotations; the wider census checked 300 lessons and all 1,200 rotations.

Rejected alternative: rely on a fixed final query position. That would allow ordering-correlated hypotheses to survive and would make lesson quality depend on downstream assembly details.

## D7 — Synchronize selected authority, preserve archival evidence

The canonical Racket program already expressed the intended rule and was not edited. The two selected base records had semantically equivalent but exact-text-divergent `target_code`. I used a task-local tool that verifies source-file hashes, JSON pointers, old values, canonical target bytes, and raw archival hashes before applying only those two pointer replacements.

Both `raw_code` fields remain byte-identical to the baseline. The final authority audit reports `SELECTED_SYNC_ARCHIVAL_DIVERGENT`, which is intentional: active selected code is exact-canonical; archival source remains historical. Execution parity passed all five canonical applications for both forms.

Rejected alternative: rewrite archival `raw_code` to make every authority string identical. That would erase provenance without adding execution value.

## D8 — Retain future-agent tooling and a minimized witness

`workspace/review_probe.py` independently checks canonical ownership, profile support, representative joint overrides, shortcut truthfulness, and query rotations. `workspace/manual_authority_sync.py` makes the narrow authority operation replayable. `counterexamples/semantic_shortcuts.json` binds a single generated case to the final source hash and records differing-cell counts for all three canonical-fitting shortcuts.

## Limits

The evidence is finite and source-bound, not universal. Six declared rivals and seven generic searched rivals do not enumerate every hypothesis a model could learn. The 300-lesson census samples production starts and rotates each materialized bundle; it does not enumerate every seed or semantic equivalence class. Those limits are reported rather than converted into unsupported claims.

## 2026-10-23 proposed parametric extension: duplicate-key precedence

The selected production generator and canonical authority remain unchanged at generator SHA-256 `70db137b815d1463c9b759c9258749291aef361633d91fbf64e7c72c8d6f2233` and rule hash `1dc6f00b70c9`. The new task-local prototype is `workspace/parametric/prototype.py`; it is **proposed and unapproved**, not a production repair or training admission.

### D9 — Parameterize only conflicting duplicate-key precedence

The canonical rule builds a per-row hash from sparse key cells. When two nonzero keys align to the same template color but carry different destinations, ordinary left-to-right traversal makes the rightmost key win. Production inputs never create that conflict, so the behavior is executable but previously unexercised.

The prototype adds one episode-fixed parameter, `duplicate_precedence ∈ {rightmost_wins, leftmost_wins}`. `rightmost_wins` is the byte-identical canonical source (SHA-256 `cae56e2f8161ccd2fd21aa8b0d4e0b51318d3e114e626ea9097fab7c2602af87`). `leftmost_wins` changes exactly one traversal expression from `(range 0 w)` to `(reverse (range 0 w))`; template discovery, row roles, grouping, blank-row behavior, colors, and broadcast semantics are unchanged.

Rejected alternatives: change key-row order, choose a fixed destination, or parameterize template discovery. Those alter larger parts of the reasoning pattern or mix multiple latent rules. Precedence is the smallest visible extension of an already defined implementation boundary.

### D10 — Keep inputs paired and the parameter fixed per episode

Consecutive seeds selecting opposite settings share the same inputs, so comparisons isolate the rule rather than the sampler. Every nonblank sparse row is modified to contain a real conflicting duplicate aligned to one template group. The retained episodes use two demonstrations and four distinct queries; demo and query counts are independently validated in the range 1–8.

Demonstrations alone refute the opposite setting before query answers are considered. This establishes identification only against the one declared rival setting, not arbitrary programs. Conflicting duplicate keys extend the production generator's accepted grammar and remain prototype-local.

### D11 — Guard exact programs and separate public/private evidence

Rule materialization accepts only the pinned canonical bytes or the exact one-loop alternate. Trailing bytes, unrelated edits, and double mutations are rejected. Public challenge files contain only demonstration input/output pairs and query inputs; seeds, settings, program text/hashes, rival predictions, and query answers stay private. Public filenames are hashes of the exact visible bytes, and batch manifest rows are sorted by those public IDs regardless of caller seed order.

Retained evidence: `WORK/checks/parametric/duplicate-precedence-v1/`. It includes two content-addressed public episodes, exact private Racket programs, all ten source-qualified canonical replays under the default, and a cross-setting witness. The adversarial boundary pass also exercised the maximum configured 8-demo/8-query sampler (16 distinct paired inputs), exact one-loop mutation, tamper rejection, and 1-demo/8-query lesson identification.

### Verification and limits

Six focused prototype tests and the unchanged production suite pass together: **68/68 task-local tests**. The default replays all ten canonical labeled pairs. All retained labels and rival predictions were executed by the bundled Racket runtime. No production source, canonical data, catalog metadata, approval state, or shared runtime changed.

The evidence is finite and bounded to two declared settings and materialized seeds. It does not prove universal identifiability, production suitability, or training value. The next useful action is an independent source-bound review of whether conflicting duplicate keys are a desirable family extension; only after that decision should a maintainer consider a production/export route.

<!-- arcpuzzles-current-supplementary:start -->
## Current supplementary checks

Current source-bound ticket observations: `generators/83ca9df09514/evidence/supplementary-current.json`. Results are reviewer-reported; blocked or unknown stays explicit. These observations do not approve a generator or variant, resolve audits, or admit data to training.
<!-- arcpuzzles-current-supplementary:end -->
