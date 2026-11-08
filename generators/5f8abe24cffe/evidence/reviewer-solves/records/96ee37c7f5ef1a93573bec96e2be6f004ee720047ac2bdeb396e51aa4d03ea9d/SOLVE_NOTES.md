# Solve work log

## Exposure declaration before solving

I had not opened task `5f8abe24cffe`'s generator, rule, notes, private labels,
reference solution, or earlier solve records. I used only `challenge.json` and
my own calculations. I had only read the packet-wide instructions and assignment.

## Visible-example hypothesis

Each input contains exactly three rectangular color-1 frames. Remove each frame
and crop away all-zero exterior rows and columns from its interior. The first two
cropped panels are a before/after pair related by one of the eight square-grid
symmetries; apply that same symmetry to the third cropped panel to obtain the
answer.

Visible checks:

- Training example 1: panel 1 rotated 90 degrees clockwise equals panel 2; the
  same rotation of panel 3 gives the shown 4x2 output.
- Training example 2: panel 1 rotated 180 degrees equals panel 2; the same
  rotation of panel 3 gives the shown 2x2 output.
- Training example 3: panel 2 is the left-right reflection of panel 1; reflecting
  panel 3 gives the shown 3x2 output.

## Revision 1

Implemented connected-component detection for complete color-1 rectangular
frames, reading-order panel extraction, nonzero bounding-box cropping, and a
search over the eight dihedral transforms. The matched operation is then applied
to panel 3. This avoids hard-coding the particular rotations/reflection seen in
training and supports rectangular cropped panels.

Remaining uncertainty before checking: a deliberately symmetric before-panel
could allow multiple transforms, but the visible lessons appear designed to make
the operation observable. The implementation chooses the first exact match in a
stable order.
