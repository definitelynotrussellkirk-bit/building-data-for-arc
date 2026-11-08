# ba5056d6102e — Boolean intersection of aligned panels

Version `3.1.0`; canonical rule hash `1586ec3843ec`.

An input has two equal-height panels separated by exactly one full-width row of
color 5. Each panel has background 0 and one distinct foreground color chosen
outside `{0,5,8}`. The output has one panel's dimensions and contains color 8
exactly at coordinates where both aligned panel cells are nonzero; every other
output cell is 0.

The curriculum uses a call-order-independent four-slot schedule:

1. `canonical_like`: public shape/palette support (5×8 panels, top 2, bottom 3,
   public occupancy signatures);
2. `palette_shift`: noncanonical colors;
3. `shape_shift`: noncanonical dimensions and clustered support, with canonical
   bottom color 3 deliberately used in the top role;
4. `structured`: striped or diagonal support, also with color 3 in the top role.

Every generated input contains all four occupancy states (`00`, `10`, `01`,
`11`). Consequently, union, xor, top-only, and bottom-only rivals disagree on
every example. Every consecutive three-example lesson also contains a
noncanonical palette and at least one top-panel use of color 3. Those two
lesson-level witnesses refute both the literal public-palette shortcut and the
wrong assumption that canonical color 3 is valid only in the bottom panel.

Declared exact controls are `half_h`, `grid_w`, `top_color`, `bottom_color`, and
`support_style`. Equal top/bottom colors are the only enumerated
incompatibility. Unknown controls are rejected.

Approval is derived externally by the catalog. This review did not alter the
Racket authority or claim training admission.
