# Solve work log

## Prior exposure

I had already inspected this task's source authority while repairing its generator, so this is an exposed post-repair solve (`earlier-exposure=yes`). During this solve I used only the prepared visible examples and did not reopen the generator, Racket source, canonical ledger, reference solution, or private query labels.

## Visible-example inference

All examples preserve dimensions and existing cells. Each changed zero is the unique missing corner of a 2×2 window whose other three cells have one identical nonzero color.

The examples also disambiguate component-level shortcuts:

- Train 1's color-5 component has a three-cell top run and one lower-right cell. The right 2×2 is completed, but that new cell is not reused to complete the left 2×2. This implies a simultaneous one-pass scan over the original input rather than iteration to a fixed point or filling the whole bounding box.
- Train 1's color-3 component and train 3's color-7 component contain overlapping qualifying windows. Both missing corners are completed, so the rule is not limited to one fill per connected component.
- Colors are copied from each local three-cell pattern; zero is the background.

## Revision 1

Implemented a pure one-pass scan. For every original 2×2 window, collect nonzero values; when there are exactly three and they are equal, copy that color into the unique zero in a deep-copied output. All reads remain from the original grid, preventing cascades within one application.

Remaining uncertainty is limited to masked queries; the visible examples determine the local rule and simultaneous-update convention clearly.
