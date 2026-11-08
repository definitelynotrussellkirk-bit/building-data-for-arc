# ba0c6a5828f9

Use the unique red (`2`) cell as the rotation pivot. For every blue (`1`)
marker, paint the in-bounds cells reached by 0°, 90°, 180°, and 270° rotations
around that pivot. Orbit members outside the canvas are skipped; they do not
cancel the in-bounds members. The red pivot remains red.

The generator uses a deterministic four-profile teaching schedule:

| Profile | Pivot | Clipped marker orbit | Purpose |
| --- | --- | --- | --- |
| `canonical` | geometric center | no | Match the 7×7/9×9 public morphology. |
| `off_center` | not geometric center | no | Refute “rotate around canvas center.” |
| `clipped` | geometric center | yes | Refute “discard incomplete orbits.” |
| `mixed` | not geometric center | yes | Exercise both hidden branches together. |

Every consecutive four sample indices contain all four profiles (with a
seed-dependent phase). Any three of the four profiles distinguish both named
canonical-fitting shortcuts. `profile` is the only exact override; all returned
pixels expose which profile was requested.

Kind: `per_puzzle`. Selected version: `3.0.0`. Canonical rule hash:
`e28fcc7b8767`. The selected Racket rule itself is unchanged.
