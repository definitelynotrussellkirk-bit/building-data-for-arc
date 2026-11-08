# Working notes: 4f09f8bfa35a

## Current rule and source binding

Generator `3.0.0` is bound to canonical `RULE_HASH = "8710221699c5"`. Row 0 contains commands `2=identity`, `3=clockwise`, `4=180`, `5=counter-clockwise`. The rule erases row 0 for binary nonzero component discovery, selects the largest body component with bbox top/left tie breaks, crops the original body through that bbox, transforms the crop in command order, and packs copies with one-column gaps. The Racket authority was not changed.

## Reversed baseline decisions

The prior `2.1.0` sampler used one clear largest object and treated uniqueness as task law. That validator rejected the canonical test's lawful tie, the distribution omitted bbox cargo and tie-break evidence, exact controls were ignored, and unknown controls were accepted. Version 3 replaces it with a source-bound teaching grammar and strict exact-control grammar.

## Ordinary teaching distribution

Every ordinary input includes:

- four commands in a non-sorted permutation;
- one smaller earlier component;
- an eight-cell selected component;
- disconnected contrasting cargo inside its bbox;
- a multicolor selected crop;
- an equal-area later component.

Thus every pair refutes all nine declared rivals: first component, reverse tie, component-cells-only crop, identity commands, reverse/sorted order, swapped quarter turns, gapless packing, and monochrome crop. `EXAMPLES_NEEDED = 4`; the production sampler supports arbitrary one-pair query rotations against this registry.

## Exact controls

`n_commands 1..5`, `shape_size 2..12`, `n_distractors 0..3`, and `shape_color 1..9` are strict and pixel-observable. Explicit-control examples use a separate constructive layout. Unknown, non-integer, boolean, and out-of-range values reject.

## Retained evidence

- `counterexamples/selection-crop-command-witness.json`: lawful input refuting all nine rivals.
- `workspace/reference_probe.py`: independent mirror and observation helpers.
- `tests/test_generator.py`: 718 focused regression cases.
- `checks/counterexample/4f09f8bfa35a/racket.json`: canonical Racket replay of the witness.
- `checks/after-v2/result.json`: final 12-stage battery.
- `checks/lesson-census-final.json`: 300 lessons, 1,500 pairs, all 1,500 rotations clean.

## Known limits and open questions

The declared rival registry is finite and does not prove unique induction against every program. Ordinary samples intentionally use a narrow role layout and fixed component sizes to guarantee all witnesses in every pair; exact controls broaden those counts but are not semantic-witness-complete. Catalog training approval remains a maintainer decision independent of the green repair checks.
## Current reviewer considerations

Source SHA-256: `fbe9445ba720e1b8bc13af7ac2f373ce6b9ab13887438e62f60357aada477764`.

# Decisions for `4f09f8bfa35a`

## D1 — Preserve the canonical authority

**Prior choice:** the baseline prose approximated the task as “one clear largest template below a command row.”

**New choice:** pin `RULE_HASH = "8710221699c5"` and mirror the exact selected rule: erase row 0 for binary nonzero component discovery, select by size then bbox top/left, crop the original body through that bbox, apply command codes 2/3/4/5, and pack with one blank column.

**Reason/evidence:** the canonical test has a lawful largest-size tie, so the old unique-largest validator rejected authority data. Canonical acceptance and independent mirror equality are tested in `tests/test_generator.py`.

**Alternative rejected:** changing the Racket rule to match the old generator. The selected rule is authoritative and already consistent with all canonical pairs.

## D2 — Make selection semantics visible in every ordinary pair

**Choice:** include a small earlier component and an equal-area later component. The selected component is the earlier of the tied largest objects.

**Reason:** this simultaneously refutes “take the first body component” and “reverse the largest tie.” Relying on occasional random collisions would leave many lessons semantically weak.

**Failure mode checked:** the small earlier body cell is vertically continuous with a command in the raw input but becomes separate after row 0 is erased, matching the authority's actual data flow and reaching canonical object-count profiles.

## D3 — Teach bounding-box crop, not selected cells only

**Choice:** place a disconnected contrasting cargo pixel inside the selected component's bbox and preserve it in the crop.

**Reason:** `component_cells_only` fits every canonical pair, making it the strongest canonical-fitting shortcut. Every ordinary generated pair now breaks it. The exact retained witness is `counterexamples/selection-crop-command-witness.json`, verified by `checks/counterexample/4f09f8bfa35a/racket.json`.

**Alternative rejected:** simply adding a second color to the selected component. That refutes monochrome conversion but does not distinguish component-mask cropping from bbox cropping.

## D4 — Teach command meanings, order, and output packing

**Choice:** ordinary examples use all four commands in a non-sorted permutation and one-column output gaps.

**Reason:** one pair then refutes identity-only commands, reversed or sorted command order, swapped clockwise/counter-clockwise semantics, and gapless packing.

**Limitation:** ordinary examples always contain four commands. The exact-control path supports one through five commands, but those control-focused examples are not claimed to carry every semantic witness simultaneously.

## D5 — Separate semantic teaching from exact-axis experiments

**Choice:** default calls use the witness-rich semantic layout. Any explicit axis request uses a simple constructive layout whose four advertised values are recoverable exactly from pixels.

**Reason:** forcing every cross-product value to retain all nine witnesses would couple unrelated axes and make small shape sizes or zero distractors impossible. Separate paths keep exact controls honest without weakening production lessons.

**Failure modes checked:** full legal cross-product over three bands; unknown keys; booleans; strings; floats; out-of-range values; hash-seed independence; input mutation; output diversity.

## D6 — Validator scope

**Choice:** accept canonical largest ties and reject malformed/ragged/non-ARC grids, missing commands, missing or one-cell selected components, illegal row-0 colors, invalid bridge structure, and outputs exceeding 30×30. `strict_canonical_like` separately enforces one of the observed canonical profiles.

**Reason:** the baseline mixed a distribution preference (“unique largest”) into task law. The new split keeps `self_check` lawful and uses strict profiling only where the battery asks for canonical-shaped support.

## D7 — Lesson assembly

**Choice:** four demonstrations and one query (`EXAMPLES_NEEDED = 4`); every default pair independently refutes every declared rival. Query order is therefore unrestricted for the declared registry.

**Evidence:** required-rotation battery pass plus `300` production lessons, `1,500` materialized pairs, and `1,500` one-pair holdouts with zero ambiguities in `checks/lesson-census-final.json`.

**Limit:** this is finite evidence against nine declared deterministic rivals, not a proof against all programs.
