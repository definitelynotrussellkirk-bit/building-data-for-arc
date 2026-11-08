# Solve notes

I am solving only from `challenge.json`.  I had already seen the task rule while repairing the generator, so this is an exposed solve; I am not consulting the generator, Racket source, reference solutions, private labels, or previous solution explanations during this phase.

Visible examples contain two to three disconnected hollow color-4 rectangles.  The outputs preserve all borders and background.  They fill the interior of the rectangle with the smallest interior area with color 2, fill the interior of the rectangle with the largest interior area with color 8, and leave a middle-sized rectangle unchanged.  Width alone is not sufficient: in training example 3 the widest but shallow top rectangle is left hollow while a narrower, taller frame receives 8.

Implementation plan: find 4-connected color-4 components, use each component's bounding box to calculate interior area `(height-2)*(width-2)`, sort by that area, and fill only the first and last interiors.  Inputs show distinct areas, so no tie policy is needed.
