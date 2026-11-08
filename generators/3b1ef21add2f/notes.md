# Working notes: 3b1ef21add2f

## Intended rule and authority

For every complete 2×2 window of red (2) in the **original** input, recolor its
four cells green (3). Take the union of all such windows simultaneously. Preserve
every other cell, including red cells attached to a window, hollow red rings,
and squares of other colors. Four-connected components are useful diagnostics,
not the unit selected by this rule. Overlapping windows must not be discovered
by scanning an already recolored grid.

Version 3.0.0 declares `RULE_HASH = 200a2c36d86e`. The selected Racket authority
and canonical ledger are unchanged. Python rivals and the independent test
oracle are authoring diagnostics; exported labels still come from Racket.

## Repair and contract

Version 2.0.1 defaulted to isolated red squares without the promised unchanged
red distractors. It admitted all-red→green on every default draw, although that
shortcut fails all three canonical pairs. Canonical-fitting rivals also went
unchallenged. Placement retries could underfill requests; many advertised axes
were ignored, fixed, coercive, or bypassed by fixed-size textures.

Version 3.0.0 exposes only exact integer `grid_h` and `grid_w` (7..16) and
`n_windows` (0..8). The last counts **all** complete red 2×2 neighborhoods,
including overlaps, rather than components or placement attempts. Every joint
combination is constructible. Known-axis `None` means omission. Booleans,
floats, strings, out-of-range values, and every unknown/obsolete axis raise.
This deliberately breaks the old ineffective controls; it is a major version
change. `observe_overrides` measures the three quantities from pixels.

The sampler uses a translated, rotated, optionally reflected 7×7 motif inside
the requested canvas. Simple draws have isolated squares and an unchanged red
L. Rich draws have overlapping windows with an attached tail, a separate
square, a hollow red ring (optionally with a tail), and a nonred 2×2 square.
The ring has no red window and stays red. Nonred square colors are chosen from
1 and 4..9; color 3 is excluded there because recoloring it to 3 would not
distinguish the any-color rival.

## Three distinct domains

1. The rule acts on rectangular digit grids. `rule_grid_errors` checks the
   bounded ARC format (1..30 per dimension; exact integers 0..9).
2. `self_check` selects a contrastful **input teaching grammar**: zero and red
   are present; at least two four-connected red components exist; if any red
   window exists, at least one red cell remains outside all windows. It accepts
   all three canonical inputs. Explicit zero-window draws are lawful no-ops.
   Rejected blank, single-component, or all-recolored grids are outside this
   chosen teaching grammar, not evidence of an undefined Racket rule.
3. Actual sampler support is narrower still: dimensions 7..16, at most eight
   windows, a bounded motif layout, and the stated palette/shape families.
   The validator is not a claim that every accepted grid is emitted or that
   any one input makes a lesson identifiable.

`strict_canonical_like` separately measures the small canonical envelope:
7..8 dimensions, palette {0,2}, one or two windows in isolated 2×2 components,
plus unchanged red cells. Rich extensions need not satisfy this predicate.

## Lesson policy and decision reversals

Use three demonstrations and one query from consecutive accepted draws.
`LESSON_SCHEDULE_PERIOD = 3`: residue 0 is a two-color simple anchor; residues
1 and 2 are rich contrasts. Every four consecutive draws contain an anchor
and at least two rich scenes. Holding out any one draw leaves a rich scene.
This is a finite declared-rival guarantee, not a universal identifiability proof.

The first repaired candidate used period 4 with one anchor and three rich
scenes. Its profile check found only 13/60 draws in the canonical envelope,
below the required 25% floor. The new one-in-three rate gives more canonical
support while retaining a rich demonstration after every query rotation.
The old passing lesson census and this failed battery are retained in the
return as intermediate evidence, not reported as final-source results.

The first rich motif used a red tetromino without a window. Independent review
found that **iteratively remove red cells of degree <2, then recolor the rest**
fit all 2,344 checked first-candidate motif variants and every canonical pair.
A hollow ring exposes this graph-2-core shortcut. Rich tetrominoes were replaced
with rings, the rival was declared, and independently authored tests first
captured the failing behavior before the repair. The exact ring witness and
Racket receipt are retained in `checks/code-review/` in the review return.

## Verification and limitations

The task-local suite has 125 cases and 18 unique test functions. It covers all
3,600 joint height/width/window choices across None/easy/medium/hard, malformed
values, deterministic replay, input immutability, all canonical labels, actual
Racket spotchecks, lesson residues, and independent 2-core disagreement.
`workspace/probe_local_windows.py` separately executes Racket on all 512 binary
3×3 masks padded to 5×5, 14 targeted cases, and three canonical inputs. It
discovers the generator's actual rival declarations and reports validator
acceptance separately from operator correctness. See the return's `REVIEW.md`
and source-bound `checks/` receipts for final counts and lesson censuses.

Six plausible canonical-fitting rivals are declared: exact square components,
component mass ≥4, a greedy in-place scan, largest window-bearing components
including ties, any nonzero color's squares, and the red graph's 2-core.
All-red→green is a seventh lesson competitor, explicitly not canonical-fitting.
Witness claims are checked against actual Racket outputs.

Limits remain deliberate: finite motif families, a fixed period, no default
no-op lessons, no input-green sampler branch, bounded object extent, and no
claim to defeat undeclared hypotheses. A model could memorize motif templates
or condition on this curriculum. Wider spatial arrangements and additional
shape families are future distribution work, not established by current tests.
The original author's reasons for most old constants and dead controls are
unknown; placeholder imported notes did not explain them.
## Current reviewer considerations

Source SHA-256: `5e7c468218a1b11c8c73e5d2d00af64889245fd02f6672975401a2764c0b5965`.

# Decisions and evidence — review-0987eedf78c5ead6

## Scope and immutable inputs

The user requested another random task from the supplied packet and preferred
an implemented result, including reusable tools when useful. This round freshly
extracted the original ZIP, verified its manifest, and made exactly one main
draw. Task `3b1ef21add2f`, question `generator-shortcuts`, blind task
`807c284a7e79`, and the later two audit targets were not swapped or rerolled.
The original ZIP SHA is
`abe5d053b32d6dfa2a186f66af2106411df69af0836b69c2d94c030f92061821`.
Earlier rounds were left intact and their evidence is not relabelled as this
round's work. Assignment and setup receipts are in `checks/round-start.json` and
`checks/runtime-and-blind-prepare.json`.

The selected Racket rule already agrees with all canonical labels. Its immutable
rule hash remains `200a2c36d86e`; authority synchronization passed before and
after. Changing the rule to match convenient Python shapes was rejected.
Independent diagnostics compare against actual public Racket outputs.

## R1: teach window membership rather than isolated component recoloring

**Old choice:** isolated red squares, despite documentation promising unchanged
red distractors. The original author's rationale is unknown; imported notes
were placeholders. This support permits all-red→green, exact-component
selection, global size selection, and in-place scanning to appear successful.

**New choice:** simple canonical-style anchors plus rich scenes containing an
overlapping window union, an attached red tail, a separate red square, a hollow
red ring, and a nonred square. Labels remain a simultaneous operation on the
original input. Components help construct contrasts, but are never the selected
reference-rule unit.

Simply adding isolated singleton noise was rejected: it would defeat all-red
but leave component-level rules plausible. Using only 2×4 overlapping rectangles
was also rejected: a greedy in-place scan can tile them correctly. The primary
motif row lengths for two through seven windows deliberately have a covered
union that cannot be tiled by disjoint 2×2s. Rotation/reflection therefore does
not accidentally remove the scan-order counterexample. Tail cells do not add
windows. A separate square defeats selecting only a largest qualifying component.

**Evidence:** independent tests; all 529 Racket/oracle comparisons in
`checks/local-windows/after/`; the actual generated witness; and the final
independent geometry review. Local tests alone are insufficient: the
largest-component rival survives every 3×3 mask because any local red windows
share the center. An explicit two-component witness closes that gap.

## R2: expose exact realizable axes, remove ineffective controls

The old grid bounds were 5..16, while difficulty branches used narrower ranges;
`n_blocks` could underfill after bounded retries. Palette/density/position
controls were ignored or singleton domains. Texture branches returned fixed
9×9 grids and bypassed dimension requests. Strict type rejection was absent.
These choices lacked an explained original rationale.

The new public contract is exactly three integer axes: height/width 7..16 and
the count of **all original red 2×2 windows**, 0..8. The count includes overlaps;
renaming it `n_windows` prevents confusing components with neighborhoods.
Version 3.0.0 signals the intentional incompatible cleanup. Known-axis `None`
keeps the shared omission convention; unknown keys, even with None, raise.
Booleans, floats, strings, and out-of-range integers are rejected rather than
coerced or clipped. `observe_overrides` reads realized dimensions and windows
from pixels. All controls use shared deterministic context machinery.

Lowering the maximum count, retaining no-op compatibility aliases, and silently
expanding a canvas were rejected. Instead a constructive 7×7 tile realizes
every joint request without retries. The first square accounts for count minus
one and a separate square supplies the last window; special zero/one cases use
incomplete red components. Explicit large counts on a two-color schedule draw
use the rich geometry without the foreign square. The profile name means
two-color, not a promise of simple geometry under every override.

**Evidence:** all 3,600 exact joint choices (10×10×9×4 difficulty settings) pass;
the official override stage accepts 28,080/28,080 draws over 312 requested cases
and three bands with no findings. These are different denominators and are not
added as unique input counts. Replay and returned-grid mutation checks pass.

## R3: separate the rule domain, teaching validator, and sampler support

An initial broad-validator proposal would have accepted every well-formed grid.
That would not describe the intended teaching inputs and would leave the generic
mutation check unable to detect an empty or all-recolored scene. The selected
contract instead follows a contrast visible in every canonical input:
show red cells that change and other red cells that do not.

`rule_grid_errors` checks bounded ARC grid format: exact integer digits, a
nonempty rectangle, and dimensions 1..30. `self_check` additionally requires
zero background, at least two four-connected red components, and an uncovered
red cell whenever red windows exist. All canonical inputs pass. No-window
override scenes remain lawful and accepted if they contain the contrasting
components; defaults have windows, avoiding a curriculum of identity-only draws.

This is a deliberate **input teaching grammar**, not a claim that Racket is
undefined on a bare square, a singleton, or an empty-background scene. The
rule can label those grids and the independent probe tests them. Canonical
outputs are not required to pass the input validator. The actual sampler is
narrower than the validator in scale, shape, palette, and component arrangement.
Rejection alone is therefore not recorded as a semantic bug.

**Evidence:** final self-check accepts 60/60 sampled defaults and 3/3 canonical
inputs; it rejects 30/63 generic destructive mutations. Accepted mutations are
not automatically bugs: adding another color or duplicating a row can preserve
the chosen grammar. The local Racket sweep separately reports validator
acceptance of 293/512 masks, 2/14 targeted grids, and 3/3 canonical inputs.
All 529 still receive correct authoritative outputs.

## R4: revise the first repair after an independent 2-core counterexample

The first candidate, SHA
`88e035b21672c2223a2c0f4e8a25f8dac51d9e0a266f4606b84cbe5ebbe95d9b`,
passed 109 focused cases and its 300-lesson/1,200-rotation census against six
declared rivals. Independent review nevertheless found a new graph heuristic:
prune red leaves repeatedly, then recolor the remaining red 2-core. It fits all
2,344 enumerated first-candidate variants and all three canonical pairs.

Retaining this as merely a caveat was rejected because a bounded repair was
available. The first candidate's nonwindow red tetromino was replaced by a
3×3 hollow ring at the free corner of the tile. Its optional one-cell tail
varies the geometry without adding a red window or merging components. The
ring has a graph cycle but no complete red 2×2, directly defeating the new rival.
`red_two_core` and an actual witness predicate were added to the declarations.

An independent test author preserved the original test bytes, strengthened the
schedule contract, and added a separately computed 2-core check. Before changing
the generator, the revised 125-case suite produced 16 failures and 109 passes.
After the repair all 125 passed. The initial importlib collection problem and
both earlier behavioral RED runs also remain retained; none is relabelled as
a successful test. See `checks/focused-refinement-test-authoring.json`.

Final independent review checked 1,768 finite geometry cases, 1,008 rich variants,
920 witness implications across 512 local masks, 48 four-pair holdouts, and
cross-process hash-seed replay. These checks are bounded authoring evidence;
the official Racket-labelled lesson census is recorded separately.

## R5: revise the schedule while preserving arbitrary query holdouts

The first candidate used one anchor and three rich draws per period of four.
Its mandatory profile check observed only 13/60 canonical-envelope hits, below
the required 25% support floor. A nominal 25% mixture leaves no sampling margin.
The final schedule instead repeats **anchor, rich, rich**. Anchors default to
7..8 dimensions and one or two isolated squares. Rich default dimensions are
7..10 easy, 7..13 medium/None, and 7..16 hard; default window counts are 3..4,
3..6, and 4..8 respectively. Explicit controls retain the full exact domain in
every band. These choices vary canvas size and local overlap while preserving
canonical examples across bands; difficulty labels are not psychometric claims.

Three demonstrations plus one query use consecutive accepted indices. Every
four-draw bundle contains an anchor and at least two rich scenes, so every
single holdout leaves a rich demonstration that refutes all seven named rivals.
The final profile check records 18/60 envelope hits and 11/60 exact-profile hits,
with nonzero exact support in each band. Semantic strict support is a different,
stronger structural predicate: 195/600; all six rich witnesses fire on 405/600.

The final census uses 100 lessons per band, requested starts 0..99, and the
tool's retained deterministic seed recipe. It reports 300/300 production lessons
and 1,200/1,200 required rotations with no ambiguity, errors, or hook warnings;
there are 896 distinct input hashes among 1,200 pair occurrences. Fixed-seed
enumeration uses seed 0, all three declared start residues, and all bands:
9/9 lessons, 36/36 rotations, 14 unique inputs. The census's default reporting
modulus remains 6 in one metadata field; `schedule_coverage.period = 3` is the
actual enumerated contract, and the recorded nine lessons confirm its scope.

The first candidate's successful census remains **intermediate** evidence on
its own hash. It does not prove the expanded final rival inventory or replace
the final runs. Complete source JSON is retained losslessly in
`checks/census/*.json.gz`, with original paths, sizes, SHA hashes, and a restore
command in `checks/census/manifest.json`. No failed lessons or old failures were
removed for size. `checks/retain_census.py` packs and restores exact bytes;
`checks/census/summary.json` is a convenience index, not replacement evidence.

## R6: use shared helpers without masking actual rule implementation

The generic linter flagged imported shared names `obj_color` and `flip_lr` as
possible rule translations. Both are legitimate shared component observation
or input-layout helpers; neither exports labels. The final source calls them
through their helper modules, clarifying provenance. No lint suppression,
shared allowlist change, or gate-policy edit was made. Racket label authority
and the other public gates are unchanged. This false-positive pattern is
reported as shared tooling feedback with the exact earlier log.

## Remaining limits and stopping rule

The generator still uses a bounded 7×7 layout, small motif families, fixed
rich-component topology, a period-three palette/layout correlation, and no
default zero-window or input-green branch. A model could memorize templates or
use an undeclared hypothesis; finite named-rival checks do not prove general
identifiability. The validator also accepts many grids the sampler cannot emit.
These limits are explicit and no approval or training-admission claim is made.

The blind and post-repair solves preserve their own real attempts and exposure
declarations. Public feedback cannot establish private query correctness.
Both audit targets are read-only; their findings do not silently expand the
allowed repair scope. The final handoff applies the exact official patch to a
fresh verified extraction and reruns the focused suite there. Work stops after
that required replay and package validation, rather than adding unrelated tests
or chasing an unbounded sequence of speculative rival rules.
