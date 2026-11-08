# Solve notes

This is an exposed post-repair solve. I had already inspected the assigned generator before this episode, so earlier rule exposure must be declared `yes`; during this solve I used only the visible examples printed by `solve_episode.py prepare` and did not reopen the generator, Racket source, canonical answers, or prior solution explanations.

## Visible-example inference

Each input has three nonzero colors. The output has one row per nonzero color, ordered by ascending numeric color. The number of copies of that color in its row equals its total input cell count. Rows are left-aligned and padded with zero to the largest count in that input.

Examples check the key alternatives:

- Example 1 has counts color 1 = 3, color 4 = 2, color 5 = 4; the output order is `1,4,5`, not size order or spatial order.
- Examples with maximum count 4 produce width 4, while examples with maximum count 5 produce width 5, so output width is data-dependent rather than fixed.
- Irregular shapes show that the bar length is cell area, not bounding-box area.

The implementation counts every nonzero cell by color, sorts the colors, and pads each bar to the maximum count. No failed natural revision was needed because this rule matches all five visible demonstrations directly.
