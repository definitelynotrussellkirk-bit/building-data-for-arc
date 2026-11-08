# `ca81880afbf3` square-hole relay family

`finish_rule=fill_only` is the exact canonical program.  Both settings first
fill square zero pockets inside color-5 components with color 2.  The alternate
then derives those color-2 components and connects aligned equal-area component
centers with color 4.  Inputs are matched across settings; demo/query streams are
independent and prefix-stable.  The fourth query is a 30×30 scene with five
square frames, two independent relay pairs, one unequal square, a rectangular
negative, and isolated component distractors.

`wrong_shifted_centers.rkt` preserves every canonical fill but shifts the derived
centers one column before the relay stage, isolating the intermediate consumed
by the second operation.

## Verification and handoff

The retained source inventory is `evidence/manifest.json`; focused receipts live
under `evidence/current/`. The final staged suite is 55/55, including repaired
ordinary-generator contracts, and the bounded family audit covers 16 seeds and
320 labeled pairs. The protected authoring preflight covers four jobs; public
projection produces 16 one-query files from four private episodes. These receipts
are source-bound reviewer evidence only; they do not grant owner acceptance or
training admission.
