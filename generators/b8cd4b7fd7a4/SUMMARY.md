# b8cd4b7fd7a4

0-bg grid (h, w ~7-9) with EXACTLY TWO non-zero cells of color 3 (green) at ALIGNED positions: either same row (horizontal), same column (vertical), or on a perfect diagonal (|dr| == |dc| > 0). Distance between them ≥ 3 (so there's interior). Rule: collect non-zero points (2 of them). Compute the Bresenham span between them EXCLUDING endpoints. Paint those interior cells color 8 (cyan) on an otherwise-empty same-size grid. Original endpoints DISAPPEAR in output.

Kind: `per_puzzle`. Imported version: `2.1.1`.
Approval is derived by the catalog from current code and retained evidence.
