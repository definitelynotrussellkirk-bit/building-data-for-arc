# Allocation quality — ticket-f0ed5197c9504860

**Status: completed bounded assessment and one source-bound Racket probe.** No
generator, draw policy, catalog weight, approval, or training mixture was changed.
The proposal below is an experiment, not a production allocation decision.

## Current draw and context

The packet's main authoring draw is uniform over 500 IDs, so each ID has a
conditional probability of `1/500 = 0.2%`. Packet inclusion priority does not
reweight that draw. The independent public-evaluation focus fires with probability
1/10 over 120 anchors and explicitly leaves main-target selection uniform. All
three sampled catalog records have `mix_weight = 1.0`; approval filtering still
changes which records are eligible for training. The supplementary
`allocation_quality` ticket weight is 10 of 105 total heuristic weight units, and
the manifest labels those weights “initial heuristics, not measured optimal
allocation.”

`TRAINING-CONTEXT.md` is a dated October 23, 2026 r6 snapshot, not a measurement
of the current packet. It reports 18,852 accepted episodes from 1,558 generators,
four-query defaults, and only 7.3% of ARCpuzzles-export outputs with a side at
least 20 versus 47% in public evaluation. It also warns that old ID-only mastery
labels can be stale after source changes and that high loss alone is not a defect.

## Ticket-seeded sample

The pinned primary is `1bfb2ef9ca71`. Two peers were selected without looking at
probe outcomes using
`random.Random(int(ticket_seed,16)).sample(sorted(main IDs excluding primary),2)`:
`27c1546d634f` and `28e5fbc279ab`. `comparison_selection.json` retains the exact
seed, 499-ID universe hash, and ordering. Every sampled source hash matches the
packet manifest and current review index.

| Generator | Current evidence and teaching | Representation / estimated review cost |
| --- | --- | --- |
| `1bfb2ef9ca71` | Approved repair, no unresolved audit, 3 exact controls, 7 tests, 3-demo schedule, one canonical-fitting rival, reusable probes. Retained source evidence reports 600/600 strict draws, 300 lessons and 1,200 query rotations without declared-rival ambiguity. | Hollow-rectangle completion, same-size output, max side 14. Low incremental review/Racket cost, but it cannot improve the documented side-20–30 gap. |
| `27c1546d634f` | Unverified, zero tests, no semantic lesson contract, and two unresolved source-bound audits. Those audits report perfect-frame/largest-object shortcuts over 600 sampled draws plus dead or misleading controls. | Hole-count crop is a useful output-smaller skill, max side 18, but current repair/rejection/ambiguity cost is high. Do not allocate volume before the retained findings are resolved. |
| `28e5fbc279ab` | Approved repair, no unresolved audit, 5 test files / 28 tests, 3-demo schedule and seven declared rivals. Retained evidence reports 1,200 unique draws, explicit largest-green witnesses, and complete lesson probes. | Template extraction/stamping with same-size outputs and max side 20. Broader and more expensive than the primary, but currently the only sampled approved family that reaches the large-side threshold at all. It still does not cover sides 21–30. |

The sample contains only per-puzzle bank families. ARC-GEN and RE-ARC were not
sampled, so this ticket makes no source-library ranking or volume recommendation
for them. Their fresh-eight-draw behavior in the dated training context remains a
coverage gap in this comparison.

## Executed probe

The single targeted command completed with exit code 0 in 3.865 seconds. It used
the pinned `1bfb2ef9ca71` source and canonical Racket rule to materialize three
consecutive demonstrations and four consecutive queries at hard difficulty. All
seven inputs were distinct and passed `self_check`; all seven protected Racket
labels matched the independent Python mirror. The demonstrations included both
schedule profiles, refuted `fixed_height_three`, and left no per-query
identifiability error. Observed maximum side was 14, confirming rather than hiding
the representation limit.

Packing four queries behind three demonstrations uses seven labelled grids,
versus sixteen labelled grids for four separate one-query episodes with the same
three-demo requirement: a 56.25% label-count reduction. This is arithmetic only;
it is not evidence of equal token cost, wall time, gradient value, or model gain.
Exact source/runtime identities and the private replay episode are retained in
`probe_result.json` and `private_episode.json`.

## Alternative allocation and bounded stopping rule

**Estimated alternative:** retain 80% of the current uniform authoring/Racket
budget and reserve 20% for an evidence-gated representation stratum. A candidate
enters that stratum only when its current source is approved, exact controls are
observable, a three-demo lesson refutes declared relevant rivals, four distinct
queries can be materialized, and at least one requested output side is 20–30.
Within this three-record sample, `28e5fbc279ab` is the only provisional candidate,
and only at side 20; `1bfb2ef9ca71` remains a high-quality uniform candidate but
is not a large-grid candidate; `27c1546d634f` is repair-only. The 80/20 split is a
hypothesis chosen to preserve broad uniform coverage while making the deficit
measurable, not a measured optimum.

Run a matched, source-bound pilot capped at 30 generators and eight attempted
3-demo/4-query episodes per generator. Use the same fixed generator set for the
uniform arm and the gated arm; execute every accepted label in protected Racket.
Measure accepted distinct four-query episodes per 1,000 labelled cells and per
minute, side-20–30 share, rejection rate, duplicate-input rate, and surviving
named-rival rate. Stop immediately for any source/rule drift or Racket/Python
label disagreement. Reject the alternative if it fails to raise side-20–30 share
by at least 10 percentage points, if quality-adjusted accepted episodes per cost
do not improve, or if rejection, duplication, or ambiguity worsens by more than
2 percentage points. Keep model training and global weight changes outside this
pilot; model benefit remains unknown until a separately matched experiment.

Evidence: `inspection.json`, `comparison_selection.json`, `allocation_probe.py`,
`probe_result.json`, `private_episode.json`, and `command.json`.
