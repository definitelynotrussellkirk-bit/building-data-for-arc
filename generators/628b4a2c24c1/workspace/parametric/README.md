# Row-corridor sweep policy

This native prototype keeps the source puzzle's row seeds and color-8 walls and
adds one episode-fixed parameter:

| `sweep_policy` | Rule |
| --- | --- |
| `rightward` | Exact canonical authority: sweep each seed right to the nearest right wall, or the edge. |
| `widest_corridor` | Measure the nearest open corridor on both sides, then sweep into the wider corridor; ties go right. |

The alternate has a real sequential dependency. **A** locates the nearest left
and right walls (or boundaries) and measures the two gap lengths. The resulting
per-seed tuple `(left_stop, left_gap, right_stop, right_gap)` is the
input-dependent intermediate. **B** chooses left or right from those measured
gaps and paints only that corridor. The direction cannot be selected before A.

`generate(seed, settings, demos, queries)` supports 2–6 demonstrations and 1–4
queries independently. Inputs are setting-independent and prefix-stable. The
first two visible demonstrations jointly include wall-free rows, both direction
branches, an exact tie, multiple right walls, wall/edge conflicts and inactive
wall distractors. Four queries scale through 9×14, 16×22, 24×30 and 30×30; the
largest uses ten active rows across the full canvas.

`teaching_check` fits eight declared rivals to demonstrations only, including
the known shortcut that refuses to extend a row without a visible right wall.
This is finite evidence, not universal uniqueness. `public_challenge` reveals
one query at a time, and `export_batch` hashes exact visible first-turn bytes
while retaining all answers, settings, programs and future queries privately.

Native qualification and exact-source owner acceptance remain required. No
training admission is implied.
