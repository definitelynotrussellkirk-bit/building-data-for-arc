# Blind solve notes

No generator, rule, canonical answers, earlier explanations, or audit records were opened before this solve. Preparation displayed only the public challenge.

The three visible examples have input/output shapes 12x4 -> 6x4, 10x10 -> 5x10, and 10x8 -> 5x8. Each input is two vertically stacked panels; each panel uses its own foreground color over zero. Output uses color 4 wherever either aligned panel cell is nonzero, and zero only where both are zero.

I compared union, intersection, exclusive-or, top-only and bottom-only predictions against the three visible outputs. The actual mismatch counts are retained in visible_probes.json. Union matches all examples. Overlapping occupied cells remain 4, ruling out exclusive-or; singly occupied cells remain 4, ruling out intersection. No incorrect solution revision was submitted merely to manufacture a negative.

The solver uses the observed fixed output color 4, background 0 and vertical equal-half split. Alternative orientations or recoloring rules outside this visible task are untested. I stopped after the visible checker passed; masked-query correctness remains unknown and is reserved for maintainer scoring.
