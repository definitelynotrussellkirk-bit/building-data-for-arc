# Working notes: d6115f669a8e

## 2026-10-03 review

The selected v1.2.0 baseline generated arbitrary 3–5-cell motifs but did not
encode the canonical left-to-right sorting curriculum. It lacked `RULE_HASH`,
`self_check`, strict canonical support, executable semantic witnesses, and
observable exact overrides. The before battery consequently reported 6 green,
1 advisory, and 5 failed stages; see
`checks/before/checks/d6115f669a8e_before_battery_summary.json`.

The repair replaces that distribution with a deterministic five-profile cycle:

1. `canonical`: three distinct-color 3-cell L objects at canonical dimensions;
2. `order_conflict`: x order conflicts with top, color, and area order;
3. `width_contrast`: right-edge sorting and center alignment disagree;
4. `equal_left`: two objects share a left edge and require the top-row tie break;
5. `shared_color`: two disconnected objects share a color and must remain
   separate components.

All profiles fit the advertised 7×9 minimum. `grid_h`, `grid_w`, and `texture`
are the only public axes; exact dimensions work throughout their full ranges,
and unknown or malformed overrides are rejected. The validator enforces a
rectangular 0-background grid, exactly three same-color 4-connected components,
2–3 object colors, bounded object/output sizes, and ARC color types.

The production label authority remains the unchanged canonical Racket rule.
`rule_mirror`, `SEMANTIC_RIVALS`, `CANONICAL_SHORTCUTS`, and
`LESSON_COMPETITORS` exist only for tests and review evidence. The four declared
canonical shortcuts were verified to fit all three canonical pairs before being
used as teaching targets.

Test-driven evidence is retained under `checks/tdd/`: the regression suite
failed 8 tests against the original generator and passed 14/14 after the repair.
The final after battery is 12/12 green. The source-bound probe in
`workspace/review_probe.py` checked 500 complete lessons per band (all five
cyclic starts), 7,500 input occurrences / 2,291 unique inputs, and found no
surviving declared rival. It also matched the Python mirror to Racket for 75
generated cases plus all three canonical pairs.

Limitations: the curriculum intentionally fixes the object count at three and
uses a small constructive shape vocabulary; rival coverage is finite and does
not prove universal identifiability. The probe therefore records its sampler,
domain limits, exact source hashes, and bounded Racket subset rather than
claiming universal induction.
## Current reviewer considerations

Source SHA-256: `014e97b0c715ec71dbf45d146b8d61f89656d64794e1ee209a8429206c92ce5f`.

# Decisions for d6115f669a8e

## D1 — Replace generic motif sampling with a rule-directed curriculum

**Baseline / original rationale.** The v1.2.0 source appears to have prioritized
shape, palette, and placement diversity by growing arbitrary small polyominoes.
No retained note explains why those axes were chosen. That distribution produced
lawful-looking grids, but it did not deliberately expose the canonical sorting,
tie-break, alignment, separator, or component-identity decisions.

**Decision.** Use five constructive profiles in a deterministic cycle so every
five consecutive examples contain the complete teaching set.

**Alternatives rejected.** Pure random rejection sampling could eventually find
witnesses, but would make complete-lesson support probabilistic and difficult to
replay. A single highly contrived mega-example would be compact but unlike the
canonical morphology and harder for a small model to decompose.

**Probe / evidence.** The before semantic gate had no executable contract. The
final source-bound census tested every cyclic start and found zero surviving
named rivals in 1,500 complete lessons:
`checks/probe/d6115f669a8e_lesson_census.json`.

## D2 — Preserve canonical support explicitly

**Decision.** One example per cycle uses three distinct-color, three-cell L
objects at dimensions cycling through 7×9, 9×9, and 9×10. `strict_canonical_like`
checks those dimensions, colors, component count, area, and 2×2 bounding boxes.

**Rationale.** The baseline profile-floor check hit 0/60 canonical profiles.
Canonical anchoring reduces distribution shift while the remaining profiles add
the counterfactual evidence absent from the original task pairs.

**Failure mode considered.** Making every example canonical-like would preserve
appearance but leave four known shortcuts unfalsified. Therefore only one fifth
of the schedule is strict-canonical-like.

## D3 — Teach primary ordering independently of incidental cues

**Decision.** `order_conflict` assigns object x-order so that top-row, color, and
area order all disagree with the canonical `(left, top)` order; reverse-left is
also necessarily wrong.

**Alternatives rejected.** Random colors and positions do not guarantee a
conflict in any particular lesson. Sorting colors before placement would create
a new accidental correlation. The profile instead randomizes the actual colors
then maps their sorted ranks to a deliberate permutation.

**Limitation.** The profile uses a fixed size/position template. Color values and
global offsets vary, but this remains finite constructive evidence.

## D4 — Separate left-edge ordering from right-edge and alignment rules

**Decision.** `width_contrast` uses crop widths 4, 1, and 2. The first object's
right edge lies to the right of the second object's right edge even though its
left edge is earlier, and narrow crops make left alignment disagree with
centering.

**Rationale.** All three canonical pairs have equal-width crops, so both
`sort_by_right_edge` and `center_align` fit every canonical output. This profile
is the minimal two-defect witness that still contains three ordinary objects.

**Probe.** Both rivals disagree on exactly the scheduled width profile in every
band and survive zero complete lessons in the final census.

## D5 — Expose the top-row tie break

**Decision.** `equal_left` places two objects at the same leftmost column with
different top rows. The higher component must precede the lower one.

**Alternative rejected.** Forcing all left edges distinct makes the tie-break
unlearnable. Random collisions are too rare and can create touching components.

**Limitation.** Only a two-way tie is generated; a three-way left tie is lawful
but unnecessary to distinguish the declared rival.

## D6 — Preserve component identity when colors repeat

**Decision.** `shared_color` gives two disconnected components the same color,
with a third component in another color. They remain separate objects under
same-color 4-connectivity.

**Rationale.** Canonical inputs use three distinct colors, so grouping all cells
of a color fits every canonical pair. Reusing one color is sufficient to refute
that shortcut while retaining a simple palette.

**Failure mode considered.** Same-color components must never touch
orthogonally. The constructive coordinates and global translation preserve a
safe gap; `self_check` independently verifies exactly three components.

## D7 — Use exactly three objects and two or three colors

**Decision.** Hold object count at three, matching the canonical examples, while
allowing a repeated color only in the dedicated component-identity profile.

**Alternatives rejected.** Increasing to four or more objects adds combinatorial
variety but also distribution shift and larger output dimensions without
falsifying an additional current rival. One or two objects underteach ordering.

**Limitation.** Generalization to more objects is not directly trained. This is
recorded rather than hidden behind a broad `n_objects` axis.

## D8 — Advertise only controls that are exact and observable

**Decision.** Public axes are `grid_h` (7–18), `grid_w` (9–20), and `texture`.
Explicit dimensions are honored for every texture and band. Unknown keys,
booleans masquerading as integers, out-of-range dimensions, and unknown textures
raise `ValueError`.

**Baseline issue.** The old source advertised overlapping/dead controls and
failed thousands of override cases; unknown keys were accepted.

**Alternative rejected.** Keeping decorative axes for compatibility would
continue to make metadata lie. Removing them is safer than silently ignoring
them.

**Probe.** Final override gate passed with no findings or warnings and rejected
unknown keys; task tests exercise min/mid/max exact dimensions for every texture.

## D9 — Keep Racket as the sole production authority

**Decision.** Pin `RULE_HASH = e09122d9163c` but do not edit the canonical Racket
row or archival solution. `rule_mirror` is an independently executable
review/test oracle only.

**Rationale.** Canonical outputs already match the written transformation and
rule smoke/authority sync passed before repair. The defect was the input
curriculum, not label authority.

**Probe.** The after battery's rule smoke and authority sync are green. The
lesson census matched Racket on 75 generated inputs plus all three canonical
pairs.

## D10 — Treat finite rival analysis as bounded evidence

**Decision.** Declare nine plausible competitors and four canonical-fitting
shortcuts in source, then have tests and the reusable probe iterate those actual
declarations.

**Alternatives rejected.** Hard-coding rival names only in a report can drift
from source. Claiming universal identifiability from a finite set would be
unsupported.

**Limitations.** Unenumerated programs may still fit the lesson. High-volume
scoring uses the Python mirror; only a bounded subset is checked with Racket.
Both limits are emitted in the probe report.

## D11 — Add task-local regression tests and a reusable census tool

**Decision.** Add 14 task-local tests and `workspace/review_probe.py`. Tests were
written against the desired contract and observed failing on the original
source before implementation. The probe records source hashes, sampler, cyclic
starts, profile counts, unique inputs, rival disagreements, and Racket parity.

**Failure encountered.** The first probe run reached the Racket boundary but
failed because portable `wrap_rule` imports `scripts.comment_solutions`; the
probe now exposes `shared/tools` as a read-only `scripts` package in its own
process. The failed and successful logs are retained under `checks/probe/`.

## D12 — Stop after the verified bounded repair

**Decision.** Do not refactor shared helpers, alter catalog approval, edit audit
targets, or broaden the Racket rule.

**Rationale.** The selected after battery is 12/12 green, task tests are 14/14,
the large lesson census is clean, and the fresh visible solve passed 5/5 on the
exact final generator hash. Additional unrelated work would increase intake
risk without addressing the assigned defect.
