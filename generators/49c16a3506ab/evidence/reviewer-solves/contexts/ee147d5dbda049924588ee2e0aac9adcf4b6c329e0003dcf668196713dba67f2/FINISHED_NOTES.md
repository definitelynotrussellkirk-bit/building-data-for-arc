# Solve notes

## Exposure declaration

I had already inspected and repaired this task's generator before this episode, so this is **not blind**. During the solve episode itself I used only the visible examples printed by `solve_episode.py prepare`; I did not reopen the generator, Racket source, canonical answers, private labels, or earlier solution text.

## Visible rule reconstruction

Each non-background color has one solid 3×3 block in a corner. Every other cell of that color is a movable singleton tied to the block of the **same color**.

For a singleton:

- if its row lies in the block's three-row band, move horizontally toward the block;
- if its column lies in the block's three-column band, move vertically toward the block;
- otherwise move diagonally toward the block;
- stop on the last cell before the next step would enter the 3×3 block.

The block and background remain unchanged. The four demonstrations include both main- and anti-diagonal corner arrangements and cells that are geometrically nearer to the other colored block, so nearest-block motion is not sufficient; color ownership is the stable cue.

## Implementation choices

I infer the background as the modal color, identify each solid corner block, collect all moves before editing the grid, clear every source, then place every destination. Collecting first avoids update-order artifacts.

No failed natural revision was needed: this implementation is the first submitted solve revision.
