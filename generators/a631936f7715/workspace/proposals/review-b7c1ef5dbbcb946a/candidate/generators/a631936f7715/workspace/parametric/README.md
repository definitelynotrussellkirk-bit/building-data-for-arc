# Proposed component-connectivity parameter

This task-local prototype keeps the canonical label-and-recolor rule and varies
one episode-constant parameter:

- `component_connectivity = 4` — canonical/default; magenta components use
  orthogonal connectivity.
- `component_connectivity = 8` — proposed variant; diagonal magenta contact
  joins components. Label lookup remains orthogonal in both settings.

Every retained pair contains two magenta dominoes that touch only at a corner
and exactly one label across that pair, so the settings execute visibly
different transformations without label-order ambiguity. A separate labelled
component and isolated marker preserve the original object roles.

Demonstration and query counts are independent. This command writes three shared
rule demonstrations and four distinct queries for each setting, executes every
pair through both exact Racket programs, and checks that the demonstrations alone
select one declared setting before query labels are inspected:

```bash
python3 review.py run python3 generators/a631936f7715/workspace/parametric/verify.py \
  --seed 20261023 \
  --n-train 3 \
  --n-test 4 \
  --out ../checks/parametric-reconcile/report.json \
  --artifact-dir ../checks/parametric-reconcile/materialized
```

Public challenges are written under `materialized/public/` as
`challenge-<sha256>.json`. The file bytes and digest use `reviewer_support.public_challenge_bytes` and
`public_challenge_id`: only visible demonstration inputs/outputs and query inputs
participate. Hidden settings, seeds, Racket text, sampling metadata, and query
answers do not participate. Setting-linked programs and
complete episodes stay under `materialized/private/`, with the mapping retained
only in the private manifest.

The witness sampler has exact finite support of 1,680 inputs: 210 ordered triples
of distinct label/control/marker colors times eight dihedral transforms of one
7×7 role template. Requests above that bound fail instead of cloning examples.
This is a proposed prototype only. It does not alter the selected canonical
Racket authority, production generator API, or approval metadata.
