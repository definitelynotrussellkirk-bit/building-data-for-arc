# Source-action parametric prototype

This separate prototype keeps the task's bracket interpretation and transparent
bitmap placement fixed while varying one hidden episode-level rule parameter:

| Parameter | Values | Canonical/default |
| --- | --- | --- |
| `source_action` | `move`, `copy` | `move` |

`move` is the exact canonical Racket source (after stripping only outer
whitespace). `copy` changes only the final source-erasure branch, so the bitmap
appears at the same destination but remains at its source. The setting is chosen
once per episode; public challenge files contain neither the setting, Racket
source, nor query output.

From the packet root, after `python3 review.py setup`, build fresh Racket-backed
evidence with:

```sh
python3 review.py run python3 generators/8a50bfdecd97/workspace/parametric/prototype.py \
  --base-seed 500 \
  --out ../checks/parametric/source-action-v1
```

The builder refuses to overwrite an existing evidence directory. It retains one
complete four-pair episode per setting, exact Racket receipts for both settings
on both episodes, public/private challenge separation, all four query rotations,
a cross-setting witness, source hashes, and explicit limitations. This is
prototype evidence only; it does not alter or approve the production rule.
