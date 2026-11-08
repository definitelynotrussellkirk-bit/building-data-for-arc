# Current notes: 01ab62800c73

## Intended rule and authority

`RULE_HASH = "6f47f78828c8"` pins the unchanged selected Racket authority. Read the nonzero values in row 0 from left to right as commands: `1` flip left/right, `2` flip up/down, `3` rotate clockwise, and `4` rotate 180 degrees. Crop rows 1+ to the nonzero body bounding box, then execute every command sequentially. Values 1–4 below row 0 are payload colors, not commands.

## Current generator design

Version 3.0.0 uses a deterministic four-profile schedule: `canonical_order`, `code_payload`, `multicolor_payload`, and `disconnected_body`. Ordinary generation uses only lawful textures. Generated bodies have eight distinct dihedral orientations; the validator deliberately accepts the broader canonical manifold when at least four orientations remain distinct. Exact axes are `grid_h=5..14`, `grid_w=6..14`, `n_ops=1..4`, and the three ordinary textures, with strict scalar and unknown-key rejection plus `observe_overrides` receipts.

Every default multi-command draw is selected to disagree with sorting the commands and with applying only the first or last command. Four demonstrations are required. The executable lesson contract checks the named rivals `sort_commands`, `first_command_only`, `last_command_only`, and `strip_code_payload`.

## Reversed decisions

The previous generator mixed invalid `no_ops` and `empty_body` fixtures into the advertised ordinary texture domain. They are now removed rather than sampled as training inputs.

The previous random command sampling did not guarantee an order witness. The new sampler explicitly chooses compositions whose result differs from sorted, first-only, and last-only execution. A key correction during review was recognizing that canonical command sequence `[3,1]` is not itself a discriminator on the canonical body: accidental body symmetry lets the sorted-command rival fit all three labeled canonical pairs. The retained generated counterexample is `counterexamples/sort-commands-fits-canonical.json`.

The first revised validator required eight distinct orientations and rejected lawful canonical inputs. It was narrowed to reject severe symmetry while generation retains the stronger eight-orientation guarantee. The initial canonical-profile schedule also reached only 21.7% in the battery profile sample; two of four profiles now use canonical-size/palette envelopes, yielding a comfortable floor.

## Evidence and limits

Final generator SHA-256: `449c1d95c75158329e3b497aa724f1124f613e6442433a626c13a4cf72527318`.

The final strict battery is 12/12 green and focused task tests are 8/8. A fixed-seed exhaustive receipt covers all four schedule starts in all three bands and every query rotation: 12 lessons, 60 labeled pairs, 60 rotations, no ambiguity. A wider production-sampler census covers 300 lessons, 1,500 pairs, 1,500 rotations, and 1,500 unique inputs, again with no ambiguity against the declared rivals.

These are finite checks against named competitors, not a proof of unique induction against every possible rule. Exact overrides can request `n_ops=1`, which is lawful but cannot expose command order in isolation; the default lesson schedule uses multi-command order witnesses. Generation is intentionally narrower than `strict_canonical_like`, which must continue to accept all labeled canonical inputs.
## Current reviewer considerations

Source SHA-256: `449c1d95c75158329e3b497aa724f1124f613e6442433a626c13a4cf72527318`.

# Generator decisions: 01ab62800c73

Final generator SHA-256: `449c1d95c75158329e3b497aa724f1124f613e6442433a626c13a4cf72527318`. The selected Racket rule was not changed.

## D1 — Treat row 0 as an ordered program

**Original choice:** The baseline summary said commands were sequential, but random generation did not guarantee that order mattered in any complete lesson. The original rationale for its exact command distribution is unknown.

**New choice:** Default multi-command sequences are selected only when the independent marker matrix produces different results under intended order, sorted order, first-only execution, and last-only execution. Four demonstrations are assembled from a deterministic four-profile schedule.

**Alternatives rejected:** Pure random commands could produce commuting or cancelling compositions. Hard-coding canonical `[3,1]` alone was also rejected after a probe showed that sorting fits all three labeled canonical pairs because of the canonical bodies, not because the operations commute universally.

**Probe/evidence:** `checks/counterexample/probe.json`, `checks/counterexample/racket.json`, and focused test `test_canonical_sorting_shortcut_fits_all_labels_but_generated_cases_refute_it`.

**Failure mode/limit:** An explicit `n_ops=1` override is lawful but cannot teach ordering by itself. The production schedule uses multi-command witnesses.

## D2 — Separate command location from command-colored payload

**Original choice:** The baseline allowed code colors in the body but did not schedule them or declare a rival, so this distinction could be absent from a lesson.

**New choice:** `code_payload` and `multicolor_payload` are dedicated schedule profiles. Values 1–4 in rows 1+ are ordinary payload; only nonzero row-0 values are commands. The `strip_code_payload` rival makes the distinction executable.

**Alternatives rejected:** Reserving colors 1–4 exclusively for commands would simplify generation but change the stated task grammar and encourage a false color-role shortcut.

**Probe/evidence:** Four-profile schedule census, `checks/schedule-period-s0.json`; wider census, `checks/lesson-census-100.json`.

**Failure mode/limit:** The finite rival checks do not enumerate every possible misinterpretation of command-colored payload.

## D3 — Use lawful ordinary textures only

**Original choice:** `no_ops` and `empty_body` appeared in the same advertised texture domain as ordinary examples. The likely intent was negative testing, but no explicit rationale was recorded.

**New choice:** Ordinary `texture` values are only `plain`, `code_colored_body`, and `multicolor_body`; `DEGENERATE_TEXTURES` is empty. Malformed grids remain covered directly by focused validator tests instead of being sampled as lessons.

**Alternatives rejected:** Marking the invalid fixtures as lawful degenerates would make them eligible for training and leave override combinations inert.

**Probe/evidence:** Baseline defect-lint and override failures in `checks/before/`; final 12-stage battery in `checks/after-final2/`.

## D4 — Guarantee asymmetric connected and disconnected bodies

**Original choice:** The baseline attempted to reject a few symmetries in a connected polyomino but had a simple fallback and no disconnected support.

**New choice:** Ordinary generated masks have all eight distinct dihedral orientations and one or two four-connected components. The disconnected profile specifically prevents “single connected shape only” from becoming an accidental grammar rule.

**Alternatives rejected:** Requiring eight orientations in `self_check` was tried and rejected because it excluded labeled canonical inputs. Generation keeps the strong guarantee while `strict_canonical_like` accepts the broader task manifold and `self_check` rejects only severe symmetry.

**Probe/evidence:** Intentional failed run `checks/tdd-red-canonical-selfcheck/`, correction in `checks/tdd-green-3/`, final focused tests and battery.

**Failure mode/limit:** The generator samples masks up to 6×6 inside larger canvases. It does not claim exhaustive shape support.

## D5 — Make every advertised axis exact and observable

**Original choice:** The baseline advertised `grid_h=6..14` and `grid_w=7..14`, but band-specific `draw_int` bounds rejected many advertised values. Unknown axes and invalid scalars were silently accepted, and `n_ops` lacked a provenance observer.

**New choice:** Strict call validation rejects booleans, non-integers, negative sample indices, unknown axes, and unknown difficulties. Every legal `grid_h=5..14`, `grid_w=6..14`, `n_ops=1..4`, and texture value is honored in every band. `observe_overrides` reconstructs all four realized values.

**Alternatives rejected:** Declaring thousands of band/axis combinations incompatible would preserve surprising behavior and add unnecessary contract complexity.

**Probe/evidence:** Baseline override report under `checks/before/`; exhaustive boundary combinations in `test_axis_overrides_are_exact_across_all_bands`; final override stage green.

**Failure mode/limit:** Exact small canvases constrain mask size by construction, but generation raises rather than silently clamping if an internal invariant cannot be met.

## D6 — Restore the canonical envelope deliberately

**Original choice:** Zero of 60 baseline draws matched either canonical `(height,width,palette-size)` profile.

**New choice:** `canonical_order` and `disconnected_body` use height 5, width 6 or 7, and a four-color total palette when unoverridden. The other two profiles retain broader dimensional and texture diversity.

**Alternatives rejected:** One canonical-sized profile out of four produced only 21.7% in an intermediate profile-floor sample and failed the 25% requirement. Making every profile canonical-sized would sacrifice useful support.

**Probe/evidence:** `checks/after-final1/` preserves the failed 21.7% iteration; `checks/after-final2/` is green. The focused 80-draw test requires at least 35 hits per band.

**Failure mode/limit:** Profile matching uses exact canvas/palette signatures, not semantic equivalence to every canonical body.

## D7 — Pin and mirror the unchanged authority

**Original choice:** The baseline omitted `RULE_HASH` and had no executable Python mirror or canonical regression.

**New choice:** Pin `RULE_HASH="6f47f78828c8"`, implement an independent pure-Python mirror, and test all three labeled canonical pairs against it. The selected Racket rule remains authoritative and unchanged.

**Alternatives rejected:** Editing the Racket rule was unnecessary because rule-smoke and authority checks already showed the authority was correct; the defects were in generation, validation, and teaching.

**Probe/evidence:** Final rule-smoke and authority-sync stages in `checks/after-final2/`; Racket counterexample receipt in `checks/counterexample/racket.json`.

## D8 — Use an executable lesson contract and two census scales

**Original choice:** The baseline had no `strict_canonical_like`, witnesses, rivals, or lesson hook.

**New choice:** Declare four named rivals and a `lesson_identifiable` hook. Test every declared schedule start at fixed seed 0 in all three bands and hold out every one of the five materialized pairs in turn. Also test 100 independently seeded production lessons per band with all query rotations.

**Alternatives rejected:** Relying on witness frequency alone was rejected because a feature may be present yet redundant. Checking only the 12-lesson semantic smoke was rejected after discovering the canonical-fitting sorting shortcut.

**Probe/evidence:** Exhaustive fixed-seed result: 12/12 lessons, 60/60 rotations, zero ambiguity (`checks/schedule-period-s0.summary.json`). Wider result: 300/300 lessons, 1,500/1,500 rotations, zero ambiguity (`checks/lesson-census-100.summary.json`).

**Failure mode/limit:** These results cover the declared rivals and sampled support only. They do not prove unique induction against undeclared hypotheses or every seed.
