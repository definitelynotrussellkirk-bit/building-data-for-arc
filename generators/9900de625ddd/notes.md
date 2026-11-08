# Working notes: 9900de625ddd

## October 3, 2026 repair

No previous review return or substantive associated note was used as evidence.
The selected baseline was generator version 2.0.1, SHA-256
`3ee7acbb6266b40779f0a1b1a82b5584831e204eda8b8429935a0e4d5aa657b9`.
The packet is an extracted source tree without Git metadata; `git status`
reported that no Git repository exists. No predecessor files were removed.

The baseline's written rule and Racket implementation agree: scan all filled,
monochrome, nonzero 3×3 windows and keep every center. The implementation already
defines overlap. Calling 4×4 squares an ambiguous degenerate case was therefore
a generator-distribution error, not a reason to change the rule. All five
canonical pairs were read and are included in the focused regression checks.
Authority stays pinned to `f64febd0911d`; no authority or admission file changes.

### Findings and choices

1. Isolated 3×3-only sampling taught object centroids and numerous partial
   neighborhood tests. Nine explicit executable alternatives were found to
   fit every canonical pair. Add a guaranteed 4×4 case, a corner-recolored
   3×3 decoy and an edge-recolored 3×3 decoy. The latter two remain 8/9 equal
   and fully occupied; together they test monochromaticity and all neighbors.
   Optional extra holes, tails and 2×2 patches vary the examples further.
2. Retain canonical dimensions/palette counts in a dedicated one-in-three
   profile in every band. Every three consecutive unforced demonstrations
   also include overlap and both recolor decoys. Declare the schedule instead
   of presenting independently measured witness frequency as a lesson proof.
3. Replace fake controls with exact pixels-derived dimensions, patch count,
   foreground color count and shape family. The old color-family aliases and
   density/placement labels never affected input and are retired. The two
   former color-count promises collapse to one exact 1..6 foreground count.
   Unknown and retired controls fail, including null and incorrectly typed
   values. The count is patches, not positive windows; this is stated publicly.
4. Use constructive bounded slot placement instead of capped rejection that
   could silently stop short. Declare conservative packing and palette/count
   incompatibilities and attach their explicitly supplied axis names to the
   exception. Free axes adapt before drawing; accepted keyed values and
   observed pixels agree. No public axis is band-restricted.
5. Strengthen validation to the documented finite shape grammar, background,
   grid/cell types, dimensions, colors, counts and separation, plus at least
   one true window. Full-one-color, empty, malformed and no-target grids are
   outside this training domain. The authority can still handle broader grids.

### Tests first and retained command evidence

The new task-local regression file was written before the generator edit.
From the packet root, the command was:

`python3 run_with_racket.py python3 -m pytest generators/9900de625ddd/tests/test_generator_contract.py -q`

The wrapper's actual test working directory is `repo/`. Against unchanged
baseline bytes, pytest returned **1: 68 failed, 7 passed**. Full output is
`checks/repair-focused-before/pytest.log`. Tests expose ignored/retired keys,
band-dependent control failures, missing observation/semantic hooks, bad grid
validation and missing canonical-profile/lesson coverage. That failure log is
retained, not replaced by the later passing log.

After implementation, the same command returned **0: 75 passed in 0.95s**;
`checks/repair-focused-after-1/pytest.log` records this intermediate run. The
test docstring's probe filename was corrected and a literal period-equals-three
assertion removed; tests still exercise every declared cyclic start and require
each three-demo lesson to refute all declared competitors. The Python erosion
inside the tests is an independent small oracle, not production label authority.
The root review records final batteries, public Racket-backed probe counts,
source hashes and fresh-packet replay separately.

Three intermediate contract checks then ran from the packet root (each wrapper
executed from `repo/`):

`python3 run_with_racket.py python3 -m arcpuzzles check 9900de625ddd --stage lint --timeout 4000 --phase after --out ../checks/intermediate-lint`

`python3 run_with_racket.py python3 -m arcpuzzles check 9900de625ddd --stage defect_lint --timeout 4000 --phase after --out ../checks/intermediate-defect_lint`

`python3 run_with_racket.py python3 -m arcpuzzles check 9900de625ddd --stage override --timeout 4000 --phase after --out ../checks/intermediate-override`

Each returned zero on generator SHA-256
`eb0c7abea013141c2e4025ab39c3531fa6df9bb7d0eec4af782d07a7b799caab`.
Lint reported zero errors and warnings, defect lint flagged zero tasks, and
the override matrix reported 14,220 draws: 12,600 accepted and 1,620 structured
incompatibility rejections, with zero findings or warnings. The unknown-key
probe was rejected. Actual logs/receipts and complete override results are
retained under the named `checks/intermediate-*` directories.

### Scope and remaining alternatives

These examples identify the rule against the ten declared rivals after the
refinement below. They do not
establish unique induction over arbitrary programs, and overrides or lessons
with fewer than three consecutive demonstrations can omit necessary evidence.
The three-profile order itself is visible curriculum structure. Large arbitrary
components, touching patches, zero-match scenes and seven-to-nine foreground
colors remain excluded; `strict_canonical_like` means this lawful declared
manifold, not the original canonical morphology. The uniform reserved-cell
packing policy can reject a count that a more elaborate irregular packing could
fit, and this conservative limit is public. No universal transfer claim is made.

### CR1: positive nonrectangular component refinement

Independent source review found another canonical-fitting rival after the
nine-rival candidate checks: erode only complete monochrome rectangular
components. On candidate `eb0c7abe...`, hard seed 2, demonstration indices
0, 1 and 2 all fit that rival; query index 3 contains a 3×3-with-tail component
whose valid center the rival drops. The independent supported Racket evidence
is `checks/code-review/report.json`; its reported omitted cell is `(8,8)=1`.
The earlier nine-rival candidate passes were genuine but did not test this
tenth alternative. They remain intermediate evidence and are not presented as
final-source measurements.

Before changing the candidate source, two regressions were added: the exact
reported demonstration tuple must refute the independent rectangles-only
rival, and a monochrome 4×4 with one missing corner must validate and contain
three matching windows. The same focused pytest command returned **1: 2 failed,
75 passed** on `eb0c7abe...`; full output is retained in
`checks/repair-refinement-before/pytest.log`.

Version 3.0.1 makes the first unforced overlap patch a 4×4 with one corner
zeroed. It keeps fifteen cells and three overlapping matching windows, so it
is a positive nonrectangular component within the existing reserved 4×4 slot.
This refutes rectangles-only erosion in every consecutive three-demo unforced
lesson without increasing the minimum patch count, colors or canvas bounds.
Explicit `texture="overlap"` retains the full 4×4, and optional later overlap
patches remain complete rectangles. `_kind`, pixel observation and the overlap
witness recognize corner-notched 4×4 patches; the tenth rival and the
`positive_nonrectangle` witness are executable declarations. Tail components
also satisfy that witness. The Racket authority is unchanged.

The focused command then returned **0: 77 passed in 0.97s**, retained at
`checks/repair-refinement-after-1/pytest.log`, against final generator SHA-256
`bbfd833e74437d412e40717fa44316df517f66a2ac8fb1f6e7a7dfd2cec26427`.
The root reviewer coordinates a fresh complete battery, the expanded dynamic
ten-rival public-API probe, source replay and solve episode for these bytes.
The source is frozen after this change; no duplicate intermediate gates were
run after the refinement.
## Current reviewer considerations

Source SHA-256: `bbfd833e74437d412e40717fa44316df517f66a2ac8fb1f6e7a7dfd2cec26427`.

# Decisions for 9900de625ddd

## D1 — Keep the selected Racket authority

The selected canonical task says to scan every nonzero monochrome 3x3 window.
Its Racket rule already implements that rule, including overlapping windows.
The canonical set contains four training pairs and one test pair, all built
from isolated solid 3x3 objects. Original author rationale beyond the retained
summary is unknown; the associated-notes file is empty and no prior review
index is present for this selected baseline.

Changing the Racket rule to require isolated, exactly-3x3 connected components
would narrow the stated rule and preserve a shortcut. We reject that change.
The rule hash remains `f64febd0911d`. The baseline Racket witness in
`checks/before-targeted/racket.json` shows four retained centers for one 4x4
block; the baseline generator source hash is
`3ee7acbb6266b40779f0a1b1a82b5584831e204eda8b8429935a0e4d5aa657b9`.

## D2 — Broaden the teaching distribution beyond exact isolated 3x3 objects

The original ordinary sampler can never distinguish “one center per object”
from “one center per matching window.” A larger solid block is a small,
source-justified discriminator: a 4x4 block has four matching windows. The
baseline incorrectly names its separate 4x4 fixture a degenerate, while its
validator accepts that same fixture.

Larger solid shapes alone leave neighborhood shortcuts intact. A full 3x3
patch with a differently colored corner distinguishes a complete-window rule
from a cross-only or occupancy-only rule. Recoloring an edge midpoint instead
distinguishes it from a center-plus-corners rule. Both are useful close
counterexamples because they retain eight of nine cells of the main color.

These extensions are justified by the selected window-scanning authority.
They are not additional official examples, and their role in the repaired
sampler is explicitly documented. A finite rival battery never proves unique
induction against every possible program.

## D3 — Prefer a smaller exact control surface to inert metadata

Baseline measurements in `checks/before-targeted/diagnostics.json` confirm
that all four purported helpful textures are byte-identical to the same
untextured draw and that an unknown override key is silently accepted.
The advertised height 5 is rejected in the easy band despite the declared
5..24 domain. The full baseline override report preserves the larger matrix.

Inert palette-family, density, position-bias and duplicate count controls
should not remain advertised as functioning exact controls. The replacement
surface must be recoverable from output pixels, honor feasible requests, and
reject unknown or incompatible requests explicitly. Reported controls must
describe realized patches and colors, including near-miss patches, rather than
label-authority outputs or an unobserved intention to place an object.

## D4 — Assess the unit actually used for teaching

A witness rate over individual draws does not establish that each lesson
shows the relevant difference before asking its query. The retained probe
therefore evaluates complete three-demonstration/one-query lessons using the
public generation API, dynamically reads the generator's declared rivals,
and distinguishes refuted rivals from those surviving demonstrations with
either an agreeing or a disagreeing query prediction.

If a small deterministic teaching cycle is used, every cyclic start must be
tested. Counts must distinguish lesson windows, total grid occurrences and
unique inputs. Exact override requests and arbitrary externally assembled
subsets do not inherit an unqualified guarantee from the default sampler.

## D5 — Preserve evidence and separate acceptance from training admission

The original packet and assignment are immutable. The repair, tests and probe
stay in the assigned task directory. Audit targets are findings-only. The
optional shared-tool proposal stays outside `patches/source.patch`.

Final acceptance evidence uses one generator hash across the final checks,
post-repair solve episode and fresh-packet patch replay. Checker feedback for
both solve episodes exposes visible-example results and execution only;
masked-query accuracy remains unknown until independent scoring. Passing
checks does not upgrade the task's existing training-safety status.

## D6 — Close the concrete complete-rectangles-only teaching gap

The first candidate passed all twelve shared stages and eliminated all nine
then-declared rivals in 420/420 lessons. Independent review nevertheless found
a simple omitted rival at hard seed 2: complete-rectangles-only erosion fits
all three demonstrations and then loses a valid query center in a tailed
component. This actual Racket-backed failure is retained in
`checks/code-review/report.json`; its exact version 3.0.0 generator bytes are
retained in `checks/prior-candidate/generator.py`.

Version 3.0.1 adds that tenth rival and changes the first unforced overlap
patch to a 4x4 square with one missing corner. The same reserved 4x4 space now
contains a positive nonrectangular component with three matching windows.
Unlike adding another object or increasing the minimum canvas, this introduces
no extra packing requirement. Full 4x4 rectangles remain available through
explicit overlap texture and ordinary extra rectangles. The finite grammar,
observer and witness hooks all recognize the new patch. Two new regression
cases failed before the fix and passed afterward; the full task suite has 85
passing tests, including 77 generator tests and 8 probe-scoring tests.

The final 420-lesson measurement dynamically discovers all ten declarations.
All ten fit 5/5 canonical pairs and are refuted by demonstrations in 420/420
lessons. Ordinary lessons use three consecutive demonstrations; forced
textures, smaller demonstration sets and externally assembled subsets are
explicitly outside this teaching guarantee. A visible three-profile cycle,
conservative packing and finite grammar remain deliberate limitations, not
claims of universal induction or unrestricted shape coverage.
