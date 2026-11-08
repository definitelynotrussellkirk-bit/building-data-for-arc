# Working notes: d377a54f20c6 — version 3.1.0

## Rule and authority

The original family is training:8cb8642d. Each zero-separated, filled two-color rectangle becomes a frame in its local majority color, with an edge-distance X and centered extension in its local minority color. The canonical normalized Racket hash remains `108312a76f48`; no executable rule was changed. The two selected base JSON `target_code` fields were synchronized to the exact canonical source. Archival `raw_code` was preserved byte for byte.

The input domain remains one to three rectangular components, two nonzero colors per component, a unique majority, dimensions at least five, literal zero background and maximum canvas size 30×30. Minority positions and counts do not determine the drawn stroke. Exact public inputs remain accepted. Explicit `scene_profile` controls retain their original behavior.

## Reproduced failure and repair

Baseline source `1cb8e82e451add585fa1e755b0817acf0a4fb8d887b65fd0d0258313596398d2`, seed 1, medium band, indices 0,1,2,3 gives three demonstrations consistent with a singleton-only marker rule, followed by a query requiring multiple markers to be treated identically. `counterexamples/singleton-marker-lesson.json` contains the exact four Racket-labeled pairs and the differing rival result. The singleton rival also fits all eight usable canonical pair occurrences. Correct per-grid labels alone therefore do not make that old lesson teach the intended rule.

The default sampler now alternates a rich scene at every even index with an odd-index scene. Each rich scene has two objects, multiple minority pixels, an aspect-ratio distinction, and overlapping local color roles. It refutes all four declared rivals: singleton-only markers, diagonals without center extension, first object only, and global color roles. In the period of eight positions, four are rich, one is an exact public anchor, and three draw from all twelve general profiles. Three consecutive demonstrations contain a rich scene; four consecutive pairs contain two, so moving any one pair to the query still leaves a rich demonstration. This structural argument concerns consecutive accepted draws; the official materialization and rotation receipts separately check the actual lesson assembly.

`EXAMPLES_NEEDED=3` and `LESSON_SCHEDULE_PERIOD=8` describe this default curriculum. `lesson_identifiable` uses demonstration labels and query input only; it deliberately ignores a supplied query output. Named witness predicates are checked against their declared rival, and `CANONICAL_SHORTCUTS` contains only the rival actually fitting every canonical pair. These are finite, executable hypotheses, not a uniqueness proof over all possible rules.

Strict type checks now reject boolean, floating-point, and string seed/index values, and negative sample indices, before constructing the RNG context. Negative integer seeds remain legal. The existing task tests now use the supported selected-source and canonical-data helpers instead of private import aliases or fixed directory depth.

## Distribution choices and remaining limits

The rich scene deliberately bundles four teaching distinctions so a three-demo lesson and every tested query rotation remain informative. This increases two-object/cross-role/multiple-marker examples; it does not claim to preserve the old distribution. The other slots retain square, tall, wide, border-marker, shared-color, multiple-object, and parity cases. Exact public anchors are retained at one eighth of default indices for the existing canonical-profile floor. Their duplicates must not be counted as novel training contributions. Medium and hard rich geometry share a dimension family; no new human difficulty calibration is claimed.

Reversal criterion: if source-bound export measurements show excessive duplicate yield or a new canonical-fitting rival, revise the schedule and add a discriminating witness, then rerun the strict semantic, profile, override, rotation, and four-query gates. Do not raise volume or silently relax a gate to hide ambiguity.

## Proposed original-family extension

`workspace/parametric/` contains a runnable, separately labeled prototype with two semantic parameters: center extension on/off and stroke width 1/2. The canonical default is extension on, width 1, with an exact copy of the original Racket program. Four instantiated Racket programs label their own episodes. The default is three demonstrations and four distinct queries; demonstrations identify the intended setting among the four declared settings. Public challenge identities depend only on visible contents; parameters, reference source and query answers remain private. No variant is registered or approved for training by this review.

The reusable `workspace/check_four_queries.py` validates an actual production export's pair counts, distinct query inputs, reference labels and demonstration-only rival identifiability. It reports bounded evidence and fails closed on errors. Final measurements and exact commands are retained in the return's `RESULTS.json`, `REVIEW.md`, and `checks/`.

Imported associated notes retain original evidence/timestamps in `evidence/associated_notes.jsonl`. Historical evidence is preserved; this note does not grant approval to changed source bytes.

## Native parametric build — review-36b6144606a947ef

Built the current native `workspace/parametric/adapter.py` contract with
episode-fixed `finish` values `redraw_only` and
`highlight_most_stroke_cells`. The default returns the exact selected canonical
Racket source. The alternate first performs the complete canonical rectangle
redraw, derives each original object's count of produced local-minority stroke
cells, selects the unique maximum, and recolors that complete produced stroke
to 9. Inputs are matched across settings; 2–6 demonstrations and four privately
shuffled sequential queries are supported, including a boundary-spanning 30x30
case.

The finite authoring audit covered 18 jobs (seeds 0, 17, 97; demos 2, 3, 6;
both settings), 138 pairs, 15 declared rivals, and 330 explicit proxy-separation
checks with no wrong-rule survivor. Native qualification passed four jobs and 40
protected-Racket evaluations. The protected causal witness replaces the
post-redraw stroke-count intermediate with original input-marker multiplicity:
stroke counts select object 1, marker counts select object 0, and the final grids
differ. Public preview verification passed 16 independent one-query views. The
portable final task stage passed 63 tests and 2 subtests.

These are bounded reviewer results. Exact-source owner acceptance remains
pending and `training_admitted` remains false.
