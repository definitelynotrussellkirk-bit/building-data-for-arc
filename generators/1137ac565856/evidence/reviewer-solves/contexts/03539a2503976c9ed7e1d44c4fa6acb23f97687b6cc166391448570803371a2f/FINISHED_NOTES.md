# Solve work log

## Exposure declaration before solving

I had not opened task `1137ac565856`'s generator, Racket rule, canonical record,
prior solutions, audit records, or private labels. I had only read the packet-level
instructions and this visible `challenge.json`.

## Revision 1 — smallest enclosing rectangular frame

**Observation.** Every input contains nested, single-cell-thick rectangular frames,
a single red (`2`) marker inside them, and background `0`. The output is a solid
rectangle. In each visible pair, its color and dimensions match the *smallest
complete colored frame whose bounding box strictly encloses the marker*:

- pair 0: the marker lies inside the `4` frame; its 14×17 bounding box becomes a
  14×17 solid `4` rectangle;
- pair 1: the marker lies inside the innermost 3×3 `9` frame, producing solid `9`;
- pair 2: the marker lies inside the innermost 4×5 `4` frame, producing solid `4`.

**Alternative considered.** Selecting the color nearest to the marker by Manhattan
distance happens to agree here, but it is less structural and could choose a stray
cell. Selecting the globally rarest or innermost color also fails if an unrelated
object exists. I therefore detect actual 4-connected components whose cells equal
an entire rectangular border, retain those strictly enclosing the unique `2`, and
choose the smallest bounding-box area.

**Test-first probe.** I added `visible_probe.py`, which runs `solve` against all
visible training pairs. With the untouched `NotImplementedError` stub it failed as
expected (`visible-probe-red.log`). I then implemented the frame test and will run
both the probe and the official visible-only checker.

**Remaining uncertainty.** The visible data always has exactly one marker and a
complete rectangular frame around it. The solver deliberately rejects malformed
inputs rather than guessing. It supports multiple colors and disconnected objects
because candidate frames are evaluated per 4-connected component.
