# Solve work log

Earlier exposure before this step: I had not opened this task's generator, rule,
notes, reference solutions, private labels, or any generator for the assigned
repair. I had only read the packet-level instructions and the visible
`challenge.json`.

## Revision 1 — horizontal beacon selection

The first row contains colour-9 marker cells while the remainder contains several
separate coloured objects. Every shown output is the tight crop of exactly one
same-colour 4-connected component, retaining its orientation and colour while
turning other colours inside the crop into background.

I measured each component's horizontal bounding interval against the marker
columns. The shown target consistently has the strongest horizontal alignment:

- example 1: colours 5 and 7 each contain one marker column, but colour 7 has the
  smaller total horizontal distance to all three markers;
- example 2: colour 5 contains two marker columns, more than every rival;
- example 3: colour 8 contains two marker columns, more than every rival.

Hypothesis: the top-row 9s are horizontal beacons. Select the component whose
bounding interval contains the most beacons; break a tie by the sum of each
beacon's horizontal distance to that interval. Crop the selected component and
mask every non-selected cell to zero.

I considered a count-only alternative: the number of markers is one less than a
large target dimension in the three demonstrations. I rejected it because it
ignores the conspicuous placement of the markers directly over/near the shown
objects and gives different test predictions. The horizontal-beacon rule uses
both marker identity and position and explains the otherwise necessary tie in
example 1.

Predictions before checking visible examples: test 1 selects the colour-5 object;
test 2 selects the colour-8 object. Remaining uncertainty is the exact tie-break
policy for unseen layouts; area and reading order are only deterministic final
fallbacks after the demonstrated alignment criteria.
