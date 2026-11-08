# Walker turn direction — proposed prototype

This task-local extension adds one semantic parameter, `turn_direction`, with
exactly two values: `right` (the canonical default) and `left`. It is **prototype**
evidence, not a production API, an approval, or a training-admission claim.
The production generator and pinned canonical rule remain separate.

## Meaning and invariant reasoning

Every bottom-row red cell starts an independent walker. The walker prefers an
upward move whenever the cell above is not gray. If gray blocks upward motion,
it tries one horizontal step in the episode's fixed direction. It stops on the
top row, at the corresponding side boundary with upward motion blocked, or when
both legal options are blocked. Visited cells become red; other cells keep their
colors. Each walker reads the original input, so painted red paths do not become
new obstacles or starting points.

`materialize_rule()` returns the exact canonical program text for `right`.
`left` conjugates that same program with horizontal reflection before and after
execution. Reflection preserves rows, upward preference, gray obstacles, start
colors, and stopping conditions; it converts only right movement and right-edge
stopping into left movement and left-edge stopping. The included bridge executes
both programs; no Python rule mirror supplies episode labels.

## Input constraints and deterministic episodes

`sample_input(seed, sample_index, turn_direction, difficulty=..., **overrides)`
passes sampling controls to the selected generator. Both `scene_profile` and
`route_layout` (`canonical` / `procedural`) are supported. For left episodes the
sampled grid is reflected. This retains the original three disjoint routes,
turn counts, terminal rows, dimensions, gray mass, and palette in the chosen
orientation; the horizontal ordering of the three roles is reversed. The
canonical validator is applied before reflection. Left grids are prototype
inputs, not a claim of membership in the canonical production profile.

`parameters_for_seed(seed)` chooses right for even integers and left for odd
integers, once per episode. `make_episode` can also receive an explicit allowed
direction; it never resamples direction between pairs. Defaults are three
training pairs and two queries. Candidate inputs are deterministic, distinct,
and bounded to 256 proposals. The first accepted demonstration must produce
different Racket outputs under the two settings. All demonstrations are checked
against both declared parameter rivals, and construction fails unless only the
chosen setting survives. No claim is made about other possible rules.

`public_challenge` returns only `train` input/output pairs and `test` inputs.
Parameter values, seed, reference code, rival results, and query answers are
retained only in the private episode and receipt. Distribute the challenge files
alone when presenting a puzzle. The evidence directory also deliberately
contains private authoring material.

## Exact runnable commands

Run from the outer packet directory. The payload runs from `WORK/repo/`.

```sh
WORK/.venv/bin/python review.py run /workspace/scratch/341195387165/packet/WORK/.venv/bin/python -m pytest generators/45922a9666b2/tests/test_parametric_walkers.py -q
WORK/.venv/bin/python review.py run /workspace/scratch/341195387165/packet/WORK/.venv/bin/python generators/45922a9666b2/workspace/parametric/prototype.py --output /workspace/scratch/341195387165/packet/WORK/checks/parametric
```

When the packet is moved, replace the absolute interpreter and output paths with
the corresponding paths in that extraction. Runtime and dependencies must be
prepared using the packet's supported setup flow. In repository layout the
prototype supplies a minimal local `scripts` package search path pointing to
`shared/tools`, which the official rule wrapper requires; exported runtimes
already provide that package. No staged dependencies or shared-code edits are used.

## Retained evidence

`WORK/checks/parametric/receipt.json` records the exact invocation, runtime
identity, source and artifact hashes, canonical comparisons, profile/layout
comparisons, episode seeds, bounded rivals, and limitations. `right.rkt` and
`left.rkt` contain the materialized programs; their file hashes include the final
newline, whereas `program_sha256` hashes the exact program string in the private
episode. `distinguishing-witness.json` holds one lawful input and both executed
outputs. `private-episode-0.json` and `private-episode-1.json` retain complete
labeled episodes; `challenge-0.json` and `challenge-1.json` omit all private fields.
`tdd-red.log` preserves the expected missing-implementation failures before code
was written; `tdd-green.log` records the final focused tests. Earlier implementation and
30-second bridge-startup failures are retained in the numbered attempt logs.
Focused tests allow 120 seconds for bridge startup; evaluation limits remain
unchanged. Receipt artifact hashes cover only completed generated JSON/Racket
files, avoiding still-open process logs.

Tests cover canonical-label execution, exact default source, forced turns,
upward preference, boxed/top/left-edge stopping, reflected profile constraints,
determinism, visible direction identifiability, and the public/private boundary.
These tests concern the prototype; canonical repair coverage is tracked
separately. The finite sample covers the four published profiles and two episode
seeds. No larger-grid coverage is claimed. Mirroring inputs can correlate input
geometry with direction, and these checks do not establish freedom from every
possible shortcut.
