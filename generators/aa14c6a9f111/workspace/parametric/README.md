# All outlines versus anchor-area selected fill

The canonical setting preserves the exact selected Racket source and completes
every same-color diagonal endpoint pair as a rectangle outline.

The alternate setting reconstructs the same ordered rectangles, measures the
first rectangle's area `A`, selects rectangle `(A - 1) mod n`, and fills only
that selected rectangle while retaining outlines for every other rectangle.
The first two demonstrations select different nonconstant indices and separate
area selection from fixed index, size rank, perimeter, and color shortcuts.

Sequential dependency:

1. **A** reconstructs the ordered rectangles and computes the first rectangle's
   input-derived area.
2. The intermediate is that area and the selected rectangle index.
3. **B** consumes the selected index to decide which rectangle receives a fill
   rather than only an outline.

The family supports 2–6 demonstrations, 1–4 independently revealable queries,
matched inputs across settings, disjoint and nested layouts, and a 30×30 nested
boundary stress case.
