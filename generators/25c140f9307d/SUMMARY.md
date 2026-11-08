# 25c140f9307d

A large red plate contains two to four separated four-cell polyomino holes. Each detached 3×3 key object has four red teeth whose free-polyomino shape matches exactly one hole up to rotation, plus two non-red payload cells. The canonical Racket rule rotates each matching key, fills the corresponding hole with red teeth, copies the payload colors onto the red rim, and returns the cropped decorated plate.

The reviewed controls are `rect_size=9..14` for an exact square plate and `n_keys=2..4` for the number of distinct hole/key pairs. Default geometry remains difficulty-aware and may be rectangular.

Kind: `per_puzzle`. Generator version: `2.2.0`. Packaging a review does not itself grant approval or training admission.
