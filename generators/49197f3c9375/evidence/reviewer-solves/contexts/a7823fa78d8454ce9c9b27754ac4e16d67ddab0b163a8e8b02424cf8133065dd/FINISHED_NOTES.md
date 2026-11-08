# Solve work log

This is an exposed post-repair solve. I had already seen the task semantics while repairing the generator, so `earlier-exposure` will be declared `yes`; during this solve I used only the displayed examples.

Visible-example hypothesis:

1. Split the foreground into monochrome 4-connected components.
2. Normalize each component to its tight crop and compare shapes modulo all rotations and reflections.
3. The five components form two equivalent pairs plus one unmatched shape.
4. Select the unmatched component and return its four-neighbor boundary in its original color, cropped tightly.

Checks against the three displayed examples: the selected colors are respectively 2, 8, and 3. The filled 3x3 unmatched examples become hollow 3x3 rings, which distinguishes boundary extraction from simply returning the whole component.
