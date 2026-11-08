# Reusable contract probe

From an extracted packet root:

```sh
python3 run_with_racket.py python3 generators/2ab8c1aaa3e2/workspace/probe_contract.py --out ../checks/contract-probe-new.json
python3 run_with_racket.py python3 -m arcpuzzles check 2ab8c1aaa3e2 --stage task_tests --timeout 600 --phase after --out ../checks/task-tests-new
```

The first command uses portable `reviewer_support` canonical readers, iterates
the actual three rival declarations rather than a copied rival-name list, and
checks every overlapping four-draw start in short sequences, every held-out
query position, RNG replay, input purity, exact dimensions/counts, and closed-form
joint override feasibility. It retains exact counterexamples and source hashes.
It refuses an existing output filename so failures are not overwritten.

Default population: seeds 0..9, indices 0..29, easy/medium/hard; starts 0..26,
three demonstrations plus one query. There are 900 draw positions, 810 overlapping
windows and 3,240 query rotations, not 810 independent lessons. This source
produced 700 unique input grids and 300 strict core draws in that population.
The joint probe uses seed 409, indices 0..2, all three bands, h in {4,22},
w in {4,20}, p in 1..12 and k in 1..9: 3,888 combinations, 1,998 accepted exact
and 1,890 structured impossibility rejections. These are grid-size corners,
not every interior h/w pair.

Use `--seeds`, `--samples`, or `--skip-joint` for a different bounded population.
The oracle is independently written Python diagnostic code. Authoritative
Racket validation is the public `lesson-census --per-band 100 --rotate-query`
and `arcpuzzles apply` evidence, retained separately in the return.

For a compact four-rival counterexample, generate seed 0, index 1, easy,
`grid_h=4, grid_w=4, pairs=2, n_distinct_colors=2`. The return includes its
actual public-API Racket output under `checks/audit/2ab8c1aaa3e2/`.
