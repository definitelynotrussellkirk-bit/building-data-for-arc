# Proposed minimum-anchor-area family

This is a task-local prototype for `a2e8d5ad83e5` (training family `e9bb6954`).
It adds one rule parameter, `minimum_anchor_area = 4 | 9 | 16`. The default `4`
is the exact canonical Racket text. Each alternative changes only the numeric
size predicate in that text. Production `generator.py`, canonical rules,
approval records and frozen examples are untouched.

## Meaning and teaching

The shared reasoning is: find four-connected same-color filled components,
select those meeting the area threshold, find each bounding box's floor center,
extend its complete row and column, and clear cells hit by distinct colors.
Multiple hits of the same color do not cancel. Unselected objects and distractors
remain as input except where a selected cross overwrites them. The reference
also supports filled rectangles; the episode sampler deliberately uses squares.

One setting is fixed across every demonstration and query. Seeded inputs and
retry decisions are matched across all settings. The first demonstration has
2x2, 3x3 and 4x4 anchors. The sampler executes all three rules and accepts that
demonstration only when their outputs are pairwise different. Rule selection
uses demonstration outputs only. The certificate covers exactly these three
thresholds; it is not proof of uniqueness among arbitrary programs.

The default three demonstrations are mixed sizes, two same-color 4x4 anchors,
and two distinct-color 4x4 anchors with a shared center row. Four queries use
mixed sizes, a 2x2/4x4 pair, two distinct-color 4x4 anchors sharing a center
column, and two same-color 4x4 anchors. The large-pair profiles are necessary:
the production sampler otherwise has at most one area-16 anchor. These new
profiles expose collision and non-cancellation behavior at every threshold.
They are sampled for all settings, not selected using the private rule.

Demonstration and query counts are independently supported in `1..8`; the
default is `3/4`. One demo identifies the threshold, while the additional
default demos expose the shared collision behavior. All inputs within an
episode are distinct. The sampler uses at most 64 tries per requested input and
fails explicitly without a partial episode. Standard medium profiles are
14..21 in each dimension; large-pair profiles are 20..26. Exact 30x30 coverage,
an all-seeds guarantee and measured learning benefit are not claimed.

## Generate paired examples

Run from the outer extracted packet directory. Payload paths are relative to
`WORK/repo`; use a new output directory on every run.

```bash
python3 review.py run python3 \
  generators/a2e8d5ad83e5/workspace/parametric/prototype.py \
  --seeds 0 17 --thresholds 4 9 16 --demo-count 3 --query-count 4 \
  --out ../checks/parametric/threshold-replay
```

This emits six complete episodes. Every label is executed through the matching
Racket source; there is no Python label fallback. `generate_episode` also accepts
an explicit `input_seed` for comparisons across different episode seeds. If
`settings` is omitted in that Python API, `seed % 3` chooses one threshold once.
Seeds and input seeds are exact integers in `0..2**63-1`; booleans, floats and
numeric strings are rejected, as are unsupported settings/counts.

Give consumers only `public/`. Each filename is SHA-256 of the exact visible
JSON bytes written by `reviewer_support.public_challenge_bytes`. Public content
contains demonstration inputs/outputs and masked query inputs only. Settings,
seeds, source hashes, Racket programs, certificates and query labels live under
`private/`. Changing hidden metadata cannot change a public name. Duplicate
visible payloads and malformed grids are rejected before creating the output.
Existing destinations are refused. The private completion manifest is written
last; an I/O interruption can leave an incomplete directory without a manifest.
The serializer does not re-execute labels; generation and qualification do.

## Focused checks and qualification

No extra Python test dependency is needed beyond the packet's declared runtime:

```bash
python3 review.py run python3 \
  generators/a2e8d5ad83e5/tests/test_parametric_threshold.py
python3 WORK/check_public_exports.py \
  WORK/checks/parametric/threshold-replay/public --demos 3 --queries 4
```

The focused tests cover canonical bytes, reference execution, exact threshold
boundaries, same-color and distinct-color collisions, strict types/counts,
matched inputs, finite-rival identification, labels and export boundaries.
Source-bound retained evidence is in `evidence/current/`; the inventory is
`evidence/manifest.json`. The original packet additionally retains independent
boundary witnesses and replay under `WORK/checks/semantic-review/`.

`adapter.py` exposes the native `program(settings)` and
`generate(seed, settings, demos, queries)` interface. `promotion.json` declares
the three bounded settings and separate count limits. After any source/test
edit, rerun focused checks and refresh the inventory through the native
`parametric manifest` command, supplying its exact previous hash when replacing
an existing inventory. Fresh qualification can then be run from the outer root:

```bash
python3 review.py run python3 -m arcpuzzles parametric qualify a2e8d5ad83e5 \
  --seed 0 --seed 17 --demos 3 --queries 4 --timeout 120 \
  --out ../checks/parametric/threshold-qualification-replay
```

Qualification re-executes labels and demonstration-only identification in a
separate protected Racket worker. Its exact saved result is authoritative for
that run. Qualification is not owner acceptance: no `parametric accept` command
is part of this review, and no variant or trajectory is admitted to training.
