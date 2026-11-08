# 627260bf308f — Palette rank recolor

Version: **3.0.0**. Canonical rule pin: `088353dcd64f`.

Read nonzero palette entries in row 0 from left to right. Identify body color-8
components using four-connectivity, rank by occupied-cell count, and recolor
with the corresponding palette entry. Diagonal contacts do not merge objects.
The generator produces inputs only; canonical Racket supplies every training label.

Exact controls: `grid_h=8..24`, `grid_w=10..24`, `n_components=2..5`, and
`palette_order=sorted|unsorted`. Every joint combination is supported in every
band. Unknown controls, including the dead v2 aliases and texture controls,
now fail explicitly. Explicit integer controls reject coercion from bool,
float, or string. Row 1 is blank; body cells are 0/8; sizes and palette entries
are distinct. Tie behavior is outside this generator's domain.

Even indices supply compact disambiguating witnesses. Odd indices broaden
shapes, component counts, palette orders and dimensions. Three demonstrations
plus one query from consecutive indices remain distinguishing under any
single-pair holdout against the seven declared rivals. This is not a universal
induction guarantee and does not cover arbitrary downstream regrouping.

Task-local tests and `workspace/coverage_probe.py` provide replayable coverage
and rival checks. See the returned `REVIEW.md` and `DECISIONS.md` for exact
source-bound counts and limitations. Passing checks does not grant catalog
approval or training-safety approval.
