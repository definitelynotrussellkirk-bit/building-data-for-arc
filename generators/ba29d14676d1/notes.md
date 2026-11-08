# Review notes: ba29d14676d1, v3.0.2

Final source SHA-256: `a10720b648bf8a9d7b5bbe6c076b17b94119bc5c79869f4ec566ddfa89aef84e`. Authority unchanged; rule hash `93b766a34b8e`.

The pinned v2.2.0 baseline had inert axes and incorrectly restricted overrides.
The final source uses exact geometry/color controls, strict lattice validation,
and a three-profile curriculum: canonical, compact counterexample, independent.
Six consecutive default draws support five demonstrations plus any one held-out
query against eight declared rivals. This is a bounded claim, not unrestricted
identifiability. Overrides/fewer demos/independent resampling can remove witnesses.

Self-review preserved individually symmetric tiles, added the stronger
outer-columns-only rival, and corrected size drift by shrinking witness scenes.
No shared or audit source was edited. Full decisions and honest failed iterations
are in the returned DECISIONS.md and checks/ evidence for review-dc64e0b5160721cf.

Tests under tests/ are portable; workspace/probe.py emits a public-reference corpus.
Final reports: 36 task tests, 12/12 battery stages, 300 lessons/1800 rotations,
64/64 independent public-Racket applications. See source-bound return evidence.
The blind and exposed solve episodes each passed five visible examples; hidden
accuracy is withheld. Neither is a token-level model trace.
## Current reviewer considerations

Source SHA-256: `a10720b648bf8a9d7b5bbe6c076b17b94119bc5c79869f4ec566ddfa89aef84e`.

# Decisions and rejected alternatives

Assignment: review-dc64e0b5160721cf; task ba29d14676d1. Final source v3.0.2.
The original source established current behavior; original author intent beyond
its comments is unknown. No unintegrated prior patch was substituted for the
pinned baseline. IDs below correspond to REVIEW.md.

## R1 — exact controls rather than cosmetic switches

The original palette/density/position controls did not reliably select observable
features, and some advertised shape boundaries were rejected. I removed inert
public controls instead of inventing arbitrary behavior for their names. Five
integer controls directly govern geometry and foreground; supplied overrides use
the entire declared domain independently of profile or band. No aliases silently
coerce strings, floats, booleans or misspellings. `None` means no override.

Alternative: retain names for compatibility and warn. Rejected because callers
would still believe a requested variation occurred. This is an intentional API
cleanup: old no-op controls now raise ValueError. All 1,536 joint tuples per band,
not merely one axis at a time, are checked. Exact foreground may deliberately
remove the color-independence teaching witness; callers changing curriculum
controls must rerun lesson diagnostics.

## R1 — validate the lattice itself

Full-color-9 rows/columns must be internal single dividers enclosing equal-sized
tiles, without border/adjacent dividers or a stray 9 inside a tile. Every tile is
nonempty and at least one is LR-asymmetric. Literal integers 0–9 are required.
The validator accepts all three canonical labeled pairs, including individually
symmetric tiles. Raising on bad generator controls and returning reasons for a
bad grid are separate contracts.

Alternative: accept any grid on which the reference returns an output. Rejected:
the reference supports a broader language than the chosen teaching domain, and
that would hide malformed/accidentally degenerate generator samples.

## R2 — retain canonical shapes, but teach a real generalization

The original one-row, width-three distribution cannot separate reflection from
swapping outer columns. Canonical shape is one of three recurring profiles, not
a universal size restriction. The declared strict profile is honestly 3-by-11
with a single foreground role; `MIN_STRICT_FRAC=0.25` is explicit rather than
claiming every lawful generalization is canonical-like. All canonical inputs pass.
Foreground 4 is retained but not treated as a semantically special color.

Alternative: stay at width three and describe the shortcut in prose. Rejected
because no generated demonstration could refute it. Rectangle widths 2–5 and
heights 2–5 are supported by the unchanged authority and independently cross-checked.
The maximum grid is 17-by-29, within the task's intended small-grid setting.

## R2/R4 — a compact, rotation-resilient teaching schedule

`sample_index % 3` selects canonical / witness / independent. The default witness
uses two tile rows, four tile columns, height 2–3, width 4–5, and foreground not 4.
Only one additional row/column is needed to challenge first-row/first-three-column
rules. Six consecutive draws contain two witness profiles; holding out any one
pair still leaves a witness. Five demonstrations are therefore declared, not
silently assuming the usual three are enough. Tests cover every cyclic start
for a deterministic set of seeds and bands, and Racket-labelled census rotations
check production-shaped lessons.

Alternative: randomly select a profile per example. Rejected because rare
witnesses can be absent from an otherwise valid lesson. Alternative: identify
one reserved query position. Rejected for this repair because query rotation is
useful downstream. This guarantee is not claimed for independently drawn
examples, fewer demos, arbitrary subsampling or witness-removing overrides.

v3.0.1 used larger witness rows/heights; an actual distribution-drift failure
showed excessive average area. v3.0.2 preserves the useful counterexamples in a
smaller 2-by-4 scene and reserves the broader size support for independent draws.
No shared threshold was changed and no failed evidence was removed.

## R2/R3 — random placement, minimal corrective edits

Start with sparse random marks per tile, gently scaled by tile area. At 3-by-3,
base draws use 3–5 marks. Force an endpoint asymmetry only when an entire tile row
or an additional tile column would otherwise lack one. An interior mirror-pair
asymmetry is additionally ensured in the witness profile. The correction chooses
a random qualifying position; there is no fixed marker/corner. These edits can
change the initial sampled mark count, so the count is not advertised as an exact
axis.

v3.0.0 corrected every tile column, accidentally eliminating symmetric individual
canonical tiles. A targeted failing test demonstrated that loss; the final source
only conditions extra columns beyond the canonical three. Symmetry is observed
in each canonical column across seeds 0–99. Complete identity transformations and
empty tiles remain intentionally excluded from production to keep the operation
observable; separate diagnostic degenerate constructors test rejection.

## R2 — independent third profile and finite rival declarations

The third profile draws all dimensions and foreground independently. This avoids
teaching that noncanonical width necessarily means multiple tile rows or a
non-4 color. A finite 600-seed probe covers all eight combinations of the chosen
three feature predicates; this is coverage evidence, not proof of independence
for all statistics. The earlier 150-seed probe missed a rare combination and is
retained as a genuine test-coverage failure.

The five canonical-fitting declarations are checked against all canonical pairs.
Three more lesson competitors cover identity, global LR reflection and vertical
reflection within tiles. Rival lists in the retained probe are read dynamically
from the source, not copied into a stale tool list. Competing rules that survive
demos but agree on the query are distinguished from answer ambiguity. No claim
is made about undeclared rivals or learned-model accuracy.

## Tooling, reference and scope

`workspace/probe.py` retains 64 named inputs and independent expected outputs for
public `arcpuzzles apply` cross-checks. Portable task tests find the public runtime
root rather than assuming a particular parent depth. Final validation includes
the task-test staging command, which the general battery does not run.

No Racket change was needed; authority hash 93b766a34b8e remains pinned. The two
random audits are findings only. Both solve records are genuine single attempts;
the second declares previous exposure, and neither reports hidden accuracy.
Shared-process suggestions are separate in FEEDBACK_TO_CODEX.md; no shared patch
is mixed into this task delta.

## 2026-10-25 parametric admission candidate — tile selection before reflection

The canonical default remains exactly `tile_scope=all_tiles`: every tile delimited by
full color-9 rows and columns is mirrored left-to-right by the accepted program. The
new branch `tile_scope=densest_only` uses a genuine two-stage rule. It first partitions
the lattice, counts occupied cells per tile, and selects the unique densest tile; it
then mirrors only that selected tile. A protected-Racket wrong-intermediate witness
substitutes the sparsest tile and changes the output, so the second stage is causally
dependent on the selected tile rather than merely adjacent prose.

The minimum two-demonstration lesson was adversarially hardened after an early sampler
made the densest tile nearly full and allowed an `exactly_one_blank` shortcut. The
final sampler varies occupancy and selected position across the first two examples.
The retained `rival_audit.py` checks 13 named alternatives, including first/last,
sparsest, majority-filled, exactly-one-blank, and fixed tile indices 0–7. Across 256
consecutive seeds none survives both demonstrations. This is finite rival evidence,
not a universal uniqueness proof.

Final reviewer evidence is source-bound to the task-local inventory. Native
qualification covers both settings at seeds 0 and 17, with two demonstrations and
four distinct queries per job: 4 jobs and 32 protected-Racket evaluations. The
matched-input self-audit covers all supported demonstration counts 2–6 over three
seeds (30 episodes, 240 labeled pairs), preserves first-turn serialization, and
includes 29×29 multi-tile and lawful 30×30 single-tile stress. The production
`generator.py`, canonical authority, and shared runtime were not modified. Exact-source
owner acceptance and any training admission remain pending.
