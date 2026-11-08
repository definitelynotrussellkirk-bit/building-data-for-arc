# Native tile-order family

This proposed native family extends the retained width-only prototype. The
production generator, canonical authority and its approval are unchanged.
Reviewer qualification is evidence for owner intake; it is not owner acceptance
or training admission.

## Rule settings

| Parameter | Values | Meaning |
|---|---|---|
| tile_width | 2, 3 | Width of full-height adjacent column tiles |
| order_mode | reverse, densest_prefix | Reverse every tile, or the prefix ending at the leftmost most-populated tile |

The default {"tile_width":2,"order_mode":"reverse"} returns the exact selected
canonical program, byte for byte. Every rule preserves column order inside each
tile. For densest_prefix, count **nonzero cells** over the entire height of each
tile, select the leftmost maximum, then reverse tile order from the first tile
through that tile, inclusive. The suffix stays unchanged. Ties and all-zero
grids are total: the leftmost maximum is selected.

This is a count-to-endpoint-to-permutation dependency. The prefix endpoint is
computed anew from each input. It is contextual selection followed by a spatial
operation, not an iterative state simulation. A wrong endpoint gives a different
final grid on the retained causal witness.

## Sampling and teaching

adapter.py loads native_family.py by exact adjacent path. That implementation
reuses the historical prototype.py motif vocabulary and width-reversal mirror.
The old three-demo/one-query builder and its historical evidence remain intact;
the native API and audit_native.py are the current path.

`generate(seed, settings, demos=3, queries=4)` supports **2–6 demonstrations**
and independent **1–4 queries**. Four queries are the normal training request.
Seeds are literal integers from 0 through 2**63−1. Invalid booleans, settings,
counts and grid cells are rejected. Ordinary use is centered on three demos.

All settings share exactly the same inputs for a seed. The sampler creates one
six-demo/four-query plan independently of settings and requested counts. The
first two demos are selected jointly for every setting; requesting more demos
or fewer queries returns prefixes without changing earlier inputs. Color and
geometry streams do not depend on the selected rule.

Inputs contain the source family's oriented 2×2 hook, checker, corner and gap
motifs in two nonzero colors on black. The native sampling domain has even
heights from 6 to 30 and widths divisible by six, from 6 to 30. The four queries
use 6×6, 12×18, 24×24 and 30×30 grids. Density, palettes, motif placement and
population counts vary; the large scene contains substantial content throughout
the canvas. These rectangles and large scenes extend the source motif grammar;
they are **not** claimed to satisfy the unchanged production validator, whose
strict calibrated domain is even squares through 20×20.

The executable transformations support the broader 1–30 rectangular domain
with width divisible by the setting's tile width. Width-six queries can reduce
the width-three prefix rule to identity or full reversal. Larger demonstrations
establish which rule applies before that small boundary is queried.

The finite hypotheses are the other three settings, identity, whole-row
reflection and within-tile reflection. Prefix settings also test top-row-only
and bottom-row-only selection, rightmost tie selection, occupied two-row-band
count, color-value sum, fixed second/middle endpoints, exclusion of the selected
tile, and suffix reversal. Band count means occupied 2-row bands within each
full-height tile; it is motif count for width two, not for width three.

At most 48 constructive candidate scenes are considered. The first two selected
demos distinguish every setting and refute each declared rival that would
disagree on any of the four planned queries. A failure to find this two-demo
cover is an explicit bounded rejection, never a short or mislabeled episode.
The query-aware selection uses the controller's private query inputs; those
inputs and their answers are not exposed in demonstration metadata. This is a
finite teaching guarantee for the generated lesson, not uniqueness against all
programs or a measured learning result on unseen queries.

## Public/controller separation

The adapter returns a private authoring object with four query labels. Use the
existing controller's sequential reveal: one query input at a time, following
the previous answer, without a total-count/final-turn hint. There is no new turn
controller or training loop here.

The audit writes only the first-query view under public/, using exact
`reviewer_support.public_challenge_bytes` and its SHA-256 filename. That view has
only train input/output pairs and one test input, with no settings, seed,
program, query answer, or future query. It is byte-identical to requesting one
query directly. Complete four-query episodes, programs and rival labels are
private evidence; do not send them to the model as an initial challenge.

## Reproduce from the outer review packet

Use the passing Python interpreter from review.py python-check; in this return
that is WORK/.venv/bin/python. Outputs must be new directories.

```sh
WORK/.venv/bin/python review.py run python3 -m pytest -q generators/997c17fd6870/tests/test_native_parametric.py generators/997c17fd6870/tests/test_parametric_tile_width.py generators/997c17fd6870/tests/test_review_repairs.py

WORK/.venv/bin/python review.py run python3 generators/997c17fd6870/workspace/parametric/audit_native.py --out generators/997c17fd6870/workspace/parametric/evidence/new-audit

WORK/.venv/bin/python review.py run python3 -m arcpuzzles parametric qualify 997c17fd6870 --seed 0 --seed 17 --demos 3 --queries 4 --out ../checks/997c17fd6870/qualification --summary
```

The native manifest helper owns the current source/evidence inventory. After an
edit, recreate that inventory with an explicit replacement hash, then qualify
again. The owner must qualify and accept the exact integrated live source.
Changing prototype source invalidates qualification; a green test alone does
not preserve acceptance. The preexisting aggregate task-test fixture still has
a fixed-depth data path; its separately recorded preflight failure is not a
failure of these focused native tests or of native qualification.
