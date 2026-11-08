# Visible-only blind solve: b9b63ae52d91

No task generator, rule, notes, reference solution, private labels, or prior explanation was opened. Only challenge.json and independent Python probes were used.

Observation: background 0 stays unchanged; every 8 becomes either 2 or 5, without changing shape. Dense examples contain red square-like regions but sparse examples contain red isolated points and line segments.

Exploratory probes (not submitted solutions): collected labels by orthogonal/diagonal neighbor counts, full radius-one neighborhood, row/column counts, coordinate parity, and horizontal/vertical/diagonal contiguous run lengths. Each had conflicting labels for the same feature, so these do not determine the answer. The apparent 2x2-square hypothesis fails on the sparse second example. Rendered the five visible examples as text to compare global alignments.

Global hypothesis: reflect the input top-to-bottom. An 8 whose reflected partner is also 8 becomes 2; an 8 without its reflected partner becomes 5. The top and bottom rows of the second example distinguish this directly: their shared columns are red and their unshared columns gray. The same comparison explains the six-row fourth example, including its apparent square fragments. The center row of an odd-height grid is its own reflection and should become entirely red on occupied cells.

Revision 1 implements this hypothesis directly, preserving zero and not reading any external data. Run the official visible-only check, then stop if all five demonstrations agree. Hidden labels remain uninspected and no hidden success is claimed.
