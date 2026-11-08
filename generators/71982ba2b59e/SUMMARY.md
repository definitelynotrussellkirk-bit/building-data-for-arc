# 71982ba2b59e

A 0-background grid contains 3-6 separated monochrome components.  Every normal draw has (1) two differently colored rotation-equivalent shapes, (2) two same-colored non-equivalent shapes, and (3) an unrelated pair.  Some draws also contain a same-color, same-shape pair to show that shape equality takes precedence and still emits 8.  Sort components by bounding-box (top, left); output the NxN relation matrix: diagonal = the component color, else 8 for rotation-equivalent shape, else 6 for equal color, else 0.

Kind: `per_puzzle`. Imported version: `3.0.0`.
Approval is derived by the catalog from current code and retained evidence.
