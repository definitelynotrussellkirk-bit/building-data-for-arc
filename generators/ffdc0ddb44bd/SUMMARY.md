# ffdc0ddb44bd — Crop the repeated shape

A rectangular 0-background grid contains three to five isolated, single-colour
objects. Candidate colours are distinct values from 2 through 6. Exactly one
translation-normalized shape appears two to four times; one differently shaped
object appears once. Select the repeated shape, take its first row-major
occurrence, crop it to its bounding box, and recolour every occupied cell 8.

The selected generator is version `3.0.1` and pins canonical rule hash
`29652af15048`. Its lawful default domain is:

- height 9..18 and width 14..22;
- majority count 2..4, always with one decoy;
- connected 3..6-cell objects fitting a 3×3 box, with a one-cell moat;
- exact observable overrides for `height`, `width`, and `majority_count`.

Colour and position are deliberately non-semantic. A four-profile schedule
crosses whether colour 2 is the decoy and whether the first row-major object is
the decoy. Four consecutive pairs therefore contain counterexamples to both
canonical shortcuts. The production lesson policy uses three demonstrations and
one query; all four query rotations are supported against the declared
competitors `color_2_object` and `first_object`.

Canonical-scale profiles are scheduled in every difficulty band before broader
size/count variants. This preserves the canonical 2-vs-1 case while retaining
diversity away from the examples.

The Racket rule was not changed. Finite declared-rival checks do not prove that
no undeclared hypothesis can fit a lesson; the source-bound Racket census and
adversarial probes remain necessary.
