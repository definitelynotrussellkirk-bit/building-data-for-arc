# Native parametric build: e44712f65f3e

`placement=centered` is the byte-exact canonical Racket rule. The nearby
`placement=nearest_edge` setting retains the same frame expansion but anchors
the expanded motif to the source frame's nearest canvas edge with tie order top,
bottom, left, right.

Inputs are generated independently of the selected setting. The ten profiles use
seed-varying geometry, include multiple independent frames, cover all four edge
directions plus two tie classes, and end with a `30 x 30` multi-object boundary
case. Current bounded evidence covers 500 Python seeds and ten complete profiles
over ten seeds in protected Racket; this is authoring evidence, not owner
acceptance or a universal identifiability proof.
