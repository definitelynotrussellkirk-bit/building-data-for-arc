# Working notes: b4ecb537757c

## Current repair

Version **3.0.0**, source SHA-256
`5dcb55bec544f478c1c7c366e680a60e678799b4669103deb2ef74cce781f467`;
Racket authority **`1232696ab606` is unchanged**. Labels remain authoritative
Racket outputs. This source pin is a review binding, not an approval claim.

The baseline checked the unrotated insert bbox. The retained seed-0 sweep,
indices 0–79 per band, found **54/240** inputs with transformed-fit failures
(easy 7/80, medium 21/80, hard 26/80). Generation now checks the selected
rotation, and the validator rejects overflowing, foreign-cell-bbox, and nested
frame cases. See [counterexamples](counterexamples/) and the
[baseline evidence](../../../checks/independent-review/baseline-probe.json).

The validator recognizes complete monochrome four-neighbor frames in colors
1–9, including a single surviving frame. It requires one isolated key in
1–4, one external matching insert with a pure bbox, and disjoint complete
frame rectangles. It accepts the four canonical inputs, including ignored
overwritten-frame fragments and orphan key-color singletons. It does not
generate damaged frames or missing-key/default cases.

## Distribution and compatibility

Direct separated-pocket construction replaces bounded random retries and the
fixed fallback. Exact axes are only `grid_h=7..22`, `grid_w=12..24`, and
`n_frames=1..4`; impossible combinations and invalid/retired axes fail visibly.
The old palette, density, placement, and texture axes are retired. Version 3
changes seed/index realizations.

Default residues 0–3 of an eight-draw period use one-frame 7×12 three-color
scenes in every band. Residues 4–7 vary feasible dimensions and frame counts.
Frames have height/width 4 or 5. Seven 3–7-cell motifs with four distinct
orientations keep keys informative. Jitter, reflections, color assignment, and
cross-pocket insert permutation provide variation within those limits.

## Lesson decision and retained reversal

Seven demonstrations plus one query span eight consecutive draws. Each key
appears on the first construction role twice. A review of the previous
consecutive-role-key design found a canonical-fitting descending-rank shortcut:
easy seed 3, indices 0–7, holdout 4. Its seven demonstrations fit while its query
answer changed; the earlier hook missed it. The
[frozen lesson](workspace/cyclic_key_lesson.json) retains that source-bound failure.

Other-role keys now vary independently, except that residues 4 and 6 provide
opposite-key pairs or nonuniform repeated-key tuples. Either anchor refutes
uniform and ±1 spatial key progressions, leaving one after any single holdout.
There are 17 declared rivals, including two canonical-fitting shortcuts.
Exact overrides still need their actual lesson assembly checked.

## Verification and remaining limits

The pinned source passed **12/12 release battery stages** and **72 portable
task tests**. Its [release census summary](../../../checks/lesson-census-release.summary.json)
reports **300 lessons / 2,400 rotations**, zero ambiguities or hook/runtime
errors, and **2,398 unique inputs** across 2,400 pair slots. Exact commands and
the separate smoke/fixed-period counts remain in the review's `RESULTS.json`
and `REVIEW.md`; earlier `after-final`/`after-reviewed` paths are intermediate.
Fixed pockets, seven motifs, and small frames restrict support. The fixed-seed
period census and finite rivals cannot establish all-seed or universal lesson
identifiability, and no downstream training improvement has been measured.
## Current reviewer considerations

Source SHA-256: `5dcb55bec544f478c1c7c366e680a60e678799b4669103deb2ef74cce781f467`.

# Decisions: b4ecb537757c

## Scope and source

The repair is generator version **3.0.0**, candidate SHA-256
`5dcb55bec544f478c1c7c366e680a60e678799b4669103deb2ef74cce781f467`.
The selected Racket authority remains **`1232696ab606`**. Python scene inspection
and rivals supply diagnostics; all retained puzzle labels come from Racket.

These bytes passed **12/12 battery stages** and **72 portable task tests**.
The release census materialized **300 lessons**, scored **2,400 query rotations**,
and reported zero ambiguities, hook warnings, or materialization/scoring errors;
its 2,400 pair slots contain **2,398 unique inputs**. See the
[battery summary](checks/after-release/checks/b4ecb537757c_after_battery_summary.json),
[portable test result](checks/task-tests-portable/result.json), and
[census summary](checks/lesson-census-release.summary.json). Exact commands and
additional smoke/period counts belong in `REVIEW.md` and `RESULTS.json`.
Earlier paths named `after-final`, `after-reviewed`, or `lesson-census-final`
are intermediate evidence, not proof for these bytes.

## Domain and construction

- **Check the selected rotation.** The baseline tested the unrotated bbox.
  Seed 0, indices 0–79 in each of three bands produced **54/240** inputs with
  an overflowing transformed insert: 7/80 easy, 21/80 medium, 26/80 hard.
  The authoritative outputs can paint onto/beyond a frame border; writes beyond
  the canvas are silently lost. The replacement selects a key and motif whose
  transformed dimensions fit. See the [baseline probe](checks/independent-review/baseline-probe.json).
- **Recognize the operational canonical domain.** Complete frames may use any
  color 1–9, and one surviving frame is valid. Keys are isolated monochrome
  singleton components in colors 1–4. Each frame needs one matching external
  insert, a pure same-color insert bbox, and one key. Complete frame rectangles
  must be disjoint. Unrelated multi-cell fragments and orphan key-color
  singletons may be ignored, as in the canonical damaged-frame examples. All
  four canonical inputs are retained as acceptance regressions. The authority's
  broader missing-key/default behavior is unchanged; the normal generator
  contract deliberately requires one key.
- **Construct feasible scenes directly.** Separated pockets replace capped
  placement retries and the fixed fallback. Impossible explicit combinations
  raise `ValueError` with their incompatible axes; requested dimensions/counts
  are never silently replaced. Frames are 4 or 5 cells on each side. Seven
  connected motifs, with 3–7 cells and initial rotations, provide informative
  orientations. Insert roles are cyclically reassigned among pockets in
  multi-frame scenes; frame colors, placement jitter, and whole-grid reflections
  vary the examples.

The task's [counterexamples](repo/generators/b4ecb537757c/counterexamples/) retain
three generated fit failures, hand-authored clipping and bbox-contamination
failures, and the nested-frame failure found during review. The nesting witness
was outside the pocket sampler but passed an intermediate validator; the final
disjoint-rectangle guard closes that domain hole without changing Racket.

## Defaults and compatibility

Only three exact axes remain:

| Axis | Accepted values | Default behavior |
| --- | --- | --- |
| `grid_h` | Integer 7–22 | 7 in compact scenes; varied feasible heights otherwise |
| `grid_w` | Integer 12–24 | 12 in compact scenes; varied feasible widths otherwise |
| `n_frames` | Integer 1–4 | 1 in compact scenes; 2–4 in ordinary varied scenes |

`None` leaves an axis unspecified. Booleans, coercions, out-of-range values,
unknown difficulty names, and unknown axes are rejected. The ineffective
`palette_kind`, `palette_size`, `n_distinct_colors`, `position_bias`, `density`,
and `texture` axes are retired, including their degenerate texture entry points.
Clients using those names must migrate instead of relying on ignored settings.
The version change also changes deterministic draws for old seed/index pairs.

Default residues 0–3 of each eight-draw period are one-frame **7×12, three-color**
scenes, restoring support for a measured canonical profile. Residues 4–7 provide
varied multi-frame scenes. Difficulty biases varied-scene heights; compact
scenes remain present in every band. This is a controlled mixture, not a claim
to reproduce every canonical layout or its frequency.

## Lesson design and the review reversal

The default lesson uses **seven demonstrations and one query**, spanning eight
consecutive draws. The first construction role cycles through keys 1–4 twice;
every single holdout leaves an asymmetric demonstration of each key. Explicit
overrides can change scene counts, so the default schedule argument must not
be transferred automatically to arbitrary override lessons.

An intermediate design assigned successive role keys consecutively. The actual
Racket-labelled lesson at easy seed **3**, indices **0–7**, with index **4** held
out admitted a rival that read the first frame's key and decremented it by
spatial rank. It fit the other seven pairs and changed the query answer, while
the older finite hook returned no reasons. The [frozen lesson](repo/generators/b4ecb537757c/workspace/cyclic_key_lesson.json)
and [authority receipt](checks/code-review/cyclic-key-racket.json) preserve this
failure against intermediate source
`eddeac72f504b2df823171ea9878497584d71a1b4d373e6291c489c1dc67952f`.

Other-role keys now vary independently except at residues 4 and 6. Those two
multi-frame anchors use opposite keys for two frames, or nonuniform repeated-key
tuples for three/four frames. Either anchor refutes uniform keys and both
spatial ±1 progressions; any single holdout leaves one anchor. The first role
retains its scheduled key. Seventeen declared rivals cover twelve individual
wrong key mappings plus frame-color lookup, uniform-first-key, rank matching,
and the two rank-derived key progressions. Frame-color lookup and descending
rank keys are declared canonical-fitting shortcuts; ascending rank keys are a
diagnostic competitor, not a canonical-fitting claim.

## Limits and rejected extensions

Retaining arbitrary random-walk motifs or unbounded packing would broaden
support but would require a separate construction/teaching argument. The present
sampler intentionally keeps fixed pockets, seven motifs, and bounded frame
sizes. It accepts canonical overwritten-frame fragments without generating new
ones. No extra symmetry, scaling, or unrestricted palette transformation is
claimed; key colors have fixed meanings.

The eight-period census enumerates starts at one fixed seed; it does not prove
all-seed behavior. Random samples and 17 rivals do not establish universal
identifiability. Production and rotated-query results must be reported
separately. These checks make no approval, admission, or measured Qwen training
improvement claim. Shared proposals F1/F2 are described in
[FEEDBACK_TO_CODEX.md](FEEDBACK_TO_CODEX.md).
