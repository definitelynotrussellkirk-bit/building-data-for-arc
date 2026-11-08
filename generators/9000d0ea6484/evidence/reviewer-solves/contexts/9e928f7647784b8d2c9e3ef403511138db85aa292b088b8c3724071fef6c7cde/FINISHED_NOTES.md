# Visible-only solve notes

## Revision 1 hypothesis

The three full-height color-3 columns at indices 4, 9, and 14 divide each
4×19 input into four aligned 4×4 panels. The output is one 4×4 panel formed
cellwise, not by copying one whole panel.

For every aligned position, compare the four source values. Solo-source cells
show that any panel can contribute. Overlap cells establish a fixed panel
priority independent of color: panel 2 beats panels 0, 1, and 3; panel 3 beats
panels 0 and 1; panel 0 beats panel 1. Therefore the order is
`panel 2 > panel 3 > panel 0 > panel 1`. If all four aligned cells are zero,
the output is zero.

Probe: implement that rule directly and check all visible examples. I had seen
the generator rule earlier during the required repair work, so this is not a
blind inference; however, this revision uses no reference source during the
solve phase and is checked only against the displayed examples.
