# Working notes: b650a355848c

## Current parametric decision

Use one episode-fixed parameter, `assignment_policy`, with exact canonical
`independent_nearest` as the default and `minimum_bijection` as the alternate.
Both preserve the source task's segmentation, marker-distance reasoning,
shape cropping, orientation-dependent ordering, and 4×4 stacking. The changed
step is meaningful: independent selection permits marker reuse; the alternate
requires a unique global one-to-one optimum.

## Sequential dependency

A computes the full shape-bounding-box/marker distance relation and chooses the
input-dependent assignment. The retained intermediate is the ordered
shape→marker/color mapping. B consumes that mapping to recolor each crop and
stack it. The protected causal witness replaces A with a constant first-marker
mapping while retaining B and changes the final output.

## Teaching and sampler repairs

The initial random lessons identified the two declared settings but admitted
three harmful shortcuts: nearest occupied shape cell, greedy nearest-unused
assignment, and simple marker-axis pairing. A fourth accidental color-order
shortcut survived two seeds. The first two lessons are now complementary fixed
2-D constructions, with randomized distinct colors and one transposed lesson;
they reject all four shortcuts without adding demonstrations.

A 64-seed census also exposed a separate abort: later markers were selected only
for distance to their own shape and could tie another shape's nearest marker.
Marker placement now uses a finite global construction search that checks unique
nearest choices, marker reuse, unique global optimum, and policy disagreement
before colors or isometries are committed. This is constructive, not a retry
loop.

## Evidence and limits

- Focused contract suite: `workspace/parametric/evidence/current/focused-tests.log`.
- Finite rival/sampler audit: `workspace/parametric/evidence/current/self-audit-report.json`.
- Native qualification, exact execution receipt, and causal witness are under
  `WORK/checks/b650a355848c/` in the return packet.
- The rival audit is finite and does not prove uniqueness against arbitrary
  hypotheses. Reviewer qualification is not owner acceptance or training
  admission.

<!-- arcpuzzles-current-supplementary:start -->
## Current supplementary checks

Current source-bound ticket observations: `generators/b650a355848c/evidence/supplementary-current.json`. Results are reviewer-reported; blocked or unknown stays explicit. These observations do not approve a generator or variant, resolve audits, or admit data to training.
<!-- arcpuzzles-current-supplementary:end -->
