# Native connectivity family for `eefadafb2b7b`

This task-local adapter promotes one nearby, episode-fixed rule parameter while
leaving the production generator and canonical task unchanged:

- `connectivity=8` is the canonical/default setting. `program()` returns the
  exact canonical Racket bytes.
- `connectivity=4` changes only the component constructor from
  `(objects-8 cyan-mask 0)` to `(objects cyan-mask 0)`.

Both settings retain the same object roles and decision rule: identify the two
red `2×2` blocks, derive cyan components, and return `[[8]]` exactly when one
derived component touches the one-cell ring around both blocks.

## Native contract

`adapter.py` exports:

```python
program(settings: dict[str, int]) -> str
generate(seed: int, settings: dict[str, int], demos: int, queries: int) -> dict
```

The supported request space is:

- settings: `{"connectivity": 8}` or `{"connectivity": 4}`;
- demonstrations: 2 through 6;
- queries: 1 through 4;
- seed: plain nonnegative Python integer below `2**63`.

Inputs are independent of the hidden setting, demo and query prefixes are stable
under count changes, and every maximal episode contains four distinct queries.
The fourth query is a substantive `30×30` boundary-spanning case.

## Teaching and adversarial coverage

The first demonstration is a diagonal-only bridge that separates 8-connectivity
from 4-connectivity. The next demonstrations add a positive orthogonal bridge
and a negative bounding-box decoy. Every scene also contains:

- a moat-separated, 4-connected outer component whose bounding box spans both
  red rings, defeating component-bounding-box shortcuts; and
- a protected one-cell cyan component, defeating smallest-component-only
  shortcuts.

`prototype.py:self_review()` evaluates the selected rule against a finite set of
connectivity, ring-contact, bounding-box, extreme-component, and constant-output
rivals. This is a bounded adversarial check, not a uniqueness proof.

## Reusable audit

From `WORK/repo` in an extracted review packet:

```bash
python3 ../../review.py run python3 \
  generators/eefadafb2b7b/workspace/parametric/self_audit.py \
  --out generators/eefadafb2b7b/workspace/parametric/evidence/current
```

The audit runs protected Racket over both settings, seeds 0 and 17, demo-count
boundaries 2 and 6, and all four queries. It also checks matched inputs, prefix
stability, finite rivals, public/private projection, exact visible-byte IDs, and
the 30×30 stress case. Public artifacts contain one query at a time and exclude
settings, programs, query answers, future queries, and requested total counts.

Native qualification and the source-bound causal witness live under
`WORK/checks/eefadafb2b7b/`. They are reviewer evidence only: exact-source owner
acceptance and any training admission remain separate downstream decisions.
