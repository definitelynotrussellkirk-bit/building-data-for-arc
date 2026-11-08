# Working notes: 2636c90a673a

## Review 2026-10-05

The selected `1.1.2` baseline emitted sparse random bodies, advertised dead and
overlapping axes, omitted `RULE_HASH`, silently accepted unknown controls, and
narrowed valid integer overrides by difficulty. Its completed before battery
was 6 green, 2 advisory, and 4 failed (`checks/before/`).

Version `2.1.0` pins the authority, advertises only six real controls, validates
all exact overrides, supports the three canonical size/palette profiles, and
constructs one connected nonzero body with canonical-scale monochrome rows.
Headers contain non-blue decoys. Every default has a repeated color-3 decoy;
even sample indices use two blue selectors and three color-3 decoys, giving two
frequency witnesses in every four consecutive pairs. This refutes the four
canonical-fitting rivals declared in `generator.py`: nonzero, odd, repeated
nonzero, and modal nonzero header selection.

Two test-first corrections are retained. The first candidate scattered colors
cell-by-cell and failed canonical component-scale coverage; a full-width
monochrome body row repaired it. A later self-review found that the modal and
repeated-marker rules still fit all generated examples despite a green shared
battery; the final frequency-decoy schedule repairs that gap and survives every
query rotation in task tests and the 300-lesson shared census.

No Racket source or canonical row changed. The independent probes live in
`workspace/reference_probe.py`; focused regressions live in
`tests/test_generator.py`.
## Current reviewer considerations

Source SHA-256: `1b6782f0c8e7f177d427cd8f901e9c49faa310bd187ba1915d7fd33de8add3de`.

# Decisions for 2636c90a673a

## D1 — Preserve the selected Racket authority

**Choice.** Keep the canonical transformation unchanged and pin
`RULE_HASH = "2d7db8fb7aa9"`.

**Rationale.** All canonical pairs, rule smoke, Racket lint, execution parity,
and authority synchronization were already correct. The failures were in the
Python input curriculum and contract, not the rule.

**Rejected alternative.** Rewriting Racket to accommodate the old random
curriculum would alter a correct task and hide the actual distribution defect.

**Probe/failure mode.** The final authority-set hash is unchanged at
`5ecacf24...`; any future rule edit must rerun canonical and parity checks.

## D2 — Remove decorative axes instead of pretending to honor them

**Choice.** Retain only `grid_h`, `grid_w`, `n_keep`, `palette_size`,
`body_style`, and `density`.

**Original rationale.** Unknown. The baseline named eight combinatorial axes,
but `position_bias` and `density` were singleton/dead, `palette_kind` and
`texture` overlapped, and `n_distinct_colors` duplicated palette size.

**Alternatives.** I considered implementing all legacy textures. They added no
rule-relevant distinction and included deliberate degenerates in the normal
domain, so removal was clearer and more falsifiable.

**Probe.** The override matrix exercised 325 cases × 3 bands × 30 seeds:
29,250/29,250 accepted with zero mismatch. Unknown and retired names fail loudly.

**Limitation.** Removing names is an API change; the selected baseline was
unapproved and its advertised contract was already false.

## D3 — Use canonical profiles for defaults, full legal ranges for overrides

**Choice.** Default to `(height,width,palette) = (5,7,9), (6,8,10), (6,9,10)`
with difficulty weighting; permit explicit dimensions 5..9 × 7..12 and palette
4..10.

**Rationale.** Exact canonical profile support was missing, especially in hard.
Profiles preserve evaluation scale, while explicit controls retain useful breadth.

**Rejected alternatives.** Fixed one canonical shape would pass a floor but
collapse diversity. Unbounded random dimensions recreated the baseline drift.

**Probe.** Final profile floor: 60/60 exact and 60/60 envelope; diversity and
distribution gates pass.

## D4 — Schedule selector count rather than keep it always canonical

**Choice.** On even sample indices, default `n_keep=2`; on odd indices use the
profile's canonical count (4 or 5). Exact `n_keep=2..5` overrides remain honored.

**Rationale.** Canonical-only counts make blue the most frequent nonzero marker.
With two blue selectors and at least five unselected slots, the generator can
place three color-3 decoys and produce a decisive frequency counterexample.

**Rejected alternative.** Keeping `n_keep=4/5` and only changing distractor
colors cannot make another color more frequent on the 7- and 9-column canonical
profiles.

**Failure mode.** A single frequency witness per four-pair lesson fails when it
is held out as query. The final parity schedule supplies two, so any rotation
retains one demonstration witness.

## D5 — Use repeated odd-colored header decoys

**Choice.** Every default repeats color 3 in unselected columns; frequency
witnesses use three 3s versus two blue 1s. A color-2 decoy is added when space
permits.

**Rationale.** This one structure refutes four nearby hypotheses:
all nonzero, all odd, all repeated nonzero, and modal nonzero color.

**Rejected alternatives.** One 2 plus one 3 refuted only nonzero/odd and was the
intermediate semantic defect. Repeating only color 2 would fail to refute the
odd-valued shortcut.

**Probe.** `checks/tdd-frequency-shortcut-red.log` shows zero frequency witnesses
before the change; final semantic gate observes 304/600, and the 300-lesson
rotation census finds zero ambiguity.

## D6 — Construct one connected, blocky body

**Choice.** Support row-band, column-band, and mixed structures at medium/dense
levels. Row 1 is fully occupied; an anchor spine keeps the scene connected;
background remains present.

**Rationale.** The old 45%-independent cell noise produced about nine nonzero
objects versus canonical about one. A connected scene preserves task focus and
supports attributable morphology controls.

**Alternatives.** Copying canonical bodies exactly would overfit three samples.
A single fixed rectangle would satisfy drift but remove meaningful diversity.

**Probe.** Independent component counting is in `workspace/reference_probe.py`;
all legal joint overrides and 144 default samples are checked in task tests.

## D7 — Restore canonical same-color component scale with a monochrome stripe

**Choice.** Paint the full first body row color 2, then place every requested
additional palette color in the remaining connected cells.

**Rationale.** The first repair's round-robin painter made same-color components
too small. Canonical inputs have monochrome rows/components of sizes 7, 9, and 10.

**Rejected alternative.** Relaxing or ignoring `canonical_coverage_soft` would
retain a real visual gap. Making the entire body one color would lose palette
support and task richness.

**Probe.** `checks/tdd-component-scale-red.log` failed at generated maximum 6
versus canonical median 9; the green log passes 45 tests, and final defect lint
has zero findings.

## D8 — Validate the owned manifold, not only mask presence

**Choice.** Check rectangular ARC-valued grids, legal dimensions, 2..5 blue
selectors, at least two unselected columns, palette size 4..10, a full body row,
multiple body colors, and one connected nonzero scene.

**Rationale.** The old validator accepted minimal impostors and did not own the
generator's actual training domain.

**Alternative.** A validator exactly replaying construction internals would be
brittle and reject canonical inputs. The final checks state observable invariants.

**Limitation.** `strict_canonical_like` intentionally shares these observable
invariants; it is not a proof that a grid came from this generator.

## D9 — Declare executable rivals and test rotations

**Choice.** Declare four canonical-fitting shortcuts, one additional lesson
competitor, three witnesses, and `lesson_identifiable`; independently transcribe
them in `reference_probe.py` tests.

**Rationale.** Correct labels are insufficient when every demonstration also
supports a plausible wrong rule. Query rotation matters because a unique witness
can disappear from demonstrations.

**Probe.** Task tests cover eight cyclic starts × four held-out positions × three
bands. The shared census covers 300 production lessons and all 1,200 rotations.

**Limitation.** These are finite, named rivals. Undeclared program synthesis may
find other equivalent descriptions; results are evidence, not uniqueness proof.

## D10 — Keep failed iterations and source-bound solves

**Choice.** Retain the original failed battery, the component-scale 11/12 run,
the intermediate green-but-frequency-vulnerable battery/census, and its old solve.
Prepare a new solve after every generator hash change.

**Rationale.** Failures explain why each change exists and prevent a solve from
being silently rebound to later bytes.

**Cost.** Extra evidence consumes return budget; duplicate runtimes and repository
trees are excluded, while decisive reports and logs are retained.

<!-- arcpuzzles-current-supplementary:start -->
## Current supplementary checks

Current source-bound ticket observations: `generators/2636c90a673a/evidence/supplementary-current.json`. Results are reviewer-reported; blocked or unknown stays explicit. These observations do not approve a generator or variant, resolve audits, or admit data to training.
<!-- arcpuzzles-current-supplementary:end -->
