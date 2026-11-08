# `41a5c2fcf25a` — area-rank component recoloring

A contiguous legend of two to four distinct nonzero colors occupies the left prefix of row 0. Rows below contain the same number of separated cardinal components, initially color `8`. Rank components by area descending, breaking equal-area ties by top row and then left column; recolor rank `i` with legend entry `i`.

Generator version `3.0.0`; canonical rule hash `729bc9e3873e`.

The four-sample curriculum deliberately includes both canonical edge branches that the imported sampler omitted: equal-area ties and color `8` used as a legitimate legend color. It also makes area rank conflict with spatial order and keeps legend order distinct from numeric sort. Public exact axes are `grid_h=10..14`, `grid_w=11..16`, and `n_blobs=2..4`.

Portable tests, an independent oracle, an executable witness/rival contract, a retained joint counterexample, and source-bound lesson censuses accompany the generator. Approval remains catalog-derived from current source and retained evidence.
