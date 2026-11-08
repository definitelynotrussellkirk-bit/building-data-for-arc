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

`build_episode` exposes demonstration and query counts independently. The
retained command below exercises three demonstrations and four distinct queries
for each setting, executes every label through both exact Racket programs, and
checks each query against the declared rival using only the demonstrations:

```bash
python3 review.py run python3 generators/a631936f7715/workspace/parametric/verify.py \
  --seed 20261023 \
  --train-count 3 \
  --test-count 4 \
  --out ../checks/parametric-final/report.json \
  --artifact-dir ../checks/parametric-final/artifacts
```

Only `artifacts/public/` is model-visible. Each public filename is the SHA-256
of the exact canonical visible bytes it contains; hidden connectivity settings,
seeds, programs, and query answers are kept under `artifacts/private/`. Batch
rows are sorted by public ID and duplicate visible payloads are rejected before
any output directory is created.

This is a proposed prototype only. It does not alter the selected canonical
Racket authority, production generator API, or approval metadata. Retained
evidence covers two settings at one seed and one declared rival; it does not
prove identifiability against every imaginable rule or every possible count.
