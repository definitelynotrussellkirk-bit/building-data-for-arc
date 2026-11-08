# 51cb5336f078 — replace an object with its bounding-box frame

Version 3.0.0. The unchanged canonical Racket rule (`2bb5c38e3f24`) starts from an empty canvas: it erases the original interior rather than merely adding an outline.

Generate one connected monochrome object with 3..18 pixels on a 5..12 by 5..12 zero canvas. Exact controls are `grid_h`, `grid_w`, `motif_size`, and `color`; all advertised combinations are supported in all bands. Legacy cosmetic, singleton, and degenerate texture controls are deliberately removed rather than silently accepted.

Default even sample indices supply bent-interior witnesses; odd indices supply broader nonidentity shapes. Three demonstrations suffice to refute the four declared rivals in the checked production sampler. Four consecutive unrejected samples contain at least two such witnesses, supporting all one-query rotations. Explicit motif sizes 3/4 disable that default teaching guarantee. Finite rival checks do not prove universal identifiability.

Approval remains a maintainer decision. This source revision does not admit any training trajectory.
