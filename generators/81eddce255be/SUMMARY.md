# 81eddce255be

A 10–14 by 10–14 grid contains a contiguous blue header run in row 0, a blank separator row, and exactly three separated body objects of distinct colors and distinct areas. The header length `K` lies in 2..6, and exactly one body object has area `K`. The selected rule clears the header and distractors while preserving that unique area-`K` object at its original location and color.

Generator version `3.0.0` is constructive. Its exact public controls are `grid_h`, `grid_w`, `K`, and `target_rank`; every documented value is legal in every difficulty band and recoverable from returned pixels. Default lessons use three demonstrations, cycle canonical 10/11/12 profiles, cover all `K` values, and cross target row-rank with target size-rank. They deliberately include non-topmost targets to refute the strongest shortcut fitting the canonical demonstrations: “keep the first/topmost object.”

The canonical Racket authority remains unchanged at rule hash `70441dae68b0`.
