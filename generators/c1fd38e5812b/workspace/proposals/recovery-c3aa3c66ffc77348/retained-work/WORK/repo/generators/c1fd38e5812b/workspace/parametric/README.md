# Parametric compression family

This is a bounded extension of generator `c1fd38e5812b`. It varies two hidden
parameters:

- `compression_axes`: `both` (canonical), `rows`, or `columns`.
- `output_orientation`: `identity` (canonical) or `transpose`.

Every family member is materialized as a closed Racket `(rule! (lambda (g)
...))` program. `compression_family.py` uses the packet's `RacketBridge` for
all emitted demonstration and query labels. A Python implementation exists
only as an independent test oracle.

The episode builder greedily selects demonstrations until every rival setting
has produced a different output on at least one demonstration, then emits
exactly four distinct query inputs. Hidden parameters, Racket programs, query
labels, and rival evidence are written only to the private file. The public
challenge filename is the SHA-256 prefix of the exact visible public JSON.

Run from the packet repository root:

```bash
python3 WORK/repo/generators/c1fd38e5812b/workspace/parametric/compression_family.py \
  --out WORK/repo/generators/c1fd38e5812b/workspace/parametric/generated \
  --compression-axes both --output-orientation identity \
  --demo-count 4 --query-count 4

python3 review.py run python3 -m pytest -q \
  generators/c1fd38e5812b/tests/test_parametric_c1fd38e5812b.py
```
