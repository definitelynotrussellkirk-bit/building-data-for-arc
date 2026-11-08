# Reviewer workspace: e438ce3e02ce

`voronoi_probe.py` is an independent, generator-free nearest-seed oracle and
inspection CLI. It accepts a JSON grid (or `{"input": grid}`), reports seed
ownership, tie arity, Manhattan-vs-Euclidean disagreements, and disagreements
for the “ignore seeds after the first three/four” shortcuts. Add
`--emit-output` to include the intended Manhattan/tie-to-8 output.

```bash
python3 generators/e438ce3e02ce/workspace/voronoi_probe.py input.json --emit-output
```

The task tests import this oracle rather than trusting the generator's own
semantic helpers.
