# 0dba62203065

A zero-background grid has a **full header row** exposing colors 2–8. Its base
pattern is an ascending or descending cycle. Canonical-profile row-2 lessons
keep that cycle exactly; row-1 lessons swap one later header value above a real
object left edge with a non-anchor value while preserving header cells 0 and 1.
This forces solvers to read the actual lookup entry instead of reconstructing
the entire legend from the first two cells.

The body contains exactly three isolated blue (`1`) objects. For each object,
read the header color above the object's bounding-box **leftmost column** and
recolor the whole object uniformly with that color. Preserve the header and
background. The body's final column stays blank because the selected Racket
rule excludes that column from object extraction.

Easy defaults to ascending base cycles, medium samples either direction, and
hard defaults to descending base cycles; explicit direction overrides remain
exact. The generator schedules all three canonical `(height, width,
palette-size)` profiles in every difficulty band, alternates row-1/row-2 body
origins, and alternates canonical object sizes `(2,3,3)` with an extended
`(2,3,4)` profile. Every draw includes a shape that distinguishes
bounding-box-left from row-major-first-cell lookup. Every two consecutive draws
also include a lesson that refutes both the public-size threshold shortcut and
the cycle-reconstruction shortcut.

Kind: `per_puzzle`. Reviewed version: `3.2.0`. Rule hash: `75437b07b887`
(unchanged).
