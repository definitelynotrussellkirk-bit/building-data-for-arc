# Native run-axis family for `0a9ee3cbb232`

The default `run_axis=horizontal` resource is the selected canonical Racket
program byte-for-byte.  The nearby `vertical` setting changes only Step A:
it counts maximal vertical rather than horizontal runs of colors 3 and 2.
Step B is shared: pack the derived `(n3,n2)` intermediate into the 2x3 tally.

`native.py` constructs setting-blind matched inputs, supports 2–6 demonstrations
and 1–4 independently prefix-stable queries, shuffles the complete private query
bank before prefix selection, and includes a dense 30x30 boundary-touching
stress case. `audit.py` is the reusable bounded teaching/projection/Racket
checker.  These are reviewer-authored prototype artifacts only; they grant no
owner acceptance, canonical approval, measured training gain, or training
admission.
