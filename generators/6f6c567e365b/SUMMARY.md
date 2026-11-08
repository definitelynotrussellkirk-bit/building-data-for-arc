# 6f6c567e365b — Cumulative Transform Script Gallery

The first row is a left-to-right script of nonzero transform keys (`1` rotate clockwise, `2` rotate 180°, `3` flip left/right, `4` flip up/down). The nonzero content below that row is cropped to its bounding box. Starting from the crop, apply each key **cumulatively** to the previous state, then gallery the original state and every successive state horizontally with one background column between states.

The repaired generator uses asymmetric connected multicolor motifs, exact dimension/key/palette controls, and rejects unknown or conflicting overrides. This prevents the historical “ignore the script” and independent-transform shortcuts.

The task-local parametric family has two settings:

- `cumulative`: the byte-exact canonical program.
- `final_cue_projection`: execute the whole script, read the first row-major nonzero color in the final state, mask the original crop to that input-derived color, then replay the cumulative script and gallery the projected states.

Both settings support 2–6 demonstrations and exactly four independent queries, including a lawful 30×30 input whose output remains within ARC dimensions.
