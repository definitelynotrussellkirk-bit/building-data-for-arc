# Public parent 35ab12c3: angular edge completion and translated shadows

The canonical rule orders each non-background color's original cells by angle
around their centroid. Consecutive angular neighbors are joined only when they
share a row, column, or 45-degree diagonal. A singleton color adjacent to one
other original color then copies that target's **completed** cells by its
marker-to-anchor offset, painting background only.

`edge_mode=all_8` is byte-identical to the authored canonical reference.
`edge_mode=orthogonal` disables diagonal edge completion while preserving the
same completion-then-shadow dependency. The deterministic sampler supports two
to six demonstrations and four distinct queries, with a substantive 30x30 case.

Independent review found that the original two-demo sampler allowed a convex-
hull shortcut to fit both demonstrations while failing a query. The first
teaching profile now includes an interior angular-chain motif, repairing the
hole without increasing the minimum count. A 32-seed audit tests six named
rivals, both settings, public privacy, query stability, and selected labels
through protected Racket. The official three demonstrations and test gold all
match the authored reference.

The source-bound authoring preflight and causal witness are reviewer evidence,
not owner registration, native qualification, acceptance, or training admission.
