# Proposed parametric lessons and replay tools

These opt-in prototypes do not change the selected approved generator, canonical
rule `54129d31ff5b`, approval records, or training admission. The default lattice
program is exactly the canonical program. The occlusion family is separate.

## Lattice connection: fixed axes per episode

`lattice_axes.py` exposes `axes=both|rows|columns`. On the existing two-by-two
cell lattice, connect same-color markers from minimum to maximum coordinates on
the selected axes; preserve other markers. Each episode fixes the setting and
retains its materialized Racket program. Colors, grid scale, marker positions
and disjoint-span grammar come from the unchanged source generator.

From the packet's outer directory, using new output directories:

```sh
python3 review.py setup
python3 review.py run python3 generators/3f26d45b9f51/workspace/parametric/lattice_axes.py --seed 17 --axes all --demo-count 2 --query-count 4 --out ../checks/axes-new
python3 review.py run python3 generators/3f26d45b9f51/workspace/parametric/lattice_axes.py --verify ../checks/axes-new
```

Demonstrations: 2..32; queries: 1..32 (default four). `--K` is 7..9 and
`--n-colors` is 2..4. Counts, seed and overrides require exact integer types.
`--max-attempts` is a global bounded sampling budget; exhaustion rejects rather
than emitting duplicate or partial lessons. Two successive teaching slots are
required to demonstrate triple-collinear connections on both axes. One demo is
explicitly unsupported; it can leave a nearest-pair rival alive on the other axis.

`lesson_certificate(demos, query_inputs)` does not accept hidden settings or
query answers. It filters three axis rules, three nearest-pair rules, identity,
bounding-box, dropped-unconnected-marker and fixed-divider-color rivals using
only demonstration outputs, then compares surviving predictions for every query.
Equivalent survivors are allowed. This finite check is not universal induction.

Every label comes from executed Racket and is cross-checked with Python.
Public IDs hash exactly the public challenge bytes. Exports sort by these IDs,
reject duplicate visible challenges, and keep seeds, programs, settings,
certificates and query answers under `private/`. Every input within an episode
is distinct. The all-settings batch deliberately reuses input geometry across
settings with different demonstration labels, for controlled comparisons.
The replay command checks exact public bytes/IDs, source and program hashes,
program execution, metadata/count types and demo-only certificates. Boolean
numeric substitutions, false approval status and stale source hashes reject.

## Separate occlusion/crop prototype

`occluded_rectangles.py` implements a bounded solid-outline mechanism inspired
by the public demonstrations of evaluation task `a6f40cea`. Reconstruct one
rear rectangle using exterior evidence and return the foreground frame's strict
interior. `paint=outline|filled` is fixed per episode. The outline mechanism
transfers; filled interiors are an authored extension. Multi-object and
alternating-color semantics are excluded. See `OCCLUDED_RECTANGLES.md` for the
exact grammar, context witness and observed global-parity discrepancy.

```sh
python3 review.py run python3 generators/3f26d45b9f51/workspace/parametric/occluded_rectangles.py --seed 701 --paint outline --n-train 2 --n-queries 4 --max-attempts 128 --out ../checks/occluded-outline-new
python3 review.py run python3 generators/3f26d45b9f51/workspace/parametric/occluded_rectangles.py --verify ../checks/occluded-outline-new
python3 review.py run python3 generators/3f26d45b9f51/workspace/parametric/occluded_rectangles.py --seed 702 --paint filled --n-train 2 --n-queries 4 --out ../checks/occluded-filled-new
```

Both prototypes require Racket. Neither substitutes Python outputs if the
runtime is unavailable. Only share `public/` when constructing answer-free
challenges; the parent batch includes private supervision.

## Focused verification

```sh
python3 review.py run python3 -m unittest discover -s generators/3f26d45b9f51/tests -p test_lattice_axes.py -v
python3 review.py run python3 -m unittest discover -s generators/3f26d45b9f51/tests -p test_occluded_rectangles.py -v
python3 review.py run python3 -m unittest discover -s generators/3f26d45b9f51/tests -p test_packet_preflight.py -v
```

The final review evidence lives in `WORK/checks/`. Red logs retain reproduced
regressions; later passing receipts identify final source hashes. Broader
production tests are outside this prototype-only change.

## Read-only packet preflight for future agents

`../packet_preflight.py` is a stdlib-only proposal. It streams all archive
payloads, verifies the WORK inventory and outer-entry hashes, rejects unsafe
paths/types and decompression limits, and estimates bytes plus file/directory
inodes before extraction. It does not extract, mount, write or execute payloads.

```sh
python3 WORK/repo/generators/3f26d45b9f51/workspace/packet_preflight.py /path/to/packet.zip /existing/destination
```

Exit codes: 0 verified with sufficient estimated capacity; 2 unsafe/corrupt or
inconsistent packet; 3 verified but insufficient bytes/inodes or read-only
filesystem; 4 destination/I/O failure. Hash consistency is not publisher
authentication, and capacity is a snapshot that excludes runtime and extra
filesystem metadata. Its source is task-local pending any shared-tool adoption.
