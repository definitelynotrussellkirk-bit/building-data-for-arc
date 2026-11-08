# Commanded-intersection adjacency finish

The native family preserves the exact canonical `all_overlap` program and adds
`adjacent_overlap` over identical 4x7 inputs.

1. **A:** read the command, transform the right 3x3 occupancy mask, and intersect
   it with the left 3x3 mask.
2. **Intermediate:** the command-dependent 3x3 overlap mask.
3. **B:** retain only overlap cells having an orthogonal neighbor in that same
   intermediate mask.

The retained counterfactual runs B on the left panel mask instead of the
intersection and changes the output. Two demonstrations distinguish the two
settings and the declared horizontal-only, vertical-only, 8-neighbor,
endpoint-only, and wrong-intermediate shortcuts. The exact canonical program
hard-codes a 4x7 input and 3x3 output, so a 30x30 stress case is not lawful for
this source-bound family; enlarging the panels would make the canonical default
non-executable and violate exact-default preservation.
