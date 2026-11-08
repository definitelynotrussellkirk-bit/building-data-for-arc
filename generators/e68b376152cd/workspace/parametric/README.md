# e68b376152cd object-order family

`order_policy=spatial` is the exact canonical Racket program: extract every
nonzero 4-connected object, sort by bounding-box left edge (top edge as tie
break), tightly crop, and center-pack with one black column. The proposed
`largest_first` setting keeps the same extraction/cropping/packing but orders by
input-measured occupied area descending, with canonical spatial order as its tie
break.

Both settings use identical deterministic inputs. The first two demonstrations
already cross color order, top order, object height, shape holes, and area order.
The four-query bank is privately shuffled before prefix slicing; it includes a
30×30 scene with five objects and 70 occupied cells spanning all quadrants. The
input-dependent ordered crop list is the intermediate consumed by the packer;
using the opposite ordered list changes the final output.

The adapter supports 2–6 demonstrations and 1–4 queries. `audit.py` checks
finite scan/color/order/alignment/gap/fill rivals; native authoring preflight
remains the protected-Racket source of label and finite-setting evidence.
