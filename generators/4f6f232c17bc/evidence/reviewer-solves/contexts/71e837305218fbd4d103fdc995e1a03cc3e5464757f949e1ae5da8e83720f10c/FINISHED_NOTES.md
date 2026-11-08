# Visible-only solve notes

## Access boundary

Read only this episode's `README.md` and `challenge.json`. No earlier rule exposure; no generator, reference solution, private label, prior solution note, or external reference consulted.

## Revision 1 hypothesis

The full-height color-5 column is a vertical reflection axis. Reflect each color-1 cell horizontally across it, recolor the reflected cells to 8, and discard reflections outside the original grid. All other output cells are 0; marker colors are ignored.

Visible observations supporting the hypothesis:

- Example 0: axis column 5 maps columns 0 and 1 to 10 and 9, preserving both rows.
- Example 1: axis column 2 maps top-row columns 3 and 4 to 1 and 0; column 5 maps outside the grid, including the second-row cell.
- Example 2: axis column 9 maps columns 7 and 8 to 11 and 10; columns 5 and 6 map outside the grid. The surviving cells match the shown output.

## Experiment plan and limits

Run the public blind check for this revision and retain its recorded feedback. One genuine implementation revision; no failed revision has been discarded. The visible examples support a vertical axis only. Masked query correctness is unavailable and must not be inferred from visible checks.
