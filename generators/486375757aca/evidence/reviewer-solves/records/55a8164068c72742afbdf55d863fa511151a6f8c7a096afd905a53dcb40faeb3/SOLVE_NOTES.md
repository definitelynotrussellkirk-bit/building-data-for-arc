# Solve work log

## Exposure record

Before this solve I had read the packet-level `WELCOME.md`, assignment duties,
and general ARC design guidance. I had **not** opened task `486375757aca`'s
generator, canonical rule, reference solution, private query labels, prior solve
notes, or audit records. The task-specific information I used was limited to the
visible examples in `solve-blind/README.md` / `challenge.json` and my own Python
probes.

## Revision 1 — framed fills plus touching-frame bridges

### Observations

Every nonzero/non-blue pixel lies strictly inside a complete blue rectangular
frame. In train examples 0 and 2, the output preserves each frame and fills its
whole interior with that frame's marker colour.

Train example 1 has three frames. Filling their interiors independently explains
the azure region but not the large green block. The upper-right maroon frame and
the lower-left green frame have orthogonally adjacent border cells. Their marker
positions are opposite corners of exactly the green block in the output. The
other pairs of frames do not touch. The green block is painted after the ordinary
fills, because it overwrites blue border cells, the maroon marker/interior, and
part of the azure fill.

### Probe

I enumerated all all-blue rectangular boundaries strictly enclosing each marker.
Every marker had exactly one candidate frame in all visible train and query
inputs. I also compared frame-border Manhattan adjacency:

- train 0: no touching frame pair;
- train 1: only the maroon and green frames touch;
- train 2: no touching frame pair;
- query 0: frame 1 touches frame 2, and frame 2 touches frame 3;
- query 1: no touching frame pair.

### Implemented hypothesis

1. Find the smallest complete blue frame around each marker.
2. Fill each frame interior with its marker colour.
3. For each orthogonally touching frame pair, fill the inclusive marker-to-marker
   bounding rectangle using the colour of the later frame in row-major order.
   Apply these bridges after all interior fills.

The single visible interaction establishes the bridge geometry and that the
lower/later frame wins in that orientation. It cannot distinguish every possible
priority convention (for example, a semantic priority tied to the green colour),
so the row-major interpretation remains the main uncertainty. Query 0's frames
form a descending chain, making this a meaningful extrapolation rather than a
special case for train example 1.

### Alternatives rejected

- **Only fill frame interiors:** fails train example 1's large green rectangle.
- **Fill a bounding rectangle for every marker pair:** fails train examples 0
  and 2, whose separated frames do not create bridges.
- **Trigger on three markers forming an L:** fits train example 1 accidentally,
  but ignores the more direct distinction that exactly one frame pair touches;
  query 0 then provides no principled interaction despite two touching pairs.
- **Use the bounding boxes of whole interiors:** train example 1 does not
  distinguish this from marker endpoints because the two markers occupy extreme
  interior corners. The output's exact correspondence to marker coordinates and
  the markers' role as per-frame instructions make marker-to-marker geometry the
  simpler hypothesis.
