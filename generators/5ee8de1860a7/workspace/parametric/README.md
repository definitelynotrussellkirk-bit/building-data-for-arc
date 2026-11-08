# Native parametric family: border to clockwise corner

`finish_rule=border_only` returns the exact canonical Racket source unchanged.

`finish_rule=clockwise_segment` is sequential:

1. replace the sole interior marker with a one-cell border in its color;
2. use the marker color to choose a cardinal ray, whose first hit is a newly
   created border cell;
3. recolor the clockwise border segment from that hit through the next corner
   with color 8.

The two settings share every generated input. Demonstration and query streams are
independent and prefix-stable for 2–6 demonstrations and 1–4 queries. The
fourth private query is 30×30. Generated scenes exclude marker color 8 so the
alternate remains distinguishable, while both Python and Racket still handle the
canonical source-domain color-8 marker without looping. `skip_border.rkt` is a
protected-Racket counterfactual that omits step 1, leaving no border endpoint
for step 2.

This directory is reviewer-ready evidence, not owner acceptance or training
admission.
