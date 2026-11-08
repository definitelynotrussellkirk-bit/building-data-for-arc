# 7f181d3b0012

Small colored grid (canonical: 3x3 binary {0,1} with 2, 4, or 5 one-cells, UD- and LR-asymmetric; generated: h 1..15 x w 2..30, 2-6 colors, with an explicit ~30% canonical-family mixture in default draws plus small/large generalization branches). Rule: output is a fresh grid of 2H x W. Top half = input verbatim. Bottom half = input mirrored vertically (flip-ud). Equivalently, output = vconcat(g, flip-ud(g)). Default draws are always UD-asymmetric so the mirror is distinguishable from plain duplication.

Kind: `per_puzzle`. Generator version: `3.1.1`.
Approval is derived by the catalog from current code and retained evidence.
