# Profile-source parametric family

This family preserves the exact canonical rule and changes one episode-fixed
choice: which anchor supplies each ordered profile used to select the crop.

- `blue_rows_red_cols` is the byte-exact canonical program. Blue supplies the
  ordered row counts; red supplies the ordered column counts.
- `red_rows_blue_cols` swaps those sources. Red supplies rows; blue supplies
  columns.

Every input is independent of the hidden setting and contains two distinct
candidate crops, one uniquely matching each setting. The anchors themselves are
cross-composed shapes: blue has the canonical target's rows and the swapped
target's columns; red has the swapped target's rows and the canonical target's
columns. Candidate copies of both anchors and two unrelated same-area shapes
make row-only, column-only, area, anchor-copy, color, and fixed-rank shortcuts
fail within the two-demonstration minimum. Target order alternates across pair
indices.

The family supports 2–6 demonstrations and 1–4 prefix-stable queries. The four
query roles are 12×18 ordinary transfer, 18×22 geometry variation, 24×26
boundary/content spread, and a substantive 30×30 stress scene with 2× scaled
components touching all four boundaries. The native owner qualifier re-executes
all claimed labels in protected Racket and fits declared programs to
**demonstrations only**.

Sequential dependency: step A finds the two anchors and derives the selected
ordered row/column profile pair from their input-dependent shapes. Step B cannot
choose the crop before that pair exists; it selects the unique candidate whose
profiles equal the intermediate. The retained causal witness replaces the
canonical intermediate with the swapped one on the same input and obtains a
different Racket output.
