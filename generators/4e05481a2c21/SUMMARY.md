# 4e05481a2c21

Extract every enclosed zero region from each colored object, recolor the union
with that object's color, crop it to its own bounding box, then pack object
patterns from left to right with one zero column between them.

The version 3.0.0 sampler retains the canonical two-object, 5..8 by 10..16
scale while adding three observable topology profiles:

- `rectangle`: one rectangular enclosed region per object;
- `notched`: a connected nonrectangular region plus an exterior zero in the
  object's bounding box;
- `split`: multiple enclosed regions plus an exterior bounding-box zero.

Lessons contain four demonstrations and one query.  The cyclic five-pair
schedule `notched, split, notched, split, rectangle` ensures every possible
query position leaves at least one notched and one split witness in the four
visible demonstrations.  These witnesses distinguish the intended rule from
three rivals that fit all labeled canonical pairs: filling the hole-union
bounding box, keeping only the largest enclosed region, and treating every zero
inside an object's bounding box as enclosed.

Kind: `per_puzzle`. Version: `3.0.0`. Canonical rule hash: `e13b35a51ff4`.
