# Post-repair visible-example solve notes

This is a human work log. I had already inspected the assigned generator and
canonical rule during the required repair phase, so this solve is **not blind**.
During this solve episode I used only the public presentation emitted by
`solve_episode.py prepare`; I did not reopen the generator, Racket source,
reference solutions, or private labels.

## Hypothesis

The 5×17 input consists of three aligned 5×5 panels occupying columns 0–4,
6–10, and 12–16, with separator columns 5 and 11. For each local coordinate,
count how many panels contain a nonzero cell there. Encode counts 0, 1, 2, 3 as
output colors 0, 2, 4, 8 respectively.

Visible checks supporting the hypothesis:

- Train 0 local (1,2) is occupied in all three panels and becomes 8; local
  (2,2) is occupied only in panel 3 and becomes 2; local (2,1) is occupied in
  panels 1 and 3 and becomes 4.
- Train 1 uses the top-left 3×3 window, showing that the transform is aligned to
  the full 5×5 panel rather than cropping the motif.
- Train 2 uses the bottom-right window and includes border cells, ruling out a
  central-3×3-only interpretation.

The implementation directly computes this count map. No failed natural
revision was needed because the three demonstrations determine the mapping and
coordinate alignment unambiguously.
