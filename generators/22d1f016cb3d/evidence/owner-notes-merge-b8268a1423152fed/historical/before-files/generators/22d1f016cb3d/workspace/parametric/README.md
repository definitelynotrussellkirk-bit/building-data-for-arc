# Boundary-palette prototype

Status: **prototype**, separate from the canonical repair and not approved for production.

The bounded hidden parameter is `boundary_palette`:

- `ends1_edges4` — canonical/default: color zero-opposing-pair cells 1 and exactly-one-opposing-pair cells 4.
- `ends4_edges1` — proposed variant: swap those two output colors.

The input scene, color-5 source cells, non-5 cells, and color-2 interior class are unchanged. The palette is selected once from the episode seed (`ends1_edges4` for even seeds, `ends4_edges1` for odd seeds) and held fixed across four demonstrations and one query. Public files retain labelled demonstrations but omit the parameter, Racket source, and query answer.

From the outer extraction directory, execute both exact Racket rules and regenerate retained evidence:

```bash
python3 review.py run python3 \
  generators/22d1f016cb3d/workspace/parametric/prototype.py \
  --out ../checks/parametric/boundary-palette-evidence.json \
  --write-public generators/22d1f016cb3d/workspace/parametric/examples
```

Run focused tests:

```bash
python3 review.py run python3 -m pytest \
  generators/22d1f016cb3d/tests/test_parametric_boundary_palette.py -q
```

Retained complete programs are `racket/ends1_edges4.rkt` and `racket/ends4_edges1.rkt`. The default file is byte-for-byte the canonical ledger source. Evidence is bounded to canonical seed 18 and swapped seed 19; it is not a claim that this prototype is approved or excludes every undeclared rival rule.
