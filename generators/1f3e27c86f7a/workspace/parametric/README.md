# Proposed payload-reflection episodes

This is a runnable, task-local **proposed prototype**, not a registered or
approved production rule. The parent is training task `40f6cd08`; the canonical
rule remains `a3f0a934419a`. The accompanying production change only rejects
lessons whose query branch was not demonstrated.

## Parameter and invariant reasoning

`payload_orientation` has two allowed values:

| Value | Executed behavior |
| --- | --- |
| `identity` (canonical default) | Return the exact original Racket program, byte for byte. |
| `mirror_lr` | Reflect the source template's interior columns before the existing proportional or edge-aligned sampling. |

Template selection, same-color target matching, source objects, border depths,
row mapping, alignment, and the no-template stripe fallback remain the same.
Reflection changes one Racket payload lookup from `(at g sr sc)` to
`(at g sr (- (+ ti-c1 ti-c2) sc))`. Reflecting the already scaled output would
be different at rounding boundaries; the independent literal test covers this.

The original generator uses row-striped payloads, which cannot reveal a
horizontal reflection. Prototype inputs retain its geometry and replace the
interior with four distinct, nonempty rectangular color regions. This makes the
parameter visible while avoiding accidental template components created by
irregular monochrome shapes. Inputs do not encode the selected setting.

An explicit setting stays fixed across every pair. With `orientation=None`
(CLI `random`), the deterministic episode seed chooses it once. Geometry,
colors, and placements may vary between pairs. All labels are executed by the
matching Racket program; there is no Python label substitute.

## Generate two complete examples

From the outer review directory, with enough free space to install the bundled
runtime, use a **new** output directory:

```sh
python3 review.py setup
python3 review.py run python3 generators/1f3e27c86f7a/workspace/parametric/prototype.py \
  --seed 17 --orientation both --demo-count 6 --query-count 4 \
  --out ../checks/parametric/new-examples
```

This writes one canonical-setting episode and one mirrored-setting episode:
six demonstrations and four distinct queries each. `--episodes N` generates
N episodes per requested setting, for `1 <= N <= 16`. `--difficulty` accepts
`easy`, `medium`, or `hard`; `--orientation` accepts `identity`, `mirror_lr`,
`both`, or `random`.

Demonstration and query counts are independent exact integers in `1..12`.
The default six demonstrations include all six branches. The first
proportional demonstration distinguishes the two parameter settings. With
fewer than six demonstrations, query branches are restricted to those actually
shown. For example, one demonstration supports four distinct proportional
queries; it does not claim all-branch coverage. All inputs are distinct across
both splits. Exhausting the finite sampling budget raises an error rather than
silently returning fewer or duplicated pairs.

## Verification and public export

`assess_episode` filters the two parameter alternatives using demonstrations
only, then checks each query input against the surviving predictions. It also
requires a changed demonstration of each query branch, refuting the corresponding
identity/skip-branch rival. Query labels are never read by this assessment.
A surviving alternative is acceptable when it predicts the same query output.

This establishes support against the declared rivals. It does not establish
uniqueness among all programs, or distinguish every possible alignment rival.

The export contains:

- `public/<sha256>.json`: exact `reviewer_support.public_challenge_bytes`, with
  demonstration inputs/outputs and query inputs only.
- `private/<same-sha256>.json`: labels, episode parameters, seed, source hashes,
  and scoped verification.
- `private/programs/<program-sha256>.rkt`: the exact executed rule text.
- `private/index.json`: sorted public identities and the private setting map.

Public filenames depend only on the exact visible bytes. Changing a private
seed, note, or query label cannot change the public bytes or identifier.
Duplicate visible payloads and nonempty destinations are rejected. Share only
the `public/` directory with a solving model. The writer projects supplied data;
it does not independently revalidate private labels, so use `build_episode`
or separately verify authored labels before exporting.

`evidence/manifest.json` is the source-bound authoring inventory consumed by
the existing priority reader. Its `current` classification concerns retained
authoring evidence; `variant_approved` and `training_admitted` remain false.
The retained example batch in `evidence/examples/` has two complete episodes,
twenty Racket-derived pair labels, and eight queries.

## Focused tests and original lesson counterexample

```sh
python3 review.py run python3 -m unittest discover \
  -s generators/1f3e27c86f7a/tests -p 'test*.py' -v
python3 review.py run python3 generators/1f3e27c86f7a/workspace/parametric/replay_lesson.py \
  --out ../checks/lesson-guard/new-racket-replay
```

The replay labels the exact seed-10 sequence: four stripe demonstrations and a
bottom-aligned query. An independently implemented stripe-only rival fits all
four demonstrations and fails the query. The repaired production hook rejects
that automatic lesson; explicit-count diagnostic use retains the rejection
reason. The retained witness is `../../counterexamples/branch-support/witness.json`
relative to this directory. Existing pointwise generation remains unchanged, so unsupported random
lessons can still be drawn and rejected. A supporting production schedule is
future work, separate from this prototype's branch-aware construction.

The 30 selected tests passed, including all four original canonical examples,
the literal reflection witness, six-branch/default counts, easy `1+12` and hard
`12+1` boundary counts, hidden-label independence, public export, and rejection
of cached compiler modules from another source tree. No full production battery
or corpus census is claimed. The packet's ordinary setup hit host disk exhaustion;
the recorded runs used the same hash-verified bundled Racket in temporary memory.
