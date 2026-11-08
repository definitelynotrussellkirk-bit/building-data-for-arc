# Post-repair visible-example solve

Earlier rule exposure: **yes**. I reviewed and repaired this generator before
preparing this episode. This is an exposed author solve, not an independent
blind inference. During the solve I opened only this challenge, its README and
solution stub; I did not reopen generator source, the reference rule, earlier
solution notes or private labels.

The three visible demonstrations preserve the original grid and add colored
reflections of each local main shape. Nonzero cells form groups through side
or diagonal contact. Within each group, the most frequent color is the shape;
the other colors are single-cell direction cues at its corner. A cue outside
the shape's horizontal extent requests horizontal reflection, one outside its
vertical extent requests vertical reflection, and a diagonal cue requests both.

Concrete observations: example 0 has two color-2 cues in separate groups, so
cue roles must be local. Example 1 uses color 1 for a main shape in one group
and a singleton cue in another; a global color-frequency rule would lose that
copy. Example 2's asymmetric shape shows a reversed outline rather than a
plain translated copy. Original positions stay intact in all three examples.

The first implementation uses a local 8-neighbor flood fill, chooses the local
plurality color, reflects occupied cells about the appropriate half-cell
bounding-box edge, and clips writes to the canvas. The displayed examples do
not independently establish clipping behavior; that fallback is an exposed
assumption and the episode does not claim to test it. No project functions,
reference program or hidden query outputs are imported.

I submit one genuine solve attempt. The checker will report visible-example
agreement and whether both masked queries execute. Their correctness is unknown
to me because private correctness feedback is withheld.
