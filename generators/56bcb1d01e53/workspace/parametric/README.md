# Proposed square-closure parameter

This task-local prototype keeps the original icon-completion family and varies
one episode-level rule parameter:

| Parameter | Allowed values | Canonical/default |
| --- | --- | --- |
| `square_closure` | `rotation`, `dihedral` | `rotation` |

`rotation` is the exact selected Racket authority. `dihedral` adds the four
reflection partners to the square branch while leaving bridge grouping,
rectangular reflection, and center filling unchanged. The parameter is chosen
once from the episode seed and held fixed for every demonstration and query.
Each materialized episode contains chiral square demonstrations that distinguish
both settings. Public episode JSON omits the hidden mode and query answer.

This is a **proposed prototype**, not a production API or approval. Production
`generate(...)` remains bound to the canonical rotation rule and `RULE_HASH`.

From the packet root, execute the prototype through the included runtime:

```sh
python3 review.py run python3 generators/56bcb1d01e53/workspace/parametric/prototype.py \
  --out ../checks/parametric/square-closure --seeds 0 1
```

The command writes exact Racket programs, public/private episodes, canonical
replay results, a shared distinguishing witness, source hashes, and runtime
identity under `WORK/checks/parametric/square-closure/`.
