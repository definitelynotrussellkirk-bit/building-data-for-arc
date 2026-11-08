# Fill then select the most-bridged component

This native prototype keeps `mode=fill_only` byte-for-byte equal to the canonical
rule.  The alternative `mode=select_most_bridges` performs the canonical fill as
step A, then uses the newly inserted orange bridge cells to select a completed
6/7 component and recolors that component cyan as step B.

The sampler is independent of the setting.  Every input contains several
separate completed chains with distinct bridge counts, while a lower-bridge
component is deliberately larger than the winner.  This rejects fixed-location
and largest-object shortcuts.  Demonstration winners move across the canvas,
and
the four query profiles culminate in a 30×30 grid with six components spanning
the canvas.

From the packet root:

```bash
python3 review.py run pytest -q generators/0a0dded71c43/tests/test_parametric_bridge_selection.py
python3 review.py run python3 -m arcpuzzles.review_base_preflight 0a0dded71c43 \
  --out ../checks/0a0dded71c43/qualification
```

This directory is authoring evidence only.  Owner source review, native
qualification and exact-source acceptance remain separate; training admission is
false.
