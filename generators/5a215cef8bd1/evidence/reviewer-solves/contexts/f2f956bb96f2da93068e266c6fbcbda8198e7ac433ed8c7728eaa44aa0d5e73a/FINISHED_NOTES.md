# Solve work log

## Prior exposure

Before this visible-only solve I had already inspected and repaired the assigned generator and its canonical Racket rule. I therefore record **earlier rule exposure: yes**. After `solve_episode.py prepare`, I did not reopen the generator, rule, canonical examples, reference solutions, or private labels. The implementation below was checked only against `solve/challenge.json` and visible-example feedback.

## Attempt 1

The inputs contain one connected color-2 object and four singleton control colors, 1/3/4/6, arranged on two rows and two columns. The outputs crop the color-2 object, recolor it to 7, make four transformed copies, and put them into a 2-by-2 panel separated by one blank row and one blank column. Comparing the visible panels gave this key:

- 1: identity
- 3: rotate 90 degrees clockwise
- 4: rotate 180 degrees
- 6: reflect left-to-right

The spatial order of output panels is not fixed by color. It copies the rank order of the control cells: the upper/lower control row chooses the panel row and the left/right control column chooses the panel column. This accounts for all three visible demonstrations, including template sizes 2, 3, and 4.

I implemented that rule directly. The solver extracts the single 4-connected color-2 object, crops its binary shape, locates the four controls, computes the four transforms, and paints the copies in color 7 with blank separators. I saw no competing visible hypothesis that explained all control permutations and all output orientations, so I made one genuine check attempt and planned to stop if it passed all demonstrations.
