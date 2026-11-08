# Diagonal midpoint completion family

`passes=1` is the byte-exact selected canonical program. `passes=2` applies the
same simultaneous-source midpoint completion twice. Step A's first-pass grid is
the input-dependent intermediate; step B recomputes eligibility on that grid.
Every generated scene contains a cascade where the first pass creates an endpoint
needed by the second, and a longer branch where a third pass would make another
write. Thus one pass, exactly two passes, and closure are all distinct. Axis-aligned,
already-filled, and distance-four decoys block broader pair-completion shortcuts.

The fourth query is a substantive 30x30 tiled scene with at least 80 original
foreground cells and at least ten writes unique to the second pass.
