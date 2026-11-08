# 65b59efc parametric workspace

Settings: `binding_mode=self|next_token`. The canonical copy is
`canonical.rkt`; `adapter.py` returns that exact text for the default.

Focused checks from the repository root:

```bash
PYTHONPATH=shared/runtime:src pytest -q generators/public_eval_65b59efc/tests
python3 generators/public_eval_65b59efc/workspace/parametric/decoder_inspect.py \
  --seed 17 --sample-index 3 --out /tmp/decoder-inspect.json
```

The inspection output exposes parsed template identities, macro tokens, panel
owners, palette bindings, and outputs under both settings without requiring a
visual guess.
