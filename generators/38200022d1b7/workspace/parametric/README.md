# Point reflection with color binding

This opt-in prototype preserves the approved generator and the byte-for-byte
canonical Racket program. It adds one episode-fixed parameter, `mode`:

| Setting | Executed transformation |
| --- | --- |
| `all_sources` (default) | Keep every source and copy it through the unique gray pivot. |
| `nearest_color` | Find the color at minimum Manhattan distance from the pivot; copy every source of that color through the pivot. |
| `farthest_color` | Find the color at maximum Manhattan distance from the pivot; copy every source of that color through the pivot. |

In both alternatives, A scans individual source cells and binds the extremal
cell's **color**. B looks up all cells of that color, including remote,
disconnected cells, and copies them to their antipodes. B cannot choose its
source set until A has returned the input-dependent color. All originals and
the gray pivot remain. This is not a recoloring rule or an extremal-cell-only
copy. Tied extrema are legal only when all tied cells share one color; the
nearest and farthest colors must differ.

## Input and episode contract

`generate(seed, settings, demos=3, queries=4)` supports exact integer seeds
`0..2**63-1`, 2–6 demonstrations and 1–4 queries. Counts are independent. Every
returned input is distinct within its episode. Separate deterministic input
streams do not consult the hidden mode, so same-seed comparisons share inputs.

Every input has one gray pivot, 3–4 other colors, at least two cells per source
color, and 6–420 source cells. Every reflected target is blank and in bounds.
The executable grammar validator accepts 7..30 rows and columns. The normal
query profile visits 7x9, 13x17, 21x25 and 30x30, in seed-shuffled order. The
7x9 profile realizes six source cells. The 30x30 profile fills all 420 antipodal
pairs in a 29x29 lawful footprint, choosing one member of each pair; input
content actually spans that footprint. The one-cell margin follows from an
integer pivot on an even-size canvas, rather than padding a small scene.

The first two demonstrations are constructive witnesses. They change selected
colors and sides, include disconnected copies of the selected colors, place
the pivot off center, and make Manhattan extrema disagree with Euclidean,
Chebyshev, mean-distance and centroid-distance selections. Additional demos
come from separately seeded orbit constructions. The finite templates and
four query-size profiles remain distribution restrictions.

## Reproduce and extend

Run from the outer packet directory. The wrapper chooses this checkout's
Python/Racket environment and runs payloads in `WORK/repo`:

```sh
WORK/.venv/bin/python review.py run python3 \
  generators/38200022d1b7/workspace/parametric/prototype.py \
  --seed 0 --mode nearest_color --demos 3 --queries 4 \
  --out ../checks/38200022d1b7/new-materialization

WORK/.venv/bin/python review.py run python3 \
  generators/38200022d1b7/workspace/parametric/audit.py \
  --seeds 0 17 --demo-counts 2 3 6 \
  --out generators/38200022d1b7/workspace/parametric/evidence/new-audit

WORK/.venv/bin/python review.py task-tests 38200022d1b7 \
  --phase after --out ../checks/38200022d1b7-tests-new
```

Use a new output directory for each evidence-producing command. The
materializer checks all labels with protected Racket before writing anything.
Its private episode holds settings, programs and all labeled queries. The
public writer emits only demonstrations and the requested single query input;
the filename is the SHA-256 of the exact serialized visible bytes, including
the helper's trailing newline. Private metadata, answers and future queries
cannot alter that filename. A one-query episode has the same first turn as a
four-query episode with the same seed, mode and demo count. The consumer owns
answer-gated sequencing; this prototype provides projection, not a controller.

`audit.py` is a reusable, source-bound tool. It executes the declared alternatives
and a finite set of plausible shortcuts, retains exact Racket programs and
input/output bindings, and fails if a rival fits every visible demo but disagrees
on any query. Execution errors are failures, never evidence of distinguishability.
It also checks matching inputs across settings, four distinct queries, substantive
30x30 content, and exact public bytes. It does not prove universal identifiability.

The first audit found a real two-demo gap: this DSL's `/` uses integer division
on integer arguments, so two distinct means collapsed to the same score. The
second teaching scene now separates both exact and truncated means. The audit
executes separate exact/integer mean and centroid rivals. The retained minimal
pre-repair lesson is `evidence/integer-mean-counterexample.json`; the repaired
18-episode audit is `evidence/final-audit/audit.json` (672 protected executions,
zero remaining findings for the declared rivals).

The thin `adapter.py` and `promotion.json` implement native qualification.
`canonical.rkt` stores exactly the selected ledger string. A source inventory
and fresh qualification are required after changing any executable source;
passing local tests or a prior receipt does not accept new bytes. Reviewer
qualification and causal replay remain separate from owner acceptance and
training admission. See the current task notes and returned native receipts
for the exact evidence produced in this review.
