# Current working notes — 0eb4eaa46003

## Rule and domain

The canonical rule hash remains `bb6e25e7de93`. It finds monochromatic 4-connected components on zero background, orders them by their bounding-box top/left positions, and uses the first blue component's ordered row counts and first red component's ordered column counts. It selects the first other component matching both profiles, crops that component, and recolors occupied cells to fixed color 8. Canonical ties are governed by that rule; the generator validator deliberately requires exactly one blue anchor, one red anchor, and one joint candidate.

The three canonical pairs are accepted. Their target is color 4, first among candidates, third among all components, and an exact red copy. Their blue copies are not always the target. Thus the earlier retained exact-blue audit is evidence about old generated support, while copy-red and the declared canonical shortcuts really fit all three canonical pairs. The original selected source `f4b671a5803452cb71324aeb03fa529ca506afa04e022b3168f577ace69af1dc` made both anchors target copies, used easy unequal-size distractors, ignored advertised controls, and lacked a pinned rule hash.

## Construction and deliberate changes

The immutable catalog enumerates 1,494 normalized connected masks inside 4x3 or its transpose. There are 1,386 eligible central shapes of area 4..10: 4, 29, 152, 340, 421, 316, and 124 respectively. Each has at least two row-profile peers and two column-profile peers of the same bbox, plus an ordered-versus-unordered counterexample. Sampling and placement remain seeded through the shared generation context.

The first repair always made a central target with one row-only and one column-only candidate. Independent review reversed that choice: maximizing the sum of candidate row- and column-profile incidence ignored both anchors, fit all canonical pairs, and matched all 48 retained intermediate samples. The new even phase selects one of the two peripheral candidates instead. Its central decoy still has score 4; the selected peripheral has score 3. Either anchor can change the answer with candidate pixels fixed; retained three-state counterfactuals exercise this directly.

Odd indices retain the central target and refute the original thirteen rivals. Even indices refute candidate incidence and the combined rule 'copy a candidate matching either anchor; otherwise maximize incidence.' Each anchor is independently sampled with its required ordered profile and a mask different from the selected target. Other candidate copies remain possible. This excludes target-anchor exact copies from current generated support; they remain lawful and accepted in the canonical data and validator. The restriction supplies deterministic evidence against both shortcut families within the small lesson budget. It is a distribution restriction, not a claim that the reference rule forbids copies.

`LESSON_SCHEDULE_PERIOD=2`; the production contract is three consecutive demonstrations plus one query. Every four-position bundle contains two odd and two even draws, so every holdout leaves at least one of each. This only covers that assembly and the declared rivals; arbitrary independent resampling of three demonstrations has no such guarantee.

Two same-area, same-bbox distractors are always drawn. A third distractor, when requested, has different area. Dimensions, colors, anchor locations, candidate order, and eligible shape masks vary. Odd ordering places the near-matches before the target and avoids the canonical third-component shortcut. Even order and colors are free. Canonical-size/palette draws are favored but are not templates.

Exact observable controls are `grid_h` 10..24, `grid_w` 14..24, `shape_size` 4..10, `n_distract` 2..3, and `palette_size` 4..6 including zero. Every joint corner is constructive. Slots divide usable space after subtracting gutters; the earlier division-before-gutters implementation failed at width 14 and is retained as regression evidence. There is no partial-layout fallback. Inert texture/palette-kind/position-bias controls were removed; unknown controls and scalar coercions are rejected.

## Evidence and tools

`tests/test_profile_contract.py` has independent pixel-level checks for controls, canonical behavior, ambiguity, deterministic sampling, both teaching phases, and rotated lesson witnesses. `tests/test_evidence_tools.py` checks lossless recovery, corruption/conflict rejection, and dangling destination symlinks. `workspace/profile_probe.py` supplies an independent component/profile oracle and both standalone and dynamic rival checks. `workspace/reference_probe.py` runs the actual supported Racket authority on both seeded phases and on different crops with identical margins. `workspace/compact_evidence.py` losslessly compresses explicitly named evidence and retains a path/size/SHA restoration map.

The final source and exact check receipts are identified in the returned `REVIEW.md` and `RESULTS.json`. Keep previous failures: ignored overrides, minimum-width placement, scalar validation, the local-name lint warning, the incidence shortcut, a stale test-count assertion, the utility symlink issue, and environment-only missing-pytest/inode failures. Current rule labels were never changed to fit a Python prediction.

## Remaining limits and audit status

This is a finite 4x3/3x4 shape family with five or six separated components, rather than all lawful Racket grids. Exactly one pair of anchors/target is required by this generator's validator. Target copies, larger masks, multiple anchors, and rule-valid target ties are outside generated support. Fifteen finite rivals do not establish universal identifiability. Query answers in the two solve episodes remain withheld.

The imported unresolved audit is left intact; this source-bound repair and new receipts supply evidence for maintainer closure without modifying historical status. The two newly assigned audits are separate findings in the return and were not patched here.
## Current reviewer considerations

Source SHA-256: `06b1f9325bd19b2f304de919efb6076fdfc4e4117c2e89f6eab2ec007933c093`.

# Repair decisions — 0eb4eaa46003

## Authority and intended distinctions

The Racket rule and canonical ledger are unchanged. All new labels come from the supported authority; independent Python calculations are cross-checks or explicitly labeled diagnostic evidence. The selected generator's domain requires one blue anchor, one red anchor, and one jointly matching candidate, while the rule itself has a first-match policy for wider lawful inputs. The validator does not silently redefine that rule.

Three canonical pairs expose the task's row-count/column-count distinction, but also allow copy-red, first-candidate, fixed-color-4, third-component, and size-only selection. The old retained exact-blue audit is a useful generated-support lead, not a canonical-fitting hypothesis. The original author's rationale for always copying both anchors is unknown; simplicity is a hypothesis, not evidence.

## Geometry and distractors

Connected, normalized masks are enumerated in a finite 4x3 footprint and its transpose, with area 4..10. This keeps generation constructive at all advertised boundaries and produces 1,494 catalog masks rather than a handful of fixed templates. The central eligible bank contains 1,386 masks; peers share the relevant ordered count vector and bbox dimensions but differ on the other count vector. At least one near-match also has sorted-equal counts, exposing loss of ordering. Disconnected masks and output synthesis from margins alone were rejected because the rule selects an actual component and returns its actual arrangement.

A paired seven-cell fixture holds blue/red anchors and both margins fixed while changing the correct crop. Actual Racket outputs differ. This rules out accidentally turning the task into reconstructing an arbitrary binary matrix from its margins. It is a hand-authored lawful example, not a claim about a sampled seed.

Two main distractors share target area and bbox. A requested third has a different area, preserving an easier relation category without reducing requested object count. The old all-distractors-have-different-size design was rejected because it hid the need for both anchor profiles. A partial-placement fallback was removed: every exact corner fits five or six separated 4x4 slots, using gutters before division. The initial width-14 failure is retained and tested.

## Independent review reversed the first repaired construction

The first repaired source always selected the center of an L in row/column-profile space. It passed its then-declared thirteen rivals and full battery, but a new input-only candidate-incidence rival fit every canonical pair and all 48 retained independent samples. This was a real missing hypothesis, not an infrastructure failure. Successful intermediate reports retain source hash `486769c2da91dd5aaef35f478d6737ccbd7b0621b94429762db5127351a44ef6` and are not cited as final acceptance.

The final odd phase retains the center selection needed to defeat row-only and column-only selection together. The even phase lets the anchors select either peripheral candidate. It samples anchor geometry independently from matching-axis catalog entries, excluding the chosen target mask. This refutes both candidate-incidence maximization and the combined exact-anchor-copy/fallback rival. The same candidate pixels can have different correct answers when either anchor alone changes; retained actual Racket counterfactuals test both directions.

An alternative with only more unequal-size distractors would leave the incidence shortcut intact. Always making the new anchor a target copy would allow a combined copy/centrality heuristic. Increasing the minimum distractor count would break the documented two-distractor control. Arbitrary random target selection without deterministic phase coverage could leave a short lesson missing one necessary distinction. These alternatives were rejected.

The chosen restriction excludes target-anchor exact copies from default generated support. Other wrong-candidate copies are possible, and canonical exact target copies remain accepted by the validator. This is a transparent cost of the deterministic small lesson curriculum; it does not assert those lawful canonical cases are invalid. A future wider curriculum could restore target copies with an expanded lesson budget while retaining both counterexample kinds.

## Lesson policy and claims

`EXAMPLES_NEEDED=3`, `LESSON_SCHEDULE_PERIOD=2`. Use three consecutive demonstrations and the following query from the same seeded difficulty stream. Any four consecutive positions contain two odd and two even phases. Holding any one pair out leaves at least one of each phase, covering the original thirteen and the two new rivals. The guarantee refers to this ordered production assembly and rotations of those four labeled pairs; it does not cover three independently resampled demonstrations.

Fifteen unique rivals appear in both semantic and lesson namespaces; thirteen actually fit all canonical pairs. Distinct namespace aliases are not counted as new hypotheses. The final battery requires rotations and enumerates both declared schedule starts at seed 0 across all three bands. A separate 100-lessons-per-band census covers 300 lessons and 1,200 inputs/rotations. Independent Python tests also examine overlapping windows. Finite declared-rival results do not establish universal induction, distribution-wide proof over every seed, or downstream learning performance.

## Exact controls, placement, and colors

All five controls are exact and measured from pixels: grid height 10..24, width 14..24, target area 4..10, distractors 2..3, and palette size 4..6 including zero. All 32 joint boundary combinations are exercised independently. `None` retains defaults; booleans, strings, floats and out-of-range values are rejected. Seed must be an integer, sample index a nonnegative integer, and difficulty one of the documented values. Removed inert `texture`, `palette_kind`, and `position_bias` keys now raise errors instead of pretending to work.

The core mixture favors canonical dimensions 11/12 by 20/21/22, palette 0/1/2/4/6/7, and familiar areas, while broader draws exercise every advertised value. Colors 1 and 2 retain their semantic roles and output 8 remains fixed. Odd candidate colors/order defeat fixed-4, minimum-color, first-candidate and third-component rules; even placement and color order vary freely. Legal minimum palettes can reuse a color on separated components. The grammar depends on connectivity rather than treating a whole color as a single object.

## Reusable evidence and runtime choices

The pixel probe, actual-authority probe, profile tests, reversible evidence compressor, and its file-safety regressions are task-local and included in the delta. The compressor preserves original path, size and SHA-256 before removing an oversized source report; the 36 MB baseline override failure is retained losslessly as gzip plus restoration map. A review caught dangling output symlinks; real filesystem regressions failed before the fix and passed afterward.

The isolated test preflight initially lacked pytest under `PYTHONNOUSERSITE=1`. A task-local environment using already installed pure-Python dependencies resolved it without network installation or shared-source edits. A later staging attempt exhausted the overlay filesystem's available inodes. Setting a task-scoped `TMPDIR` on the available temporary filesystem resolved staging while preserving isolation. Both failures remain recorded as environment failures. Neither is counted as a failing rule or passing test suite. Installed environments and runtime copies are omitted from the return.

## Scope and open work

The generator is limited to the finite small-mask family, five/six separated components, one anchor pair, one joint target, and the stated controls. It does not cover all Racket-lawful grids or every plausible rule. The original unresolved audit record is preserved for explicit maintainer closure using this new source-bound evidence. Separate assigned audits reproduce a missing equal-color transpose relation and confirm a color-sorting teaching shortcut; neither audited source was modified. Hidden query correctness for both solve records remains unknown.

## 2026-10-24 native parametric profile-source family

The separate native adapter under `workspace/parametric/` preserves the exact canonical Racket bytes as the default `profile_sources=blue_rows_red_cols` setting. Its nearby alternative, `red_rows_blue_cols`, swaps which colored anchor supplies the ordered row and column profiles. Both settings receive byte-identical input scenes; only the executed rule changes. Each scene contains both cross-composed target shapes plus same-area/same-bounding-box distractors, so the answer cannot be recovered from area, color rank, target position, unordered margins, or a fixed candidate index.

The family supports 2–6 demonstrations and 1–4 independent prefix-stable queries. Every visible demonstration distinguishes the two settings. The four retained queries are distinct, and the fourth is a substantive 30×30 construction with 288 occupied cells and content touching all four boundaries rather than padded small geometry. A 1,024-episode corner sweep (256 seeds × two settings × four count corners) generated 6,656 labeled pairs with no failures; all 512 maximum-size queries met the stated 30×30 density and boundary checks.

The required sequential dependency is: **A**, identify the blue and red anchors and derive the episode-selected ordered row/column profile pair; **intermediate**, that input-dependent pair of ordered count vectors; **B**, scan non-anchor components in reading order, select the first component matching both vectors, then crop and recolor it. B cannot choose a component before A determines the vectors. The native protected-Racket witness at `WORK/checks/0eb4eaa46003/causal/witness.json` holds the input fixed and replaces the canonical intermediate with the swapped-source intermediate; its replay confirms that the final output changes. The retained diagnostic beside it records the corresponding target-component change.

Native qualification executed both settings at seeds 0 and 17 through protected Racket and retained four queries per job. The task-local manifest binds the adapter, prototype, canonical source, promotion contract, tests, README, and current evidence. This is reviewer-ready source/evidence only: owner integration must rerun qualification and fresh acceptance on the exact integrated bytes, and no training admission is claimed.
