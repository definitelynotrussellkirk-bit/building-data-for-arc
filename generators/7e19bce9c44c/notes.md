# Working notes: 7e19bce9c44c

## 2026-10-04 review-26ac03f9f182e076

Prior return `local-random-72fb665ea625` was used as a design lead, not as a
measurement of the selected baseline. Its retained notes correctly identified
the all-nonzero, connectivity-independent crop and intentionally left medium
and hard exact-profile support for later review.

The fresh baseline battery on generator SHA-256
`17014e2200b4a4d49c8e87bd9eb8d8cfadc581944b4e8c5e151928729eacbd55`
was 11 green stages plus one advisory. The profile census found exact canonical
profiles in easy 8/20, medium 0/20, and hard 0/20; the assignment requires at
least one exact hit in every band. The existing modal-color and largest-object
rivals were useful but did not cover a stronger canonical-fitting shortcut:
compute the crop bounds from only the two most frequent nonzero colors, then
preserve the original grid inside that smaller box.

Version 3.1.0 makes two task-local changes. First, default medium and hard draws
at residues 5 and 9 modulo 10 use exact canonical profiles. Anchors stay on odd
residues, and any explicit override disables the internal schedule so the six
public exact controls retain their original semantics. Second, every even
default draw uses three colors and makes the uniquely least-frequent color the
only color on the top boundary; the other two colors own lower left/right
boundaries. This yields a direct counterexample to the new rival without
weakening the existing modal-color, single-object, or internal-hole witnesses.

An intermediate semantic probe found one medium lesson at seed
`122751217542644`, start index 11, whose three demonstrations all missed the
three-color refutation. The schedule was changed from probabilistic color
coverage to deterministic even-index coverage. A later witness probe showed
the same rival witness absent from easy, so the even-index construction was
extended to easy as well. Those failed iterations remain under
`checks/semantic-gate-probe/`, `checks/tdd-red-lesson-schedule/`, and
`checks/tdd-red-easy-rival/`.

Final generator SHA-256 is
`f0ce75d69bb0ffb2f3d407740df371382532eb476225600340c81c0f57583a11`.
The 12-stage after battery is fully green; the profile floor records exact hits
of easy 2/20, medium 4/20, and hard 4/20. The semantic gate accepted all five
canonical inputs, validated 600 generated draws, fired all five declared
witnesses, verified the canonical-fitting rival on 60/60 witness checks, and
found 12/12 sampled lessons identifiable. The larger census materialized
300/300 lessons, checked 1,200 query rotations, and found zero ambiguity or
scoring errors across 1,200 unique inputs. The task-local
`workspace/shortcut_probe.py` additionally exhausts all ten schedule start
residues and all four query rotations in every band.

The selected Racket rule was not edited. Finite declared-rival tests are not a
proof of universal induction; future plausible shortcuts should be added to
`CANONICAL_SHORTCUTS` or `LESSON_COMPETITORS` and replayed through both the
large census and the cyclic-start probe before the schedule changes.
## Current reviewer considerations

Source SHA-256: `f0ce75d69bb0ffb2f3d407740df371382532eb476225600340c81c0f57583a11`.

# Decisions: 7e19bce9c44c

## D1 — Treat retained work as a lead, not evidence

The prior return used was `local-random-72fb665ea625`. Its rationale—crop all
nonzero content regardless of color or connectivity—matches the canonical rule,
but its hard-band profile rationale was remeasured from the selected baseline.
The new baseline battery, not the retained note, established R1.

Alternative rejected: accepting the prior “deliberate extrapolation” as sufficient.
The assignment explicitly requires one exact canonical profile in each band's
20-draw check, so medium 0/20 and hard 0/20 were defects even though pooled
support and all other stages passed.

## D2 — Add sparse default-only anchors rather than flatten the bands

Medium uses a 9×10 canvas, 3×4 content box, seven occupied cells, and two
nonzero colors. Hard uses a 10×10 canvas, 4×3 box, eight occupied cells, and two
colors. They occur at sample-index residues 5 and 9 modulo 10 only when the
caller supplied no overrides.

Rationale: this meets the per-band profile floor while preserving the hard
band's dominant 4×4/three-color extrapolation. Putting anchors on odd residues
leaves an even refutation in every three-consecutive-index window.

Alternatives rejected:

- Make all medium/hard draws canonical-like: easier to verify but erases useful
  extrapolative variation.
- Let anchors partially override caller controls: violates exact override
  semantics and makes controlled experiments surprising.
- Choose anchors randomly: profile frequency would be probabilistic and could
  leave a lesson or a pinned 20-draw census without support.

Failure mode retained: the generator's teaching manifold is narrower than the
Racket oracle. Single-color, border-touching, or filled-box inputs may be lawful
for `crop-to-content` but remain outside `self_check` by design.

## D3 — Declare and defeat the strongest canonical-fitting shortcut found

The new executable rival `two_most_frequent_colours_only` chooses crop bounds
from the two most frequent nonzero colors and then preserves the original grid
inside that box. It fits all five canonical pairs. The three-color construction
makes a uniquely least-frequent color the only occupant of the top crop row;
the two more frequent colors own lower left and right boundaries.

Rationale: this rival strictly subsumes the intuition behind “ignore a tiny
outlier” and is stronger than the already-declared modal-color or largest
single-color-object shortcuts. The construction gives a single-scene,
output-differing witness rather than relying on frequency across a dataset.

Alternative rejected: add only a rival name/test without changing generation.
That would document ambiguity but continue emitting lessons unable to refute it.

## D4 — Make lesson coverage deterministic after the first failed probe

The first implementation allowed the color count to vary. The semantic probe
then found a medium lesson at seed `122751217542644`, start 11, with three
non-refuting demonstrations. A focused red test replayed that exact lesson.
The repair moved three-color refutations to every even default sample index and
kept anchors odd. A second red probe showed easy lacked the new witness, so the
same deterministic schedule was extended to easy.

Rationale: witness frequency is not lesson coverage. With three demonstrations
and one query assembled from consecutive indices, every block and every query
rotation now retains at least one even refutation demonstration. The task-local
probe exhausts all ten schedule starts × four rotations × three bands (120
windows), while the production census checks 300 sampled lessons and 1,200
rotations.

Limitation: this proves only the declared rivals over the tested finite schedule
and sampler. It does not prove the intended rule is the only conceivable rule.

## D5 — Preserve the six-axis public contract

No public axis was added or removed. Any nonempty override dictionary bypasses
the internal anchors, and existing exact controls remain observable. Focused
tests cover all declared boundary combinations, incompatible geometry, bad
types/ranges, deterministic replay, and global-RNG purity.

Alternative rejected: expose a `profile` or `teaching_mode` override. That would
expand the public API solely to explain an internal curriculum schedule and
would add combinations with no user need.

## D6 — Do not edit the Racket authority

The canonical and selected task-local Racket sources remained synchronized;
rule smoke, Racket lint, and authority sync all passed before and after. The
assigned defects were distribution and teaching-contract defects, not oracle
semantics. `RULE_HASH` remains `36e37e8e3020`.

## D7 — Build a reusable task-local probe

`workspace/shortcut_probe.py` reads the generator's actual
`CANONICAL_SHORTCUTS` and `LESSON_COMPETITORS`, verifies canonical shortcut fit,
exhausts cyclic start/query rotations, repeats the official profile-floor seed
recipe, and saves one exact generated disagreement. This avoids future reviewers
copying a stale rival list or inferring lesson coverage from aggregate counts.
