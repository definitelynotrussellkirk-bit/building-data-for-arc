# Working notes: 0fcb77c31d06

## Current rule and authority

`RULE_HASH = c515fc7de0cf` is pinned to the unchanged canonical Racket authority.
Row 0 is a sparse frequency legend: ignore zero and choose the unique most
frequent color. In rows 1 onward, split that color into 4-connected components,
select its unique largest component, crop its bounding box from the input, and
upscale the crop by a factor of two. The Python `oracle_output` is a diagnostic
mirror; Racket remains authoritative.

Final selected generator SHA-256: `6f886ddc07655663270b14e8eb3c76b7b6000852664c3274906b246938ecfc93`
(version `3.0.0`). The selected baseline was
`8ef3c7b6902bf2e13130765793456fa1243dba013dea310843edb3e178f2be04`
(version `2.2.0`). No earlier return was used as repair authority; the retained
associated-notes file was empty and there was no selected-task review index.

## Baseline defects and reversals

The baseline declared eight axes, but only height and width were useful exact
controls. Several string axes were aliases or singletons, the three degenerate
textures intentionally violated the rule domain, scalar controls accepted
coercions, and difficulty-specific ranges contradicted the advertised domains.
The baseline also omitted `RULE_HASH`, had no executable semantic contract, and
could not reach the canonical four-foreground-color palette profile. Its
optional placement of a second key-color object meant some lawful outputs never
required the “largest component” step.

The more important teaching defect was structural. In every labeled canonical
pair, the legend winner is the leftmost nonzero legend color and the body has
only one component in that color. Thus three plausible wrong rules fit all
canonical labels:

1. choose the leftmost legend color;
2. choose the top-left/only object of the frequency-winning color;
3. crop the bounding box of all key-colored cells instead of the largest
   connected component.

The old choice was broad nominal configurability plus optional random controls.
The replacement deliberately narrows the public surface and makes the missing
semantic distinctions mandatory in every generated input.

## Current generation contract

Only `grid_h` (`9|10|11|12`) and `grid_w` (`10|11|12|13|14`) are public axes.
Both are strict integers, observable exactly, and supported in every difficulty
band. Unknown controls, booleans, floats, strings, negative sample indexes, and
unknown difficulty names fail closed.

Every generated lesson input has:

- a blank separator row;
- three or four nonzero legend colors with a unique winner;
- a non-key color in the leftmost legend position;
- exactly two separated key-color objects, with the smaller one earlier in
  reading order;
- a unique larger key-color object whose crop visibly contains background;
- a still larger non-key distractor, forcing use of the legend before size;
- a second non-key distractor color.

`strict_canonical_like` describes the shared canonical/generated manifold and
therefore accepts all imported canonical inputs. `teaching_check` adds the
anti-shortcut requirements above for production generation only. This split is
intentional: the first implementation incorrectly put teaching-only witnesses
inside `strict_canonical_like`, and the semantic gate correctly rejected that
because it disowned 5/5 canonical inputs.

The declared semantic rivals are leftmost-legend/top-left-object,
frequency/top-left-object, frequency/all-key-pixels bbox, and largest body object
without using the legend. All three canonical shortcuts are verified against
all labeled canonical pairs; every generated input refutes all four rivals.
`EXAMPLES_NEEDED = 3`. A source-bound census materialized 300 lessons (100 per
band), 1,200 unique pairs, and all 1,200 query rotations: zero declared-rival
ambiguities, materialization errors, hook warnings, or scoring errors.

## Verification and retained evidence

- Initial task-test red: `checks/task-tests-red/` (13 expected failures against
  the baseline contract additions).
- Semantic regression red/green: `checks/task-tests-semantic-red/` and
  `checks/task-tests-semantic-green/`.
- Final task tests: `checks/task-tests-final-14/` (14 passed; rerun after final
  packaging replay is also recorded in `RESULTS.json`).
- Final twelve-stage battery: `checks/after-final/`.
- Large lesson census: `checks/lesson-census-final.json`.
- Exposed post-repair solve: `solve/`; revision 1 passed 3/3 visible examples,
  with earlier rule exposure declared and no reference consulted during solve.

## Known limits and open findings

The semantic result is finite evidence against four named rivals, not a proof of
unique induction against every possible program. Generated legends intentionally
avoid frequency ties, key objects avoid equal-area ties, shapes come from a small
polyomino family of areas 3 through 7, and canvases are limited to 9..12 by
10..14. Those choices keep lessons unambiguous and canonical-adjacent but do not
exercise tie-breaking or arbitrary geometry. No remaining blocking finding is
known for the selected generator; the Racket authority was not changed.
## Current reviewer considerations

Source SHA-256: `6f886ddc07655663270b14e8eb3c76b7b6000852664c3274906b246938ecfc93`.

# Decisions for 0fcb77c31d06

## D1 — Keep the Racket authority unchanged

- **Prior state:** The selected Racket rule already matched all canonical
  labels; the Python generator simply failed to pin its hash.
- **Decision:** Add `RULE_HASH = "c515fc7de0cf"` and keep the authority bytes
  unchanged.
- **Alternatives considered:** Rewrite the rule to match the baseline's looser
  generation grammar or add special handling for degenerate legend cases.
- **Probe/evidence:** Rule smoke, Racket lint, authority sync, and all canonical
  oracle comparisons pass in `checks/after-final/`.
- **Failure mode avoided:** A generator repair silently drifting from the
  selected canonical program.

## D2 — Replace eight nominal axes with two exact observable axes

- **Prior choice:** `grid_h`, `grid_w`, `palette_kind`, `palette_size`,
  `position_bias`, `n_distinct_colors`, `density`, and `texture`; several were
  singletons, aliases, ignored, or intentionally invalid.
- **Decision:** Publicly expose only `grid_h=9..12` and `grid_w=10..14` as strict
  integer controls, with every value legal in every band.
- **Alternatives considered:** Preserve dead names for compatibility, or declare
  a large incompatibility table for band-specific ranges.
- **Why rejected:** A smaller truthful API is more useful than controls that do
  not change an observable or that leave the rule domain. There was no retained
  consumer requiring the old aliases.
- **Probe/evidence:** The final override gate passes; task tests exhaust all 60
  band/height/width combinations and verify exact observation.
- **Known limit:** Palette and geometry choices are intentionally sampled rather
  than externally controlled.

## D3 — Make anti-shortcut structure mandatory per input

- **Prior choice:** A second key-color object was optional and distractor sizes
  did not force use of the legend.
- **Decision:** Every generated grid has a smaller earlier key object, a unique
  larger key object, and a still larger non-key object. The legend winner is
  never the leftmost nonzero legend color.
- **Alternatives considered:** Rely on aggregate random frequency, or schedule
  one special counterexample among otherwise canonical-like pairs.
- **Why rejected:** Aggregate coverage can still produce a three-demo lesson in
  which a shortcut survives. Per-input witnesses make every ordering and query
  rotation safe against the declared rivals.
- **Probe/evidence:** All four semantic witnesses fire in 600/600 semantic-gate
  samples; the 300-lesson census reports 0/300 production ambiguities and
  0/1,200 rotated-query ambiguities.
- **Failure mode avoided:** Correct labels that do not teach counting, connected
  components, or largest-within-key selection.

## D4 — Restore canonical palette reach without copying canonical position bias

- **Prior choice:** Exactly three foreground colors, so total palette support
  was fixed at four including background; canonical data reaches five.
- **Decision:** Alternate three- and four-foreground-color legends. Choose the
  key from an interior palette position, then explicitly place a non-key color
  leftmost.
- **Alternatives considered:** Always use four colors, or exactly reproduce the
  canonical legend layouts.
- **Why rejected:** Alternation preserves smaller examples while reaching the
  missing canonical profile; copying canonical layouts would preserve the very
  positional shortcut under repair.
- **Probe/evidence:** Final distribution and profile-floor gates pass; task tests
  observe both legend palette sizes.

## D5 — Use bounded backtracking over compact polyomino templates

- **Decision:** Areas 3 through 7 use rotated/reflected nonrectangular templates;
  a bounded backtracker keeps component bounding boxes separated by a one-cell
  halo and satisfies the reading-order constraints on every legal canvas.
- **Alternatives considered:** Continue stochastic growth/placement retries, or
  use fixed coordinates.
- **Why selected:** Backtracking makes the full exact override domain reliable;
  orientation and placement still vary deterministically by seed.
- **Probe/evidence:** Override, diversity, grammar, and 14 task tests pass. The
  selected crop always contains visible background before scaling.
- **Known limit:** This is a small shape family, not arbitrary polyomino support.

## D6 — Separate canonical validity from teaching strength

- **Initial repair mistake:** `strict_canonical_like` included anti-shortcut
  conditions that the public canonical examples do not satisfy.
- **Observed failure:** The semantic gate rejected 5/5 canonical inputs while
  separately confirming all generated witnesses.
- **Reversal:** `strict_canonical_like` now accepts the shared
  canonical/generated task manifold. New `teaching_check` enforces the stronger
  production-only contract and is called by `generate`.
- **Probe/evidence:** The failing run is retained at
  `checks/semantic-gate-after/`; the red/green tests are under
  `checks/task-tests-semantic-red/` and
  `checks/task-tests-semantic-green/`; the final semantic gate passes.
- **Failure mode avoided:** A strict predicate that claims to describe the task
  while disowning its authority examples.

## D7 — Use three demonstrations and support arbitrary query rotation

- **Decision:** Declare `EXAMPLES_NEEDED = 3`. Each individual pair refutes all
  declared rivals, so production order is not semantically privileged.
- **Policy tested:** 100 independently materialized lessons per band; each of
  the four pairs in every lesson was held out once as query.
- **Result:** 300/300 production lessons and 1,200/1,200 rotations had no named
  ambiguity; all 1,200 inputs were unique.
- **Evidence:** `checks/lesson-census-final.json`.
- **Known limit:** This is finite coverage against four executable rivals, not a
  proof against every possible hypothesis.

## D8 — Retain a Racket-checked exact counterexample

- **Decision:** Save seed 4242 / sample 0 / medium / 10x12 at
  `repo/generators/0fcb77c31d06/counterexamples/canonical-shortcuts.json`.
- **Reason:** It lets future reviewers replay the strongest canonical shortcuts
  without reconstructing the analysis.
- **Evidence:** `checks/selected-counterexample/racket.json`; the focused task
  test verifies the source hash, checks, Racket output, Python mirror, and every
  declared rival output.

## D9 — Preserve solve provenance

- **Decision:** The post-repair solve is explicitly marked exposed because the
  rule had already been read. No generator, Racket source, private labels, or
  reference solution was reopened during that solve.
- **Result:** Revision 1 passed 3/3 visible examples and was frozen with the same
  generator hash.
- **Evidence:** `solve/summary.json` and `solve/FINISHED_NOTES.md`.
