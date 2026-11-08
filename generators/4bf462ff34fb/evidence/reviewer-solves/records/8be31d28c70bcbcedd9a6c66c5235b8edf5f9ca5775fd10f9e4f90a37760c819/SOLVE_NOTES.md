# Visible-only solve log

Earlier exposure: yes. I repaired this task's generator before this required solve, so this is not a blind inference record. During this solve phase I used only the prepared visible examples and did not reopen the generator, Racket rule, private labels, reference solutions, or earlier solution explanations.

Hypothesis from the three demonstrations: segment color-1 cells into 4-connected components. Recolor a component from 1 to 3 exactly when it touches the top edge and touches none of the bottom, left, or right edges. Preserve interior blue components, blue components touching any other edge (including top corners), and every non-blue component.

Checks against visible examples:
- Example 0 preserves the blue component at the top-left corner while recoloring two top-only blue components; this rules out “all top-touching blue.”
- Example 1 preserves the left-edge singleton and interior/bottom blue components while recoloring all top-only blue components.
- Example 2 preserves the top-left component and other non-target blue components while recoloring the top-only components.

Implementation: 4-neighbor flood fill over color 1, compute each component's border signature, and recolor only signature `T`. The transformation preserves shape and dimensions.
