# Native parametric family

`finish_rule=pack_only` is the exact canonical stable row compaction.
`mark_vertical_contacts` consumes that packed intermediate and recolors every
packed nonzero cell having a packed vertical neighbor to color 2. Inputs are
matched across settings. Adjacent active rows occupy disjoint columns before
packing, so packing creates the contacts and mark-before-pack is observably
wrong. Every scene also contains a nonmonotone row-order witness; the query pool
has four distinct inputs and a dense 30x30 stress case.
