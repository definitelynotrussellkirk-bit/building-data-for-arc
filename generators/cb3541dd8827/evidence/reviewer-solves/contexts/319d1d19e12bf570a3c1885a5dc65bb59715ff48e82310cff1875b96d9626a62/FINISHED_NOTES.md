# Solve work log

## Exposure declaration

I had seen the selected generator's intended rule earlier while repairing it, so this
is **not** a blind first encounter. During this solve episode I kept the generator,
Racket rule, reference outputs, private query labels, and earlier solution notes
closed and used only `challenge.json` / the visible examples.

## Revision 1

### Visible hypothesis

Every substantial nonzero connected component that is the exact perimeter of an
axis-aligned rectangle is a frame. Inside each frame the input contains background
zeros and exactly one non-background color different from the frame. The output
keeps the frame and everything outside it unchanged, then paints every interior
cell with that seed color. Multiple frames are processed independently.

This explains all four demonstrations:

- example 0 expands seed color 1 through the interior of the color-2 frame;
- examples 1 and 2 show two frames receiving their own distinct seed colors;
- example 3 shows three frames, refuting a first-frame-only or single-global-seed
  interpretation;
- frame colors vary (2, 5, 6, 7, 8, 9), so color 2 is not special.

### Implementation and probe

`solution.py` finds four-connected components separately for every nonzero color,
recognizes a component only when it equals the full perimeter of its bounding
rectangle, finds the unique interior seed color, and fills only that rectangle's
strict interior. This avoids treating isolated seed cells as frames and supports
several disconnected frames of the same color.

I checked the implementation locally against every visible training pair before
submitting the revision. All four matched exactly. The remaining uncertainty is
limited to malformed inputs with incomplete frames or multiple seed colors; the
visible task consistently supplies exact frames with one seed apiece, so the solver
leaves such ambiguous interiors unchanged rather than inventing a rule.
