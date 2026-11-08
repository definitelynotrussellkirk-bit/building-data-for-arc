# Parametric family: dilation-hole behavior

`hole_behavior=sealed` preserves the exact selected canonical Racket program: compute each object's enclosed-hole count before and after one clipped 3×3 dilation, select the unique object whose count decreases, then crop the **original** object and recolor it 8.

`hole_behavior=persistent` uses the same setting-independent scenes but selects the unique holed object whose count remains positive and unchanged. Every scene contains one object of each class plus solid distractors. Two constructive demonstrations swap target size, position, color rank, and void-area rank so fixed-position, fixed-color, largest/smallest, and first/last-holed shortcuts do not survive the declared minimum.

Sequential dependency:

1. **A:** segment objects and compute `(holes_before, holes_after)` after 3×3 dilation.
2. **Intermediate:** the per-object metrics and the unique index satisfying the episode setting.
3. **B:** crop and recolor the original cells of that selected object.

B cannot choose an output crop before A identifies the input-dependent object. The protected causal witness uses the other qualified setting as a wrong-intermediate counterfactual.
