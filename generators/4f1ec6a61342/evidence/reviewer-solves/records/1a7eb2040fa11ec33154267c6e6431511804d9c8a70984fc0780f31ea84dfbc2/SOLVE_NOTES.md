# Solve work log

## Prior exposure

I had not opened task `4f1ec6a61342`'s generator, rule, notes, solutions, audit
records, or private labels. I used only `solve-blind/challenge.json`.

## Revision 1 — room selected by a count key

The gray `5` cells form horizontal and vertical walls that divide each grid into
four rectangular rooms. The cell at the upper-left corner is a numeric key
(sometimes it is itself `5`, so it visually merges with the wall). In every
training example, exactly one room contains that many blue `2` cells:

- key 5: room counts are 2, 5, 4, and 6; the 5-count room becomes azure;
- key 3: the 3-count room becomes azure;
- key 6: the 6-count room becomes azure.

The output clears the blue clues and any non-gray corner key to black, preserves
the gray walls, and fills the complete selected room with azure `8`. I implemented
separator detection from complete gray rows/columns while exempting `(0, 0)`,
counted blue cells in each room, selected the first exact match, and reconstructed
the output. The two visible test keys (1 and 6) also each have a unique matching
room by manual count.

Remaining uncertainty: the examples do not define behavior for zero or multiple
matching rooms. The generated instances appear designed to have a unique match;
the implementation leaves all rooms unfilled only if no match exists.
