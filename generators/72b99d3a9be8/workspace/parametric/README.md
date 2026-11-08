# 72b99d3a9be8 reflector-color family

`reflector_color=2` returns the exact source-bound canonical Racket program.
`reflector_color=3` changes only which input color is interpreted as a wall;
the wall orientation is still measured from the selected color's neighboring
cells.  Every episode uses matched inputs, 2–6 prefix-stable demonstrations,
and four fixed queries including a 30×30 stress scene.

The sequential dependency is explicit: A traces the selected color and derives
an ordered bounce-event sequence; B consumes those events implicitly by
continuing the beam in each reflected direction.  `audit.py` checks Python ↔
protected-Racket parity, other-setting rejection, finite shortcut rejection,
and sampler prefix stability.
