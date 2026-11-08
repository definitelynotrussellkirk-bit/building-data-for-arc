# Proposed parameterized shear family

Status: opt-in prototype; no production selection, approval, or training admission.
Task `4326f5c2ded0`; original ARC family `training:423a55dc`.

## Rule and parameters

For every nonzero cell `(r, c, color)`, let `b` be the bottommost occupied row
across the whole input. Write that color at `(r, c + step * (b - r))` if the
column remains on the canvas. Start with a zero canvas of the original shape.
The original source cell is cleared. All colors and components share `b`.

| Setting | step | Status |
| --- | ---: | --- |
| left, stride 1 | -1 | Exact canonical default |
| left, stride 2 | -2 | Proposed variant |
| right, stride 1 | +1 | Proposed variant |
| right, stride 2 | +2 | Proposed variant |

The default returns the exact ledger program text, whose normalized hash is
`884d94dde3d6`. Alternate programs change only the displacement expression.
The program lookup refuses a changed or ambiguous canonical authority. Every
label executes in the supplied protected RacketBridge and must agree with an
independent Python diagnostic; there is no Python label fallback.

## Reproduce

From the outer extracted packet folder, with the packet runtime available:

```bash
python3 review.py run python3 generators/4326f5c2ded0/workspace/parametric/shear.py --all-settings --count 2 --seed 17 --train 3 --test 4 --out ../checks/parametric/new-episodes
python3 review.py run python3 generators/4326f5c2ded0/workspace/parametric/verify_boundaries.py --out ../checks/parametric/new-boundaries.json
python3 review.py run python3 -m unittest discover -s generators/4326f5c2ded0/tests -p test_parametric_shear.py -v
```

Use a new output directory/file. Runtime payload paths are relative to
`WORK/repo`; the `../checks` destinations are in `WORK/checks`.
The only Python requirements are the standard library and the packet runtime.
The unit suite has no pytest dependency and requires a real Racket executable.

Select one variant with `--direction right --stride 2`, or all four with
`--all-settings`. `--count` is episodes per setting. Counts are independent:
`--train 1 --test 4` is supported. `--height 30 --width 9` requests that exact
shape for every pair; either dimension may be overridden alone.

The Python API `build_episode(seed, settings=None, ...)` chooses one hidden
setting deterministically from the seed before producing labels. Its choice
is independent of requested pair counts. The CLI uses explicit settings and
defaults to the canonical one.

## Sampling and teaching checks

Each episode starts with a diagnostic demonstration: interior markers reveal
direction and stride, edges expose clipping, and row gaps and blank bottom
rows distinguish the global occupied-row anchor from competing anchors.
Additional scenes include multiple objects, edges, gaps, outlines, and tall
occupied spans. Default query sizes are 30x30, 24x27, 27x21, and 12x19; the
30x30 tall-span query occupies rows across its height.

All demonstration and query inputs in an episode are distinct. Sampling uses
local deterministic random generators and makes at most 256 attempts per
input. The supported generation envelope is height 8..30, width 9..30,
1..16 demonstrations, and independently 1..16 queries. Empty foregrounds,
noninteger values (including bool), ragged grids, and unsupported dimensions
or counts are refused. The standalone rule diagnostic accepts nonempty
foregrounds on rectangular 1..30 by 1..30 grids.

`lesson_audit` selects surviving rules from demonstration inputs and outputs
only. It considers all four settings and eleven named shortcuts: identity,
rigid shift, canvas-bottom anchor, top anchor, per-component anchor,
per-color anchor, occupied-row rank, wraparound, clamping, single-color-only
movement, and source retention. Query outputs are consulted only after
selection to determine whether surviving rules disagree on a query.
`build_episode` refuses query-relevant ambiguity within this finite set.
This is a declared-rival check, not a proof against every possible program.

## Public output and private evidence

`write_batch` uses the packet's `public_challenge_bytes` and
`public_challenge_id`. Each `public/<sha256>.json` contains only demonstration
inputs/outputs and query inputs. The filename hashes the exact visible bytes
written. Seeds, settings, programs, and query answers occur only in the
separate `private/<sha256>.json`. Batch order is sorted by public ID;
duplicate visible payloads are rejected before anything is written, and an
existing output directory is refused. The writer is a projection utility;
the CLI supplies it only with Racket-verified `build_episode` results.

Private records retain the setting, seed, complete matching Racket program,
program and source hashes, actual Racket pair count, and finite-rival audit.
The receipt deliberately marks the batch proposed and training_admitted false.

## Retained evidence

The return contains eight episodes (seeds 17 and 18 for each setting), with
three demonstrations and four queries each: 56 Racket-labeled pairs and 32
query answers. The 13-test unittest run also executes all four settings and
all 12 labeled canonical occurrences (six unique pairs).
The separate boundary verifier executes 114 Racket pairs: eight hand-derived
witness applications, 16 six-pair boundary episodes, and two five-pair
count-independence episodes. Exact results and commands are under
`checks/parametric/` in the return. Production batteries were not applicable
to this prototype-only change.
