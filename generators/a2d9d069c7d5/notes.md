# Working notes: a2d9d069c7d5

## Current decision — review-49d4129a9b4d2641

Keep canonical rule `e2513b1ebd3d` and the selected generation algorithm unchanged.
Add an opt-in proposed family in `workspace/parametric/`: episode-fixed object
versus area voting and strict versus inclusive ties. The default is object
voting with strict comparison, matching the three canonical train pairs and
one test pair. Settings and matching Racket programs stay private; each public
episode teaches the setting with four identifiable demonstrations and supports
four distinct query inputs. Details and runnable commands are in that README.

The useful reasoning is segmentation into monochrome 4-connected squares,
parity, aggregation, and conditional plus retention alongside unconditional
center marking. Neither object count and area nor strict and inclusive ties
should be interchangeable shortcuts. Four hand-counted witness profiles
separate those choices. Certification covers exactly four settings and eight
declared shortcuts, using demonstration labels only; it is not a universal
induction claim. The sampler holds input scenes fixed across settings for the
same seed, and input-derived public identities exclude hidden labels/metadata.

The existing three diagnostic textures are lawful layouts. Declare
`LAWFUL_DEGENERATE_TEXTURES = DEGENERATE_TEXTURES` so their intended status is
explicit; a focused test generates and self-checks each. This repairs the
metadata omission behind the retained defect-lint finding. It does not itself
clear the historical review index or assert that a full battery was rerun.
The generator version, RULE_HASH and emitted generation behavior are unchanged.

Independent bounded review reproduced two private/reference-label validation
holes: Python equality accepted `7.0` as `7` and `False` as `0`. Exact integer
color and shape validation now precedes comparisons and export, with regression
tests. `write_batch` remains a projection API; external callers must build or
explicitly replay episodes before export. Bounded sampler/retry checks also
covered a crowded impossible layout and the 64-retry distinctness limit.

Next: replay the included focused tests and inspect the proposed curriculum
before choosing production integration or training admission. No broad
generator battery or distribution census was required for this metadata and
prototype scope. Full physical packet extraction was infeasible in the review
environment; the accompanying tools report archive-space needs and preserve
official delta validation using a complete verified in-memory source view.

Imported associated notes retain their original evidence and timestamps in
`evidence/associated_notes.jsonl`; retained audit files are unchanged.
