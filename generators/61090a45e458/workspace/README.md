# Workspace

The selected implementation is `../generator.py`.

## `shortcut_probe.py`

Replays the generator's actual `CANONICAL_SHORTCUTS` and
`LESSON_COMPETITORS` declarations. It verifies canonical fit, saves an exact
generated disagreement witness, checks consecutive three-example production
lessons, and rotates each scheduled example into the query position.

From the extracted packet root:

```sh
python3 run_with_racket.py python3 \
  generators/61090a45e458/workspace/shortcut_probe.py \
  --starts 30 --seeds 17 808 5150 --assert-clean \
  --out ../checks/shortcut-probe.json
```

The report's labels use an independent Python implementation. Use the shared
`arcpuzzles apply` command for a hash-bound Racket output on a retained witness;
the normal `rule_smoke` and `authority_sync` gates check rule binding separately.
