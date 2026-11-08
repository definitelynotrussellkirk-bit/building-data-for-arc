# Workspace

`bbox_rival_probe.py` is a deterministic, source-bound authoring probe. It
iterates the selected generator's live `CANONICAL_SHORTCUTS` and
`LESSON_COMPETITORS`, verifies canonical fit, finds a generated disagreement
witness for each declared competitor, and checks every holdout rotation of
consecutive production windows over a bounded start range.

From the extracted packet root:

```sh
python3 run_with_racket.py \
  python3 generators/dc657616ec21/workspace/bbox_rival_probe.py \
  --seed 1701 --search-limit 32 \
  --out ../checks/bbox-rival-probe.json
```

The tool is a finite diagnostic against declared rivals, not a proof of unique
induction against undeclared hypotheses. The selected implementation remains
`../generator.py`; workspace files are never selected automatically.
