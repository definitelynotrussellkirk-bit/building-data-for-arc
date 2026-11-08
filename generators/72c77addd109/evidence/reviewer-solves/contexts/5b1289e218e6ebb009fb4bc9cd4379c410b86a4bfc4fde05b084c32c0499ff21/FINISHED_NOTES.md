# Solve notes — 72c77addd109

This is a human-style work log based only on `solve/challenge.json`. I had prior rule exposure from reviewing this task's generator, so this is not a blind solve; during this solve phase I did not reopen the generator, Racket rule, reference solution, private labels, or earlier solution explanations.

## Visible observations

- Every input has four monochrome 4-connected components: two hollow rectangular borders near the bottom and two non-frame shapes near the top.
- The output is a fresh black grid: the top shapes vanish from their original locations, the two frames stay where they were, and one shape is moved onto each frame.
- Pairing is not by reading order or color. In train 2, the five-cell red shape goes to the larger frame while the three-cell yellow shape goes to the smaller frame. Across the examples, sorting solids by occupied-cell count and frames by interior area explains every pairing.
- The full tight crop is centered, not merely its occupied-cell centroid. Irregular holes remain holes. When a crop is larger than the frame interior, its colored cells overwrite border cells rather than being clipped; train 2 and train 3 make this visible.

## Hypothesis / implementation

1. Find same-color 4-connected components.
2. Classify an exact bounding-box border as a frame; all others are solids.
3. Sort frames by `(height-2)*(width-2)` and solids by occupied-cell count.
4. Start from an all-zero grid, redraw frames, then paste each solid's tight crop centered relative to the paired frame interior. Pasting after redrawing the frame accounts for border overwrite.

The visible examples determine the negative-half centering convention too: use floor division, equivalent to placing the crop at `frame_min + 1 + floor((interior_size-crop_size)/2)`.
