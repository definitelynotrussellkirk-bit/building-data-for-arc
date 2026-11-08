# 2376352117fc — marker-vector translation

One blue (`1`) single-cell marker, one distinct red (`2`) marker, and one
4-connected green (`3`) motif containing 3–8 cells appear on a zero background.
Compute the displacement **from blue to red**. Translate every green cell by that
vector, recolor it cyan (`8`), and paint only the translated in-bounds cells on a
**fresh zero grid**. The original markers and green motif do **not** remain.

Clipping is per cell: the output can contain the full motif, a partial motif, or
no cyan cells at all. Existing input cells are not obstacles to output painting.
The Racket authority is unchanged. Its canonical fully clipped example is valid.

The selected generator is version `3.0.0`. Its five realized axes are `grid_h`
(7–18), `grid_w` (7–19), `motif_size` (3–8), `texture` (full/partial with or without
input overlap, or empty), and `vector_kind` (all eight compass directions).
Unknown axes and invalid values are rejected. Fixed colors encode semantic roles;
this is not a palette-permutation task.

Default generation cycles eight semantic profiles with a seed rotation. Every
three consecutive default samples contain full visibility, partial clipping,
and an input/target overlap. This distinguishes the declared finite rival set;
it is not a proof that every imaginable program is ruled out by three examples.
An explicit texture override intentionally replaces this default schedule.

Approval remains derived from current code and retained evidence, not this file.
