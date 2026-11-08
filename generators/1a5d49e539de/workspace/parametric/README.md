# Proposed `symmetry_axis` prototype

This task-local prototype leaves the approved generator and canonical rule
unchanged. It varies one episode-wide semantic parameter:

- `symmetry_axis=left-right` — the original/default rule, using the exact
  canonical Racket source.
- `symmetry_axis=top-bottom` — the nearby variant, changing only the reflection
  used to decide which object is asymmetric.

For both settings, the reasoning structure is unchanged: split the shared-color
foreground into 8-connected objects in row-major discovery order, test each
object against the episode's reflection axis, select the first asymmetric
object, and return its tight crop. The parameter is selected deterministically
once from the episode seed and is fixed across all demonstrations and queries.
Candidate scenes are retained only when the alternative axis predicts a
different crop, so the demonstrations identify the chosen rule.

## Exact four-query replay

Run from the packet's outer extraction directory, using fresh output paths:

```bash
python3 review.py run python3 \
  generators/1a5d49e539de/workspace/parametric/prototype.py \
  --out-dir ../checks/parametric/symmetry-axis-replay \
  --public-dir ../checks/parametric/symmetry-axis-replay-public \
  --seeds 0 1 \
  --difficulty medium \
  --start-index 0 \
  --n-train 3 \
  --n-test 4
```

The retained seeds cover both parameter values. The writer executes every
selected and rival prediction with the bundled Racket bridge, writes full
private evidence, and writes only demonstrations plus answer-masked query
inputs to opaque public files. The submitted receipt used the same arguments
with `symmetry-axis-final` and `workspace/parametric/examples` as its output
paths.

## Verification

Use the packet's staged task runtime rather than importing the task tests from a
bare checkout:

```bash
python3 review.py run python3 -m arcpuzzles check 1a5d49e539de \
  --stage task_tests \
  --phase after \
  --out ../checks/parametric/task-tests-replay/result
```

The 41-test task run includes the 33 canonical generator regressions and the 8
focused prototype tests. Those tests pin the canonical rule bytes, check the
variant source, exercise deterministic sampling and retry boundaries, compare
both Racket programs with an independent Python mirror, require three
demonstrations and four distinct queries per episode, and verify public/private
projection and opaque visible-content identifiers.

The bounded adversarial helper can be replayed independently:

```bash
python3 review.py run python3 \
  generators/1a5d49e539de/workspace/parametric/adversarial_probe.py \
  --out ../checks/parametric/adversarial-replay/result.json
```

## Scope and limits

This is a proposed, unapproved extension. It does not alter production
`generate(...)`, the selected generator hash, the canonical rule, approval
state, or training admission. Evidence is finite for the retained settings,
seeds, and bounded search. Outside the retained unique-axis grammar, the two
rules may select the same first asymmetric object; such candidates are rejected
rather than treated as identifying examples.
