# a287e878de99 — Path Endpoints Only

Generate a 7..15 × 8..17 zero-background grid containing 2..5 separated gray/color-5 components. The output retains exactly the gray cells with one orthogonal gray neighbor and erases every other cell.

Version `3.0.0` pins canonical rule hash `d7cc9d995b63`. A four-example schedule cycles through simple paths, a branch, a cycle-with-tail, and an isolated-cell scene so lessons distinguish the local degree-one rule from component-level “keep two endpoints” and `degree <= 1` shortcuts. Exact controls are `grid_h`, `grid_w`, `component_count`, and `scene_pattern`; all advertised combinations are constructive and pixel-observable.
