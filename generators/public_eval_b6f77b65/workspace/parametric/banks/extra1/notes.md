# public_eval_b6f77b65 — current authoring decision

## Status: complete candidate implementation; original-label gate blocked

The general Racket rule, input generator, two-setting native adapter, distinguishing
demonstrations, four-query bank, and candidate causal/public checks are implemented.
This family is **not reviewer-ready** because its immutable public parent contains
a documented erroneous training output. Normal authoring preflight was run and
failed with "Official train[1] does not match reference"; no passing preflight,
native inventory, qualification, approval, or acceptance is claimed.

The first assigned family, public_eval_58f5dbd5, was completed before work on this
second family began. The round therefore remains honest partial progress.

## Parent and correction proposal

The frozen challenge record SHA-256 is
1e9a7f12d2d4c28921b2dc9f33d38c4e332aba08d1358518f89608b3a9c0629b.
The test-output record SHA-256 is
9f06d2c5e62844d80e159daef42ae66a24b118a3b6dabf2c93caa3b891182383.
The immutable public-parent.json and raw datasets are unchanged.

Protected Racket matches **7 of 8 complete originals**: four of five training
pairs and all three provided test golds. The only disagreement is zero-based
train[1].output[4][5], predicted 0 versus frozen 2. Color 2 has seven body cells
in that input and eight in the frozen output; deletion and rigid downward motion
cannot introduce that eighth cell. The independent geometry model locates the
extra cell; conservation alone establishes the contradiction, not its unique
coordinate.

This is corroborated by the official repository's
[issue 10](https://github.com/arcprize/ARC-AGI-2/issues/10) and
[followup issue 60](https://github.com/arcprize/ARC-AGI-2/issues/60).
The correction linked from issue 10,
[commit 5e97dbc3d5770a5b2f8b50434a88b88e7ec6d176](https://github.com/82deutschmark/ARC-AGI-2/commit/5e97dbc3d5770a5b2f8b50434a88b88e7ec6d176),
changes the same cell from 2 to 0. That commit is in a contributor fork; it is
evidence for the proposed correction, not evidence that this frozen packet or the
official main branch has been updated.

The proposed JSON pointer is /b6f77b65/train/1/output/4/5. A copied fixture with
only that proposed correction matches all eight predictions in memory. No
corrected fixture was substituted into preflight. The exact proposal, hashes,
all original predictions, and primary-source links are retained under
WORK/checks/public_eval_b6f77b65.

**Next owner action:** adjudicate the source correction; update the dataset and
its provenance through the owner workflow; regenerate the immutable parent
binding; rerun the unchanged authoring preflight; then register, review, qualify
and accept the exact native source. Do not add a task-specific pixel exception,
weaken original-pair checks, or describe the strict expected-failure test as a
passing official gate.

## General rule and admitted grammar

Background is zero. A one- or two-color nonzero prefix in row zero names every
structural color to remove; row one is empty. The header is retained unchanged.
Colors are exact integers in 0..9, dimensions are at most 30 by 30, and the
Python parser requires a complete arch structure below the separator.

A maximal nonzero horizontal run of length at least three is a roof. Its
interior splits into maximal equal-color horizontal beams; its two endpoints
start vertical posts. Each post extends down through the same color but stops
before the next lower roof spanning its column, even if that roof has the same
color. The parser must reconstruct every structural input cell exactly once.
A monochromatic L can therefore contain a post and a separate beam.

After deleting selected pieces, iterate to a fixed point. At the start of each
pass, sort surviving pieces by descending bottom row and use their original
row-major IDs to break ties. A move lowers one entire piece by one cell only if
its destination is in bounds and clear of other pieces. Update occupancy
immediately after each move. Horizontal pieces additionally stay when their
lateral supports satisfy the episode's policy. Posts rely on obstructions below.
All motion is downward and the bounded loop follows a finite movement potential.

The default support_mode=both requires occupancy immediately at both lateral
ends to hold a horizontal piece. The alternative support_mode=either permits
one such end. Both retain the same decomposition, selector deletion, collision
checks, deterministic update order and header. The default program is the exact
reference.rkt; the native copy canonical.rkt is byte-identical and declared as a
local resource. RULE_TASK_ID is literal ee_b6f77b65 and RULE_HASH is ef06dc0a5b58.

The update order is part of this general deterministic rule. It is not claimed
to model every physically possible equilibrium, nor to be order-independent.
An early independent top-first exploratory simulation had additional geometric
mismatches; the retained bottom-first inference and protected reference are the
authoritative candidate evidence.

## Constructive input diversity and teaching

The sampler builds stable scaffolds, including multiple independent bases,
bridges between smaller arches, nested levels, multicolor roof interiors,
same-color joints, unequal post lengths, palette permutations and horizontal
reflections. It never loads original grids or outputs while generating.

The first two demonstrations use two present selectors: a base-post color and
a middle-beam color. Their labels under both settings require more than simple
erasure and more than one gravity pass. The second marker matters, and touching
same-color pieces sometimes drop different distances. Both demonstrations
distinguish the two support policies. An additional demonstration uses absent
selector colors and leaves the scaffold unchanged.

| Source index | Role | Total arches | Core tiers | Input size range |
| --- | --- | ---: | ---: | --- |
| 0 | Teaching plus timing pair | 6 | 3 | 16–18 × 27–29 |
| 1 | Teaching plus joint pair | 7 | 4 | 20–22 × 26–28 |
| 2 | Absent selectors | 2 | 2 | 9–11 × 13–15 |
| 3 | Additional demo | 3 | 3 | 12–14 × 17–19 |
| 4 | Additional demo | 6 | 4 | 20–22 × 25–27 |
| 5 | Additional demo | 7 | 4 | 24–26 × 25–27 |
| 6 | Query | 5 | 3 | 24–26 × 21–23 |
| 7 | Query | 6 | 4 | 26–28 × 27–29 |
| 8 | Query | 8 | 4 | 28–30 × 25–27 |
| 9 | Query | 9 | 5 | 30 × 30 |

The native adapter materializes all six demonstrations and four queries before
taking a requested prefix. A separate GenCtx stream shuffles the complete query
bank before prefix selection. Same seed means matched inputs under both settings.
Requested demos are 2..6 and queries 1..4. Only a selected single-query public
file may be given to the model; the bundle listing and future files are private.

The observable selector_count axis is exactly 1 or 2 and uses
ctx.draw_int_strict. Overrides change the header only, preserve its first color,
and leave the full scaffold unchanged. First two profiles default to 2; caller
overrides still take precedence. Seeds and indices are exact integers in
0..2**63-1. Optional easy/medium/hard strings select layout draw streams; they
are not calibrated difficulty labels. Structural profiles repeat modulo ten with
fresh keyed draws at later indices. The generator performs one self_check.

## Resolved teaching findings

The initial main audit found four either-mode lessons where holding every
horizontal beam fit both demonstrations but failed on a query. The independent
pass found six order-sensitive lessons and one same-color lower-roof-joint
lesson with the same teaching failure. Those source-bound v1 failures remain
retained; they are not counted as passing results.

Demo 0 now includes a separate, initially stable pair of arches. Removing the
existing two selector colors makes a lower beam race the posts above it: the
specified bottom-first update lets it escape before the posts can pin it.
This distinguishes top-first processing under both policies and visibly moves
a horizontal beam under either. Its post heights vary within the constructive
constraint. A blank column isolates this structure from the existing core.

Demo 1 includes a second pair of arches that distinguishes a vertical post from
a same-color beam immediately below it. Binding them moves the post early and
traps a neighboring beam. This pair is appended after the core's reflection:
reflecting that particular pair reverses the relevant same-pass beam-ID tie and
would erase the teaching distinction. The overall rule is deliberately ordered,
so arbitrary reflection equivariance is not asserted.

The compact 6×5 timing and 6×4 joint examples have 24 protected executions with
full programs, labels and runtime identity in the independent evidence. All 25
new sampled rival regressions pass after reproducing 20 failures on the old
teaching construction; two literal tests pin their exact outputs. The original
cores' support-policy, two-marker, cascade and same-color-L checks remain.
The independent v2 audit explicitly verifies that all 32 audited query inputs
are unchanged, and all seven of its old findings are now demo-refuted.

## Executed evidence and limits

The full current family suite reports **146 passed, 1 strict expected failure**
for the frozen known original defect. The generator-specific portion includes
a 960-input sweep, strict types, observable override provenance, initial stability,
body isolation, and meaningful 30×30 support coverage. Literal protected tests
cover a cascade, exact one-pass intermediate, same-color independent motion,
two selectors, a same-color lower-roof junction, and absent selectors.

The static linter reports no errors or warnings and recognizes selector_count
as an observed axis with values 1 and 2. Maximum-seed requests execute all six
demonstrations and four queries under both settings: **20 labels agree with
protected Racket**. The 30×30 case contains 171 nonzero cells, including its
header, and retains 167 after deletion; the scaffold has nine arches on five
levels, with content across the canvas. Counts alone are not a difficulty claim.

The separate blocked-candidate checks execute 24 generated labels at seeds
17 and 43 under both settings, construct and replay two causal counterexamples,
serialize 16 single-query views, test first-turn/private-future invariance, and
reject four corruptions. Their report explicitly uses a candidate diagnostic
schema. The existing passed-preflight evidence loader remains strict and cannot
treat these diagnostics as qualification.

Step A derives disjoint physical pieces and deletes selected colors. Its
intermediate contains the actual input-derived IDs, orientations, colors and
cell sets, plus pre-gravity survivors. Step B settles those surviving bodies.
The executed wrong-intermediate counterfactual replaces rigid pieces with
independently falling pixels; both settings yield different final outputs.
Protected execution and replay validate final labels. The intermediate's
interpretation remains a reviewer argument, not an instrumented proof.

Current main and independent rival results are retained in their source-bound
audit reports. The main v2 pass records 80 of 80 demo refutations, zero
query conflicts or execution errors, and 480 protected executions. All four
of its initial beam-freezing findings are resolved, with all 32 main-audit query
pairs and the rival programs unchanged. The independent v2 pass covers 32 comparisons and 128 rival-query
executions, with 48 canonical claims matching protected Racket and no errors
or query conflicts. Its 28 demo refutations leave four either-mode joint rivals
that agree with every audited query; those are recorded as finite consistency. They test finite named alternatives and seeds; no finite audit
proves universal uniqueness. Every rival executes all four queries even when
a demonstration already refutes it. Execution errors never count as refutations.
No acceptance or training admission is granted by any check in this return.

Current generator SHA-256: 7beb829128c7351152625b3becda792effe0f06eca980e7af08e09df51f6aca3.
Reference/canonical SHA-256: e1d2905dbbdfc0239ac78e7e612305ac77176cc8712b422effecccec281a3f8c.

