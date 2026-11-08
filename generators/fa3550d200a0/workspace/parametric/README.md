# Native quarter-turn family

Parameter: `quarter_turns ∈ {0,1,2,3}`. The default `0` program is byte-exact
canonical. Inputs come from the approved generator and are accepted only when
all four rotated target footprints remain inside the canvas and do not overlap.
The adapter computes claim labels with an independent Python transform; native
qualification replays every label under protected Racket.

```bash
python3 review.py run pytest -q \
  generators/fa3550d200a0/tests/test_parametric_native_adapter.py \
  generators/fa3550d200a0/tests/test_parametric_quarter_turns.py
python3 review.py run python3 -m arcpuzzles parametric qualify fa3550d200a0 \
  --seed 0 --seed 17 --demos 3 --queries 4 \
  --out ../checks/fa3550d200a0/qualification --summary
```

Sequential dependency: extract each matched outside piece's marker-relative
cell offsets, rotate that intermediate by the selected number of quarter-turns,
then stamp the resulting offsets at the same-colored marker inside the canvas.
