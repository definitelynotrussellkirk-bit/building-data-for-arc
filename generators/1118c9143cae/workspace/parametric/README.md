# 1118c9143cae echo-scope family

This proposal keeps the exact selected rule as `echo_scope=all` and adds one
input-dependent alternative, `echo_scope=rarest_color`.

For the alternate rule, **Step A** counts every present nonzero color and emits
the unique least-frequent color. The intermediate is that color value and its
source-cell set. **Step B** preserves the input and adds 180-degree echoes only
for cells in that selected set. Step B therefore cannot know which cells to
echo until Step A has inspected the current input.

Every admitted scene has one two- or three-cell rare color that changes across the core demonstrations, no singleton colors, a
separate unique most-frequent color, and first/last/minimum colors that are not
the rare color. The first two demonstrations refute the alternate setting plus
fixed-minimum, first/last-visible, singleton-only, most-frequent, horizontal,
vertical, rotate-only, and identity shortcuts. The four queries include a
substantive 30x30 boundary case. Inputs are generated independently of the
setting, so same-seed episodes are byte-identical across both rules.

The adapter emits deterministic Python claim labels. Native qualification must
re-execute both programs with the protected Racket runtime. This proposal is not
owner acceptance or training admission.
