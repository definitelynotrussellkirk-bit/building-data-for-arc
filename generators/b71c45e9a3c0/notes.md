# Working notes: b71c45e9a3c0

Final review version: 2.1.0, generator SHA-256
`e10b490a09aa7a4a03b4bdcefde83bf325727a40db77098fd6e85d1b909bcd9a`.

The imported 1.2.1 source had dishonest/dead axes, capped placement that could
silently drop requested groups, no semantic contract, and no shapes with an
empty bbox top-left corner. The selected repair uses six exact observable axes,
constructive separated quadrants with randomized margins, 1–2 gap shapes in
every input, and declared rivals for top-row anchoring and global-key reuse.

The intermediate 2.0.0 source pinned every group to an outer corner. A new
regression caught that restriction; 2.1.0 jitters origins within each quadrant.
The prior source-bound exposed solve is retained under `checks/prior-solve/`.

See root `REVIEW.md`, `DECISIONS.md`, and the independent probes in `workspace/`.
## Current reviewer considerations

Source SHA-256: `e10b490a09aa7a4a03b4bdcefde83bf325727a40db77098fd6e85d1b909bcd9a`.

# Design decisions for `b71c45e9a3c0`

## Decision context

The original associated-notes file was empty, so original intent beyond comments/source is unknown. Where an “original rationale” is mentioned below, it is an inference from the imported 1.2.1 code rather than a prior author's recorded decision.

The canonical transformation was already coherent and synchronized: for each 4-connected color-3 object, read the cell at `(bbox_top - 1, bbox_left)` and recolor the object to that color. I changed the sampler and executable teaching contract, not the Racket authority.

## D1 — Keep the authority unchanged and pin it

- **Choice:** `RULE_HASH = "0668839edbcc"`; no canonical, archival, or selected Racket source changed.
- **Original rationale:** the 1.2.1 comments already described the corrected bbox-left key position, but the source did not pin the authority.
- **Probe:** authority sync, 120-call rule smoke, and independent canonical oracle parity.
- **Rejected alternative:** rewriting the rule to match the baseline generator's narrower examples. That would preserve shortcuts rather than improve training data.
- **Limitation:** generator approval remains a maintainer/catalog decision; a synchronized rule is not itself training approval.

## D2 — Replace nine misleading axes with six exact observable axes

Final axes:

| Axis | Domain | Default policy | Reason |
|---|---|---|---|
| `grid_h` | integer 9–14 | weighted toward 11 | Includes canonical height while retaining size variation. |
| `grid_w` | integer 9–14 | weighted toward 10/11/12, with band anchor | Covers all canonical widths and exposes exact overrides. |
| `n_groups` | integer 2–4 | strongly weighted to 3 | Matches canonical color-count profile while retaining object-count variation. |
| `n_gap_shapes` | integer 1–2 | hard favors 2, otherwise 1 | Guarantees bbox-anchor counterexamples rather than hoping they occur. |
| `palette_kind` | `low|high|mixed` | weighted to mixed | Produces an observable palette partition while always using distinct object keys. |
| `shape_profile` | `compact|extended|mixed` | weighted to mixed | Changes realized bbox heights, so the control is visible in pixels. |

- **Original rationale:** inferred goals were broad variation and negative fixtures, but `palette_size`, `n_distinct_colors`, `position_bias`, `density`, and `texture` were either ignored, redundant, single-valued, or mixed unlawful degenerates into the normal domain.
- **Implementation:** strict unknown/type/range checking, `gen_ctx` exact draws, and `observe_overrides` reconstructed from returned pixels.
- **Probe:** 239 override cases × 30 seeds × 3 bands = 21,510 accepted draws with zero findings; task tests independently recover every axis.
- **Rejected alternatives:** aliases that cannot be separately observed; “helpful texture” values that are byte-identical; unlawful `no_keys`, `key_below_shape`, and `multiple_keys_per_shape` values in the ordinary training domain.
- **Limitation:** palette classes are task-local buckets, not a claim that color magnitude has semantic meaning.

## D3 — Construct placement instead of retrying

- **Choice:** sample up to one group in each north/south × west/east quadrant, reserving a central row and column. Within each quadrant, independently jitter the key row and bbox-left column over every fitting origin.
- **Original rationale:** random rejection placement sought spatial variety and group separation, but a 60-attempt cap could exit without placing a requested group.
- **Why this construction:** it guarantees every declared product, including four extended groups on 9×9, while allowing both margins to vary on larger grids. No successful draw depends on a retry budget.
- **Probe:** 96 seeds per band at the 9×9/four-group boundary, exact observed group counts, plus the 512-sample layout report.
- **Rejected alternative 1:** raise the retry cap. It changes failure probability but does not eliminate silent shortfall.
- **Rejected alternative 2:** fixed corner origins. This was implemented briefly in version 2.0, then rejected when the anti-corner regression failed.
- **Rejected alternative 3:** unconstrained backtracking over all coordinates. It can provide broader layouts, but the current local rule does not need that complexity and the quadrant construction has an obvious fit invariant.
- **Limitation:** the central separator is visible and the generator does not cover every validator-lawful layout. This is documented rather than hidden.

## D4 — Make bbox-left anchoring observable

- **Choice:** split connected shape templates into compact/extended and occupied/gap pools. Every generated input contains exactly one or two gap shapes whose normalized bbox cell `(0,0)` is empty while bbox-left remains defined by a lower row.
- **Original rationale:** all imported shapes contained `(0,0)`, likely for simple key placement. That accidentally made bbox-left identical to “leftmost occupied cell in the top row.”
- **Probe:** witness `empty_bbox_corner` fires 600/600 times and its linked rival `above_topmost_occupied` disagrees 60/60 checked times. The independent probe disagrees 128/128 times in each of four bands.
- **Rejected alternative:** merely describe bbox-left in `SUMMARY`. Text metadata does not teach a pixel-only model.
- **Failure mode guarded:** a model can no longer score perfectly by locating the top-row occupied cell and looking above it.
- **Limitation:** the finite shape pools do not enumerate all connected 3–5-cell polyominoes.

## D5 — Use distinct per-object keys and teach that choice

- **Choice:** all key colors are distinct within an input; mixed palettes contain at least one low and one high key.
- **Reason:** it makes per-object association observable and refutes a “use one global key color” rule.
- **Probe:** `multiple_key_colors` fires 600/600 and `one_key_for_all` is refuted 60/60; independent disagreement is 128/128 per band.
- **Rejected alternative:** repeated key colors as a normal axis. Repetition is lawful but weakens the diagnostic value of small lessons; it can be added later as a separate, explicitly balanced curriculum phase.
- **Limitation:** the current training sampler does not teach repeated keys, though the Racket transformation itself would handle them.

## D6 — Anchor defaults near canonical profiles without shrinking override support

- **Choice:** weighted choices favor height 11, width 10–12, and three groups; all values 9–14 and 2–4 remain reachable and exactly overridable.
- **Original rationale:** difficulty bands previously separated small easy from large hard grids, but easy had zero canonical-profile support in the retained 20-draw check.
- **Probe:** profile floor improved from 6/60 exact with easy 0/20 to 47/60 exact with easy 15/20, medium 16/20, hard 16/20.
- **Rejected alternative:** force only canonical dimensions. That would maximize profile score by discarding useful size diversity.
- **Limitation:** difficulty now changes weighting rather than defining disjoint manifolds; geometry/semantic hardness remains modest.

## D7 — Require a three-demo semantic lesson contract

- **Choice:** `EXAMPLES_NEEDED = 3`; each materialized lesson has three demos and one query. `lesson_identifiable` requires a bbox-gap witness and multiple key colors in the demos. Two executable rivals are declared and independently reimplemented in tests.
- **Reason:** individually correct labels do not guarantee that demonstrations distinguish the intended program from plausible alternatives.
- **Probe:** strict semantic gate checks 12/12 lessons and all 48 query rotations; the larger census checks 300 lessons, 1,200 pairs, and 1,200 rotations with no declared-rival ambiguity or errors.
- **Rejected alternative:** rely on witness frequency pooled over independent grids. A frequent witness can still be absent from a particular lesson or from a specific curriculum slice.
- **Limitation:** two rivals are not an exhaustive hypothesis space. This is evidence of targeted separability, not a proof of unique induction.

## D8 — Keep validation broader than generation

- **Choice:** `self_check` validates rectangular ARC grids with 2–4 connected color-3 objects, valid 2–3-cell bbox dimensions, 3–5 cells, one exact key per object, and distinct key colors. It does not require quadrant placement, a central separator, or a gap shape.
- **Reason:** canonical examples and external lawful probes should not be rejected merely because the production sampler uses a narrower constructive strategy.
- **Probe:** all four canonical inputs pass; malformed grids return diagnostics instead of raising.
- **Rejected alternative:** validate only what `generate` emits. That hides distribution restrictions and makes lawful adversarial testing impossible.
- **Limitation:** distinct keys are still a validator restriction chosen for this curriculum, not inherent to the Racket program.

## D9 — Independent authoring tools and tests

- **Choice:** `workspace/reference_probe.py` implements components, bbox oracle, rivals, and observed axes without calling production helpers. `workspace/layout_probe.py` measures interior placement coverage. Task tests use those independent functions.
- **Reason:** tests that call the same helper as production can pass with a shared bug.
- **Probe:** portable task runtime passes 49/49 and records copied source hashes.
- **Limitation:** independence is implementation-level, not formal verification; both are still Python programs written from the same task understanding.

<!-- arcpuzzles-trainer-ambiguity:start -->
## Current trainer ambiguity follow-up

Claude supplied 1 exact canonical lesson(s) with a proposed alternative rule. Retained privately with source hashes and all stored queries: `evidence/trainer-ambiguity-current/current.json`. These are **open describer flags**, not confirmed wrong labels or failed current parametric qualifications. Check whether the proposed rival fits every demonstration and changes any stored query; distinguish source revisions before repairing. Approval and training state are unchanged.
<!-- arcpuzzles-trainer-ambiguity:end -->

## 2026-10-25 native parametric review

Built a task-local episode-fixed `scope=all_objects|largest_key_size` family
under `workspace/parametric/` without changing the approved production generator.
The default program is the exact canonical Racket source. The relay variant finds
the unique largest color-3 object, reads the key above its bounding-box top-left
corner as a target occupied-cell count, then recolors only the unique object of
that size using its own bounding-box key.

The family supports 2–6 demonstrations and four distinct matched-input queries,
including a substantive 30×30 boundary-spanning case. A finite audit covers both
settings, seeds 0/17/97, and demo counts 2/3/6; all six declared shortcuts are
rejected and 147 labels match protected Racket. Native qualification passes four
jobs and 40 protected-Racket evaluations. The retained wrong-intermediate witness
uses the largest object's size instead of its key-derived target and changes 16
final cells. Status is reviewer-ready with exact-source owner acceptance pending;
no training admission is claimed.
