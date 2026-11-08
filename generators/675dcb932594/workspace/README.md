# Maze authoring probe

`maze_probe.py` is a bounded, standard-library diagnostic for this task. It
discovers its checkout or portable runtime with public `reviewer_support`, reads
the generator's actual `CANONICAL_SHORTCUTS` and `LESSON_COMPETITORS`, and reports
namespaced rival results without maintaining a second rival-name list.

From the repository root, with a **new** output path:

```bash
python3 generators/675dcb932594/workspace/maze_probe.py --seed 0 --per-band 200 --out maze-coverage-new.json
python3 -m pytest -q generators/675dcb932594/tests/test_maze_probe.py
python3 -m pytest -q generators/675dcb932594/tests/test_generator_675dcb932594.py
```

The probe also runs when invoked by an absolute path from another directory.
`--start-index` selects the first sample index; `--per-band` is bounded to
1..10000. An existing output file is refused to preserve prior evidence.

The report includes generator and rule hashes, exact seed/index/band ranges,
canonical fits for every declared shortcut, actual shapes and semantic profiles,
distinct-input counts, validator/strict-hook outcomes, connected-component
counts, shortest-path counts, horizontal/vertical move signatures, painted versus
preserved zeros, each rival's refutation count, first disagreements, and errors.
A single BFS retains every equal-distance predecessor; dynamic programming on
that DAG counts paths and move signatures without enumerating exponentially many
paths. This independent implementation does not use the generator's `_union_probe`
as its expected-output oracle.

**Label boundary:** this tool produces Python diagnostics, not Racket labels or
training data. Verify a proposed counterexample with the supported public command
from the review packet's WORK directory:

```bash
python3 run_with_racket.py python3 -m arcpuzzles apply 675dcb932594 --input ../checks/new-input.json --out ../checks/new-racket.json
```

Input may be one grid or `{"inputs": [grid]}`. The wrapper's payload cwd is
`WORK/repo`; its `../checks` paths deliberately refer back to WORK. The public
receipt binds the input, output, generator and selected rule. Canonical helpers
and the authoring probe expose reference information and must not be consulted
during a visible-only solve episode.

The review's final diagnostic covers seed 0, indices 0..199, all three bands:
600 successful draws, 200 distinct inputs per band, and 300/600 refutations of
each weighted-cost shortcut. Production lesson evidence is a separate Racket
census in the review ZIP; the input-level probe does not certify lesson assembly.
