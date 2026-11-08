# Solve notes

The visible examples show one small three-color template and separate square
objects in the two singleton template colors. The modal color inside the
template is copied into a scaled/rotated/reflected version of the template at
each marker pair. The two external squares occupy the transformed marker-port
locations; only background cells corresponding to the template's modal-color
cells are painted.

Revision 1 implements this directly: find the 8-connected multicolor template,
find 4-connected monochrome external marker squares, greedily pair nearest
opposite-color objects without reuse, try the eight D4 transforms and both
marker assignments, and paint scaled fill cells while preserving existing
objects and holes. I expect this to handle the unit, scale-2, scale-3,
multi-pair, same-diagonal, opposite-diagonal, and mixed examples shown.
