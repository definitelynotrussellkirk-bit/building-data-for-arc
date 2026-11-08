# Working notes: ce99418cc163

Review assignment: `review-79c697b6421ee247`, October 3, 2026.
Original generator SHA256:
`0ed2c27a0023e7a9ccb429c045e4be754ea7910fa7d77dbb0b68a0eb632c3705`.
Final generator SHA256:
`b4cfe7e65fa908424e28ef372fc14e01993f5989a28b8f238e6a6be16060daee`.

No prior return was used as a lead: the task's associated-notes file was empty.
The supplied b90d4c3d5553 example was consulted for interface conventions, not as
empirical evidence about this task. Original author's rationale is unknown.

## Findings and decisions

**R1 — inert controls and narrow support.** v1.1.1 sampled one three-red L,
ignored advertised corner/palette controls and never generated the three-color
canonical profiles. Replace inert controls with five observable axes and four
red-graph families. Preserve input-only generation. Canonical train example 1
has six red cells and SIX additions, proving that arbitrary grouping into two
independent rectangles loses canonical behavior.

**R2 — false-positive validator.** A distractor alone bypassed the old validator;
three unrelated red pixels could also pass. Validate rectangular integer grids,
red graph topology, occupancy counts and at least one lawful writable corner.
The retained before regression run had 33 failures and 5 passes; the same 38
focused tests pass on v2.0.0. This is genuine before/after evidence, not a
manufactured failing solver trace.

**R3 — underdetermined lessons.** Both declared rivals fit all five canonical
pairs. A blocked five-red chain provides both a protected occupied corner and a
remote cell that only iterative closure would fill. The three-slot default
schedule places this witness in every consecutive three-demo window. The
source-bound census checks all three cyclic starts, 102 lessons per band, not
merely individual witness frequency.

**R4 — exact source authority.** The selected archival target differed from
canonical/raw code only by `;; Positions of every red(2) cell`. Removing that
comment synchronizes all active sources without changing semantics or touching
the canonical ledger. The final battery reports synchronized authority and
canonical execution parity.

## Measurements and limits

The after battery has 12 green stages, no advisory/failing stages. Its strict
census passes 600/600 inputs; canonical profile hits are 11/20 easy, 15/20 medium,
12/20 hard. The separate Racket-backed probe passes 612/612 unique generated
inputs and refutes both declared rivals in 306/306 overlapping lessons. Its
seed/index recipe and public-generation parity checks are in the retained
report. These denominators are distinct and must not be added as if independent.

The four motifs leave a template-recognition shortcut and the default schedule
correlates blockers with chain geometry. Arbitrary large red graphs, multiple
irrelevant colors per grid, demonstration dropout and downstream exporter policy
are not covered. `strict_canonical_like` checks a lawful task-local grammar;
it is not an exact test for membership in the sampler's probability support.

The deliberate assembly mutation in `workspace/assembly_probe.py` removes chain
demos but keeps a chain query, making both rivals survive. This demonstrates a
failure of that **constructed** assembly policy, not an observed production
exporter bug. Require ambiguity checks after actual lesson assembly.

All full reports, original failures, source-bound receipts, exposed/blind solve
records, and reviewer-owned fresh-replay results are in the return packet.
Neither solve's hidden-query correctness is available to this reviewer.
## Current reviewer considerations

Source SHA-256: `b4cfe7e65fa908424e28ef372fc14e01993f5989a28b8f238e6a6be16060daee`.

# Decisions — ce99418cc163 v2.0.0

Source identity: baseline `0ed2c27a0023e7a9ccb429c045e4be754ea7910fa7d77dbb0b68a0eb632c3705`;
final `b4cfe7e65fa908424e28ef372fc14e01993f5989a28b8f238e6a6be16060daee`;
canonical rule hash `bc2eb2b8f3e7`. No prior return used as a lead. The original
rationale is unknown wherever the baseline does not document it.

## R1: distribution and exact controls

**Four graph families rather than arbitrary point clouds.** Keep the elementary
single L; add two independent Ls, shared rails, and a five-edge chain. The shared
motif follows canonical train example 1, whose six red pixels induce six missing
corners. The chain is a lawful counterexample to iterative completion. Uniform
random red noise was rejected because most draws either teach identity or obscure
the intended local relation, and validating an arbitrary graph grammar would
expand this bounded repair substantially. Limitation: a learner could recognize
these four templates; larger graphs remain untested.

**Rows and columns sampled independently without replacement.** Randomly permute
support coordinates and transpose the motif. Adjacent coordinates and borders
are allowed. This removes a fixed missing direction, fixed rectangle order and
fixed spacing without requiring collision rejection. Two nominal independent Ls
have disjoint row/column support by construction; geometric interleaving is
allowed. Shared and chain motifs explicitly handle the interactions excluded
by that independent layout.

**Canvas 4–20 in every band, weighted toward 10×12.** The old generator had no
canonical size/palette support. A strong 10×12 component restores that profile
without copying any canonical grid; the remainder still spans the declared
range. Difficulty changes mild size weights rather than silently narrowing exact
controls. Measured exact profile hits: 38/60 final versus 0/60 baseline. The
trade-off is heavy concentration at one canonical shape; this is a support
repair, not a claim of balanced shape sampling or difficulty calibration.

**Fixed semantic colors; one sampled irrelevant color.** Background 0, evidence
2 and output 3 are required by authority. Noise/blocker color is selected from
1,4,5,6,7,8,9. Each grid uses a single irrelevant color, matching canonical-style
palette size, with 0–6 ordinary distractors and a default bias toward 3–4. Palette
swapping red would violate the rule; unconstrained multicolor clutter was
rejected for this pass. Multiple irrelevant colors remain a coverage limitation.

**Occupied corners are separate from ordinary distractors.** A blocker is placed
at a geometrically supported location; ordinary noise is placed outside all
supported/red cells. Chain noise also avoids the remote closure-only cell, so
a random distractor cannot erase the non-cascading witness. A single L with a
blocker would be identity-only and is rejected explicitly, not retried silently.
Noise beyond actual free capacity is likewise rejected with implicated axes.

**Retire inert axes, major version bump.** Advertise only grid_h, grid_w, layout,
n_blockers and n_distractors, with observation from returned pixels. Unknown and
retired controls fail loudly rather than being accepted as no-ops. The alternative
was to invent precise semantics for every old placeholder (palette, anchor,
texture, missing_corner, etc.); this would preserve names but not a trustworthy
contract. Consumers using old keys need migration; this is a deliberate v2 change.

## R2: validator and regression policy

The old distractor early-return accepted a grid with no red evidence. Require
rectangular integer colors, bounded dimensions, recognized red graph topology,
occupancy counts and at least one writable supported corner. The validator is a
lawful-domain check, not exact membership in the probability distribution: e.g.
it can accept multiple irrelevant colors even though this sampler emits one.
The first test run genuinely failed 33 of 38 cases; the unchanged tests all pass
after repair. Invalid types, boundary dimensions, all layouts/bands, exact
controls, structured incompatibilities, determinism and independent rectangle
prediction are explicitly tested.

## R3: demonstrations, rivals and measurement

A three-slot schedule cycles teaching-chain / multi-L / single-L by seed plus
sample index. Any three consecutive default draws contain a blocked chain; this
is stronger than a good marginal witness percentage and costs no rejection
sampling. We rejected purely random 1/3 teaching selection because many short
lessons would omit its witness. We also rejected putting witnesses only at index
zero because other cyclic lesson starts would fail.

Two declared rivals are executable: overwrite occupied fourth corners; or use
newly painted corners recursively. Both fit 5/5 canonical pairs. The chain
separates both and still has real output changes. Its default blocker correlation
and finite motif vocabulary are acknowledged, not presented as universal
identifiability. Exact overrides and downstream demonstration filtering can
invalidate schedule coverage.

The large probe covers all three cyclic starts for 34 seeds per band, retaining
612 unique inputs, 306 overlapping lessons and reference receipts. Actual rival
declarations are iterated, not duplicated by name. Labels come from Racket;
a separately coded rectangle-enumeration oracle cross-checks diagnostic code.
The assembly mutation is explicitly intentional: discard teaching demos and
retain a chain query. Both rivals then survive. No genuine failed solve was
invented to demonstrate this point.

## R4: authority and integration

Canonical and raw Racket code already agreed. The archived target differed only
by one comment, so synchronize that target rather than alter authority, change
labels, or weaken the gate. Canonical ledger SHA256 remains
`08f88dbbda5279692992bc90a689c7b5cc6d426832557708666ecf8532146e41`.

Audits A1–A3 are read-only and outside the repair scope. New tests and probes live
under this task, not shared tooling. A fresh original extraction receives the
exact delta; every patched source hash, focused tests and all task battery stages
are verified again. Training approval is not changed by any of these checks.
