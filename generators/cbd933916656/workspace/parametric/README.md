# Perimeter rank → selector-chosen bounding box

`finish_mode=rank_only` is the exact selected canonical rule: rank the three
same-color components by cardinal perimeter and recolor them 2, 4, and 8.

`finish_mode=selector_bbox` adds a sequential dependency. **Step A** constructs
that canonical ranked 2/4/8 grid. The common original component color is an
input-derived selector: 1 chooses the smallest-perimeter rank, 3 the middle rank,
and 5 the largest. **Step B** finds the selected rank color in the completed
intermediate and fills that component's bounding box. Skipping or misranking
Step A makes the selected rank color identify the wrong geometry.

The first three demonstrations use selector colors 1, 3, and 5 in order, so the
full mapping is taught at the declared minimum of three examples. Component
positions are shuffled independently of rank. Every scene deliberately makes
perimeter order differ from occupied-area order, and every component has gaps
inside its bounding box. The fourth query is a substantive 30×30 case with more
than ninety occupied input cells.

This is reviewer authoring evidence only. Owner source review, fresh native
qualification and exact-source acceptance remain separate.
