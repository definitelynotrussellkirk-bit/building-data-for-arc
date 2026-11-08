# Visible-only solve notes

Earlier generator work exposed the task family, so this is not a blind solve. I did not reopen the generator, Racket rule, private labels, prior solve notes, or reference material during this final-source episode.

From the four visible demonstrations: process each nonzero color independently. Whenever its original cells occupy exactly three corners of an axis-aligned rectangle, add the same color at the fourth corner. Preserve every existing cell. Example 2 establishes that an additional same-color point may be irrelevant, so rectangle detection must search row/column pairs rather than assume exactly three total cells. Apply the rule from the original input in one pass so newly filled corners do not trigger cascades.
