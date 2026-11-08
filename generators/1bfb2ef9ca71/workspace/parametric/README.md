# Native parametric family: `1bfb2ef9ca71`

`finish=borders_only` is the selected canonical Racket source byte-for-byte.
`finish=fill_largest_interior` first draws every colored rectangle border, then
selects the frame with greatest enclosed interior area (row-major tie-break) and
fills that interior with the frame's own color.

The settings use identical inputs. Three demonstrations move the winner across
colors, locations, and aspect ratios; the first separates largest interior area
from longest perimeter. Four queries include border contact, three-object
competition, and a substantive four-rectangle 30×30 scene.

Sequential dependency: A is the canonical border construction; the intermediate
is the grid of closed colored frames; B measures their enclosed interiors and
fills the largest. `skip_borders.rkt` runs B on a blank intermediate, leaving no
frame or enclosure to select.
Re-run the bounded authoring audit with:

```sh
python3 generators/1bfb2ef9ca71/workspace/parametric/audit.py
```

It checks matched/prefix-stable episodes, sequential public-view privacy, the
30×30 stress case, and six named shortcuts. It does not replace protected
qualification or owner acceptance.
