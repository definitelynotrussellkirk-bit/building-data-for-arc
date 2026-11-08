# generic_checker_rays_gen1

gen1: diamond rings on a checkerboard; flanking segments fire rays.

Scene: a two-color CHECKERBOARD field holds 1-3 diamond rings (|r-cr| +
|c-cc| = k). Each ring gets 1-4 of its sides flanked by a parallel diagonal
SEGMENT one step outward, each segment in its own color. Transform: every
free chain end (exactly one same-color diagonal neighbor) fires rays
perpendicular to its chain in each diagonal direction that opens onto
background, painting its color over the checkerboard to the edge (shapes
block). Rings never fire (no free ends); segment middles never fire.

Kind: `generic`. Imported version: `1.0.0`.
Approval is derived by the catalog from current code and retained evidence.
