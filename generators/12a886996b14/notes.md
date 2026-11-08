# Working notes: 12a886996b14

## Current decision

Generator `3.0.0` models the canonical translation analogy rather than a marker-token surrogate. Red (2) and green (3) are placements of one connected marker template; yellow (4) may hide a proper subset of the red source. The vector between marker bounding-box top-lefts is applied to one connected irregular yellow object on a fresh blank grid.

Final generator SHA-256: `03f0f6d5b397fa53f9d2cc6d40c2a349be7076893bffc2073241c2d5d94c2d5b`. Canonical rule pin: `8de52d1da0e7`.

## Reversed baseline choices

The issued `2.0.1` source used singleton red/green cells, allowed malformed `no_red`, `no_green`, and collision-based `zero_delta` textures, and advertised controls it did not honor. Those choices were not supported by the canonical examples. They were replaced by a strict lawful grammar with six observable axes: grid height/width, marker size, yellow size, source occlusion, and vector direction. There are no production degenerates or palette aliases.

## Teaching design

Lessons use two demonstrations plus one query. A six-slot direction/occlusion schedule guarantees that every three-consecutive-pair window, under any query rotation, retains upward-motion and partial-occlusion evidence. Declared rivals are `always_down`, `equal_visible_markers_only`, and `translate_filled_yellow_bbox`; executable witnesses and `lesson_identifiable` reject surviving competitors.

The strongest canonical-fitting rival is `always_down`, because every canonical labeled pair has positive row displacement. Exact refutation: `checks/counterexamples/12a886996b14/always_down_upward.json`, verified against the selected Racket authority in the adjacent `racket.json`.

## Verification status

- Before battery: 5 green, 2 advisory, 5 failed.
- Final required-rotation battery: 12/12 green.
- Selected task tests: 23/23 passed.
- Random census: 300/300 lessons, 900 unique inputs and rotations, zero reported ambiguity/errors.
- Fixed-seed schedule census: 18/18 start-residue lessons and 54/54 rotations, zero reported ambiguity/errors.
- Post-repair visible-only solve: first revision passed 3/3 demonstrations.

The canonical Racket behavior was not changed. Only the selected/archival base-bank text and role metadata were synchronized exactly to canonical to remove a diagnostic source divergence.

## Limits

These checks establish support against the declared finite rival set, not universal induction. The schedule enumeration fixes seed 0; seed-independent witness slots are tested broadly but not formally proven for every geometric draw. Colors remain fixed semantic roles, and sizes stay within the declared compact canonical-scale domain.

Imported associated notes retain original evidence/timestamps in `evidence/associated_notes.jsonl`.

## Audit resolution

The absent-red-marker audit (`review-127df307b670c69c:v0001`) is resolved by the exact v3.0.0 repair above: malformed missing-marker and collision texture values are removed and rejected. Closure relies on the reviewer-reported negative fixtures and selected checks; the canonical rule remains unchanged.
## Current reviewer considerations

Source SHA-256: `03f0f6d5b397fa53f9d2cc6d40c2a349be7076893bffc2073241c2d5d94c2d5b`.

# Decisions for `12a886996b14`

## Objective and success criteria

The repair had to produce lawful training inputs that teach the canonical bounding-box translation analogy, preserve the canonical Racket behavior, expose only controls that are real and observable, and remain identifiable with two demonstrations when any of the three lesson pairs can become the query. Success meant a fully green required-rotation battery, selected task regressions, a broad lesson census, and an exact counterexample to the strongest canonical-fitting shortcut.

The historical rationale for the issued singleton-marker distribution is not recorded. Its code comments describe convenience rather than a task-specific reason, so I treated its singleton restriction and malformed degenerates as implementation artifacts, not requirements.

## Distribution choices

### D1 — Real matching marker shapes, not singleton stand-ins

Red and green now encode the same connected template of 3–6 cells. The translation vector remains the difference between their bounding-box top-lefts, exactly as in the authority. This preserves the structural analogy visible in canonical examples and prevents a learner from reducing the task to two unrelated coordinate tokens.

Rejected alternative: retain single cells and merely add stronger validation. That would make labels correct but continue to erase the task’s shape-copy evidence.

### D2 — Model canonical source occlusion explicitly

The `occlusion` axis is `none|partial`. In partial cases, yellow covers a proper subset of the red source template, while the complete green copy reveals the hidden cells. The red anchor itself remains visible so the bounding box is well-defined. Validation permits missing red cells only when yellow explains them.

Rejected alternative: require red and green to be visibly identical in every generated input. One canonical pair directly contradicts that simplification, and the `equal_visible_markers_only` rival would survive.

### D3 — One connected irregular yellow object

Yellow size is 3–8 cells, always one 4-connected non-rectangular object. This gives a meaningful shape to translate and refutes the rival that fills and translates the yellow bounding rectangle. Tiny isolated yellow points and unrelated multiple objects were removed from the production grammar.

Rejected alternative: independent random yellow cells. It increases superficial diversity while weakening object-level teaching and can make bbox-filling shortcuts hard to diagnose.

### D4 — All direction classes, with a teaching schedule

The exact `vector_direction` axis supports all eight nonzero sign classes. Production uses a six-slot schedule:

`down_right, up_left, up_right, down_left, up, up_right`.

Canonical labeled pairs all have positive row displacement, so the strongest public-only rival preserves horizontal displacement but forces `dr = abs(dr)`. Four of six slots move upward; every three-slot lesson window contains at least two upward cases. This guarantees that both ordered lessons and all three query rotations retain a demonstration that refutes `always_down`.

Rejected alternative: sample directions independently. Good marginal coverage would not guarantee that each complete lesson contains a disambiguating witness.

### D5 — Two demonstrations plus one query

`EXAMPLES_NEEDED = 2`. This is the smallest lesson that can preserve the intended analogy while refuting scheduled rivals under all query rotations. The semantic hook validates every pair and rejects a lesson whenever a declared competitor fits all demonstrations but changes the query answer.

Rejected alternative: rely on individual-grid correctness or frequency statistics. Neither establishes that a particular lesson teaches the rule.

### D6 — Canonical-scale grids and strict observable axes

Declared axes are only `grid_h` (9–14), `grid_w` (12–16), `marker_size` (3–6), `yellow_size` (3–8), `occlusion`, and `vector_direction`. Every value is recoverable from the resulting grid, every legal cross-product combination is realizable, and unknown controls fail closed. Difficulty changes default size bands but does not silently narrow explicit overrides.

Removed as dead or misleading: `palette_kind`, `palette_size`, `position_bias`, `n_distinct_colors`, `density`, `texture`, and `n_yellow`. Colors are fixed semantic symbols in this task; exposing palette controls would imply interchangeability that the rule does not have.

### D7 — No lawful degenerate textures

`no_red`, `no_green`, and the former collision-based `zero_delta` are malformed for this rule and no longer appear as production textures. They are represented instead as negative mutation fixtures that validation must reject.

Rejected alternative: keep them as “edge cases.” The canonical Racket program requires both marker bboxes, and the old zero-delta construction did not actually contain both colors at one cell.

### D8 — Preserve authority behavior; synchronize source text

The canonical Racket algorithm already expresses the intended rule and passed canonical replay. I did not change its behavior. The selected base-bank `target_code` was synchronized exactly to its canonical/archival `raw_code`, and role metadata now states which copy is archival and which is selected. This resolves authority diagnostics without introducing a second implementation.

## Testing and probes

Tests were written before the replacement implementation and initially produced 22 expected behavioral failures plus one pre-existing determinism pass. The final 23-test suite covers all canonical pairs, every exact axis and direction, source occlusion, all query rotations of every schedule window, the `always_down` counterexample, malformed semantic mutations, invalid override handling, deterministic fresh returns, and global RNG isolation.

The final required-rotation battery passed all 12 stages. A production census materialized 300 lessons—100 per band—and checked 900 unique pair inputs and 900 query rotations with no reported ambiguity, hook, scoring, or materialization errors. A separate fixed-seed run enumerated all 18 band/start-residue lessons and all 54 rotations. Exact evidence is listed in `REVIEW.md` and `RESULTS.json`.

## Decision reversal from the issued version

The central reversal is from “minimal marker tokens plus optional malformed degenerates” to “canonical-like shape analogy with only lawful, observable variation.” This is not cosmetic broadening: it changes what evidence a learner receives while leaving the label rule unchanged. The prior generator’s wide-looking metadata was replaced with a smaller but truthful axis contract.

## Known limits

- The semantic checks cover the three declared competitors and the canonical-fitting `always_down` shortcut; they cannot establish uniqueness against every possible program.
- Exhaustive schedule enumeration is at seed 0. The deterministic witness schedule is seed-independent, but geometric realization across all possible seeds is supported by sampling and tests rather than formal proof.
- Marker and yellow sizes are intentionally bounded to compact canonical-scale shapes. Larger shapes and grids are outside this generator’s declared domain.
- Fixed colors 2, 3, and 4 are semantic roles, not a palette generalization.

## Native parametric reviewer addition — 2026-10-24

The approved production generator remains byte-for-byte unchanged at SHA-256
`03f0f6d5b397fa53f9d2cc6d40c2a349be7076893bffc2073241c2d5d94c2d5b`.
A separate native family now exposes the episode-fixed parameter `finish`:

- `translate_only` uses the exact canonical program bytes (SHA-256
  `e82fb1f39767ac9e312cf6d13978d729a74c5ed664349c2903b94e4eb6a3836c`).
- `cue_payload` first performs the canonical red-to-green translation, then
  identifies the unique cue color adjacent to the translated yellow footprint
  and paints that color's remote payload cyan while retaining the translated
  yellow object.

The sequential dependency is non-cosmetic. Step A infers the input-derived
red-to-green vector and produces the translated yellow footprint. That footprint
is the intermediate consumed by Step B: only after translation can the rule
choose the adjacent destination cue and therefore the remote payload. The
retained `source_cue_payload.rkt` counterfactual selects beside the untranslated
source footprint instead and changes nine final cells under protected Racket.
Evidence is `workspace/parametric/evidence/current/causal-case.json` and the
packaged replay at `checks/12a886996b14/authoring/causal-case.json`.

The family supports 2–6 demonstrations and four distinct sequentially revealed
queries, keeps matched inputs across settings, hides future queries/settings/
programs/answers, and includes a substantive 30×30 boundary case. The bounded
authoring audit covered both settings, seeds 0/17/97, demo counts 2/3/6, 18 jobs,
272 protected-Racket evaluations, and eight declared rivals. Native
qualification passed four jobs and 40 additional protected-Racket evaluations.
This is reviewer-ready only: exact-source owner acceptance remains pending and
training admission is false.
