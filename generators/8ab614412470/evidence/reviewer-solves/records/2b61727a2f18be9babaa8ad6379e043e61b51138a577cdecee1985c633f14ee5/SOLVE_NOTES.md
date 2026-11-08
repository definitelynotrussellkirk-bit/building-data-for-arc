# Visible-only solve notes

## Exposure declaration

I had already studied and repaired this task's generator before this episode, so this is an exposed solve, not a blind solve. During this solve I used only the visible examples in `solve/README.md` plus my own reasoning; I did not open the generator, Racket rule, references, private labels, or prior solution explanations.

## Hypothesis

Count each non-background color across the entire input. Preserve every cell whose color occurs at least twice, and replace every globally singleton color with background 0. Shape and positions otherwise stay unchanged.

Evidence from the visible examples:

- Example 0 removes colors 6 and 9 (one occurrence each) while retaining colors 4, 5, and 7 (two each).
- Example 1 removes both singleton colors 4 and 5 while retaining count-2 color 8 and count-3 colors 3 and 6.
- Example 2 removes all three singleton colors 4, 5, and 6 while retaining count-2 color 3 and count-4 colors 7 and 9.
- The count-2 survivors are spatially separated, so an adjacency/component rule is contradicted. Count-2 survivors also contradict a threshold of three. Multiple singleton deletions contradict “erase only one outlier.”

## Predicted queries

Query 0: retain colors 3 and 7; erase singleton colors 2 and 4.

Query 1: retain colors 3, 4, and 8; erase singleton colors 1 and 2.

## Implementation

A `Counter` over nonzero cells supplies global multiplicities. The output maps a nonzero value to itself exactly when its multiplicity is greater than one; all other cells become 0. The input is not mutated.
