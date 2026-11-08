# Solve work log

## Prior exposure

I had earlier exposure to the family rule while reviewing this same generator, before this fresh solve was prepared. I did not consult the Racket authority, generator implementation, private labels, prior solve code, or prior solve notes during this attempt. I used only the newly prepared visible examples and the solve harness.

## Revision 1 — crossed strands become a woven rectangle

The input contains one long non-background row and one long non-background column. Each is a strand with a repeated base color and exactly two cells of a second marker color. Their intersection contains one strand's base color, which appears to select priority. The output clears the input and draws a rectangle whose horizontal bounds are the two horizontal markers and whose vertical bounds span the crossing row and both vertical markers.

I compared the three visible outputs in coordinates relative to the rectangle's top-left corner. Odd relative rows are either entirely horizontal-base (horizontal priority) or alternate horizontal-base/vertical-base (vertical priority). On even relative rows, even relative columns carry a marker color: vertical-marker between the vertical marker rows, horizontal-marker outside that band. Odd relative columns carry vertical-base, except that the nearer vertical-marker row uses horizontal-base when horizontal priority is selected. This accounts for all cells in all three visible outputs, including the asymmetric boundary row in train 0 and the crossing-straddled cases in trains 1 and 2.

The program identifies the background by global frequency, finds the dominant row and column by non-background occupancy, infers each strand's marker as its lower-frequency non-crossing color, then renders the inferred rectangle from scratch.

Remaining uncertainty: ties in distance from the crossing to the two vertical markers are not demonstrated. The implementation breaks such ties toward the upper marker. Also, the visible examples keep base and marker frequencies unequal after excluding the crossing; the solver treats that as part of the lesson contract.
