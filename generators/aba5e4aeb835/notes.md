# Working notes: aba5e4aeb835

Record design decisions, hypotheses, review findings, and unresolved questions here.
Imported associated notes retain original evidence/timestamps in `evidence/associated_notes.jsonl`.

## 2026-10-03 review-d83e98f966e5d70f

The imported 1.3.0 sampler described different colors from its canonical rule:
it placed random-colored border cells and interior 1/2 "mirrors", then forced
an interior 2 with an empty cell above it. The actual rule uses source 2,
mirrors 3/4, wall 5, and fixed output color 8. The original rationale for that
domain mismatch is unknown. Its self-check rejected canonical top/bottom
sources and admitted out-of-domain straight upward examples.

The repair constructs a route before adding objects. Core profiles retain
9x12 size and canonical colors; broad profiles vary dimensions without
restricting the exact override domain by difficulty. Reflection geometry uses
proper 3/4 swaps under quarter turns and axis reflection. Extra objects never
erase source or path objects. One active-wall distractor is deliberately placed
behind the wall, where it is unvisited by the true beam.

Four cyclic profiles are canonical exit, active wall, long route, and repeated
mirror orientations. `EXAMPLES_NEEDED=4` applies to all default lesson starts.
Every advertised axis is reconstructed from returned pixels. The only declared
incompatibility is `n_walls=0` with `wall_stop=1`; unknown axes, invalid values,
and noninteger numeric controls are rejected.

An initial repaired version passed the entire battery and a five-rival census,
but independent review found a surviving conditional wall shortcut: honor walls
only after the last mirror. The final active-wall profile includes an occluded
mirror and declares that rival explicitly. The failing regression and earlier
source are retained in the return, alongside the successful final checks.

`workspace/probe_laser_distribution.py` obtains labels through the public
Racket apply command. It reads actual rival/witness registries, verifies each
canonical shortcut on all four canonical pairs, and audits 100 overlapping
lessons per band with explicit unique-input counts. The task-local tests must
be invoked explicitly; the root pytest suite does not discover this folder.

### Limits and next decisions

- The sampler covers three route topologies and their spacings/orientations;
  it does not claim all accepted geometries, unlimited reflections, or all rivals.
- Normal samples have one noncorner border source and canonical input colors.
  Interior/multiple sources, corner precedence, unsupported colors, and cycles
  belong to separate robustness work; the tracer's cycle/original-grid semantics
  have focused tests, but those cases are not mixed into this curriculum.
- Four default demonstrations are required for the reported teaching schedule.
  Exact overrides can remove witnesses and must be re-audited when used in data.
- Passing checks does not grant training approval or establish a model score gain.
- The Racket authority and approval metadata were left unchanged. Existing
  archived text divergence is retained; selected authority checks pass.
## Current reviewer considerations

Source SHA-256: `d928e5dc3e7a968b3f52611bd41054ca71f71ab2e08b7ae23901613c8d037d3d`.

# Decisions for aba5e4aeb835

Assignment: `review-d83e98f966e5d70f`. Final generator SHA256:
`d928e5dc3e7a968b3f52611bd41054ca71f71ab2e08b7ae23901613c8d037d3d`.
The canonical Racket identity remains `17ecf3938e04`.

## G1 — Restore the actual task domain

The original sampler mixed two incompatible descriptions. Its summary used a
random-colored border source with mirrors 1/2, while the executed authority
uses source 2, mirrors 3/4, wall 5, and paint 8. The 1.3.0 repair merely forced
an interior 2 and cleared the cell above it. The original reason for using the
wrong palette and source location is unknown; the inline rationale only
explained avoiding identity outputs.

The final sampler uses a unique noncorner border 2 and canonical input colors
`{0,2,3,4,5}`. All four source sides are sampled. It constructs true mirror
routes before placing distractors. This makes reference execution exercise
reflection and stopping, while a trace-based validator accepts all four
canonical inputs. Border walls remain legal because a canonical input has one.

Rejected alternatives: changing the Racket authority to match the old generator
would change the task; retaining interior sources with a stronger nonidentity
filter would keep teaching the wrong input distribution; random palette
permutations would violate fixed color roles. Evidence: the five failing stages
in [the baseline battery](checks/before/checks/aba5e4aeb835_before_battery_summary.json)
and the [10 failing baseline regressions](checks/baseline-regressions.log).

## G2 — Construct the route before adding objects

Three route shapes provide different turn patterns: a fold with crossings, a
stair with repeated mirror orientations, and a weave with both equal and unequal
successive mirror types. Independently drawn coordinate levels vary spacing.
Quarter turns and axis reflection exchange mirror colors 3/4 correctly; odd
quarter turns exchange construction dimensions before honoring a final shape
override. Each route reaches two through five mirrors and paints at least one
zero. Extra mirrors and walls do not overwrite the source or earlier path.

This avoids rejection loops, post-hoc clearing, silently missing objects, and
count changes. The original approach could add an extra 2 or erase requested
objects when clearing the source's preceding cell. Exact controls now describe
observable output pixels: height, width, reached reflection count, unvisited
mirror count, wall count, source side, and active wall stop. Unknown keys and
invalid types fail. A requested active wall with zero walls is the sole declared
incompatibility.

Every legal control is available in every difficulty band. Difficulty changes
the unpinned size prior; it does not make an explicit dimension invalid. The
final override battery accepted 74,340 draws and recorded 90 declared
incompatibility rejections, with no findings or warnings across 827 cases and
74,430 total draws. See [override evidence](checks/after/checks/aba5e4aeb835_after_override_results.json).

## G3 — Require complete lessons to defeat named shortcuts

The default four-position schedule contains canonical exit, active wall, long
route, and repeated-mirror profiles. All four consecutive starts are exercised.
Two profiles preserve 9x12 canonical size and colors. Broad profiles retain
8..18 by 8..20 dimensions and zero through four distractors/walls. This keeps
canonical profile support in every band without replaying a canonical grid.

Four demonstrations, as declared by `EXAMPLES_NEEDED`, collectively distinguish
the following rivals: ignore mirrors; swap mirror meanings; ignore walls; stop
after three reflections; stop at repeated mirror orientations; honor a wall
only after the final mirror. The final three of those fit every usable canonical
pair, so canonical agreement alone cannot reject them. The lesson hook decides
from demonstrations only and does not inspect a query answer.

An intermediate implementation passed all 12 stages and a five-rival census.
Independent review then identified the conditional wall rival: every active
wall followed the last mirror, so ignoring it when another mirror lay beyond
was never tested. The [failing regression](checks/wall-gap-red.log) was retained.
The corresponding intermediate generator remains at
[prior-source-v1/generator.py](checks/prior-source-v1/generator.py), with its
after-v1 and lesson-probe receipts.

The final active-wall profile places one requested distractor beyond the wall.
It reserves enough interior space even at 8x8, protects previously traversed
cells, and leaves the mirror unvisited under the true rule. This supplies a
counterexample to the conditional wall rival without changing exact counts or
the authority. The final expanded probe verifies every fired witness against
actual Racket output, including 84 occluded-mirror draw uses across bands.

Rejected alternatives: unconstrained random layouts make crucial branches rare;
counting a wall or mirror without checking its effect does not establish a
teaching witness; relying on pooled witness frequency does not establish that
each lesson contains that witness; sampling only start index zero does not test
all schedule phases.

## Measurement and denominator choices

The final source-bound probe uses four seeds (`104729,130363,155921,196613`),
starts 0..24, and sample indices 0..28 in each difficulty band. Four consecutive
demonstrations plus one query form each lesson. This yields 100 lessons per band,
300 overlapping lessons, 348 draw uses, and 1,500 lesson pair uses. There are
115 distinct inputs per band and 183 globally distinct generated inputs, with
cross-band reuse. One repeated input occurs within each band's 116 draws.

Racket labels are deduplicated by exact input hash: 187 public executions cover
the generated inputs plus four canonical inputs, in batches of 64, 64, and 59.
All six rivals are rejected by all 100 demo sets per band. All 1,149 fired
witness claims agree with the corresponding Racket/rival disagreement. These are
finite observed results, not independent statistical trials or a universal
identification claim. See [final report](checks/lesson-probe-final/report.json),
[manifest](checks/lesson-probe-final/manifest.json), and the complete retained
draw/lesson rows in that directory.

## Limits and scope decisions

- Three constructive route shapes cover useful branches, not all accepted
  geometry or every possible shortcut. Paths beyond five reflections and
  generated cycles remain future work.
- The validator accepts a broader lawful task domain than the exact sampling
  templates. Accepted input does not imply nonzero sampling probability.
- Normal examples exclude corner/interior/multiple sources and unsupported
  input colors. Focused tracer tests cover cycles and original-grid reads;
  those tests do not claim these cases appear in the curriculum.
- Exact overrides can remove witnesses. The default four-demo guarantee must
  not be copied to arbitrary pinned mixtures without running the probe.
- No training run, Qwen benchmark, held-out competition score, or approval change
  occurred. Three root tests require unavailable optional Torch dependencies.
- Both independent audit targets are left unchanged. Their distinct issues and
  source-bound counterexamples are recorded in [AUDIT.md](AUDIT.md).
