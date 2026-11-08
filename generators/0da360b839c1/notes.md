# Working notes: 0da360b839c1

Review assignment `review-f01141c33d0599ef` repaired the imported input generator without changing the selected Racket authority.

Final generator SHA-256: `d352b5c3d77261a1ae98c0953e2c37d63e349ef79ef9180b6d391228c1209eee`.

Key retained evidence:

- Baseline defects: `checks/before/checks/0da360b839c1_before_battery_summary.json`.
- Final 12-stage battery: `checks/after/checks/0da360b839c1_after_battery_summary.json`.
- Whole-lesson rival census: `checks/lesson_probe_100_per_band.json`.
- Test-first logs: `checks/tdd/`.

Known limits: finite named-rival coverage; overlapping cyclic lessons; no model-training claim; catalog approval remains external.

Imported associated notes retain original evidence/timestamps in `evidence/associated_notes.jsonl`.
## Current reviewer considerations

Source SHA-256: `d352b5c3d77261a1ae98c0953e2c37d63e349ef79ef9180b6d391228c1209eee`.

# Decisions for `0da360b839c1`

All decisions below are bound to final generator SHA-256 `d352b5c3d77261a1ae98c0953e2c37d63e349ef79ef9180b6d391228c1209eee`.

## D1 — Preserve the selected Racket authority

- **Original rationale:** Unknown from the imported notes. The baseline selected rule already matched the canonical examples, passed Racket smoke, and synchronized with the selected authority.
- **Choice:** Do not edit the Racket rule. Pin its normalized hash as `RULE_HASH = "05f942009299"`; use a separate Python mirror only for tests/probes.
- **Alternatives rejected:** Rewrite the rule to match the generator description; make Python the output authority. Either would expand scope and risk changing task semantics when the defect was in input generation.
- **Probes:** Before and after `rule_smoke`, `authority_sync`, canonical-pair unit test, and mirror parity.
- **Failure modes / limits:** One archival bank entry remains divergent, although selected sources synchronize and execution parity passes. Python parity is finite, not a proof for all grids.

## D2 — Replace broad/false axes with exact composable controls

- **Original rationale:** The imported generator exposed broad dimensions, singleton pseudo-axes, and ordinary textures including negative fixtures; their intended training value was undocumented.
- **Choice:** Expose only `grid_h 7..13`, `grid_w 7..13`, `anchor_dr -1..1`, `anchor_dc -1..1`, `n_cells 4..8`, `n_colors 2..3`, and four named `layout_profile` values. All exact cross-products are constructible, so `INCOMPATIBLE_OVERRIDE_COMBINATIONS` is empty.
- **Alternatives rejected:** Keep broad ranges and silently clamp; preserve dead texture aliases; encode many incompatibility exceptions. Those make metadata untrustworthy and weaken reproducibility.
- **Probes:** Observable-axis unit test and official override checker over 39,060 draws.
- **Failure modes / limits:** The exact domain is deliberately narrower than every geometrically possible point-reflection grid. It optimizes truthful control and canonical support rather than exhaustive geometry.

## D3 — Use a period-four lesson schedule

- **Original rationale:** The imported random/blob generator had no complete-lesson guarantee. Pooled diversity cannot prove that any one lesson contains the distinctions needed to infer the rule.
- **Choice:** `sample_index mod 4` selects `one_side`, `split_side`, `axis_cross`, `swap_pair`; therefore every four consecutive demos contain all four profiles regardless of start residue.
- **Alternatives rejected:** Independent random profile draws (can omit rare witnesses); a longer period (more cyclic windows and weaker minimum lesson contract); hard-coded one profile per difficulty (confounds concept with band).
- **Probes:** Unit test over every cyclic start and every band; task-local 100-seed cyclic census.
- **Failure modes / limits:** Periodicity is predictable and creates overlap. Generalization examples are concentrated in `swap_pair`; future curriculum changes must preserve the cyclic-window guarantee.

## D4 — Profile-specific input choices

| Profile | Input choice | Reason | Rejected alternative / failure caught |
|---|---|---|---|
| `one_side` | 7×7, centered anchor, connected cells in one open half-plane, 4 cells, 2 colors | Matches one canonical profile and gives a simple point-reflection demonstration. | Anchor-only or 1-color fixtures hide movement/color preservation; arbitrary blob sizes starved canonical support. |
| `split_side` | 8×8, anchor offset by one column, two disconnected components, 4 cells, 2 colors | Matches another canonical profile while refuting grid-center and largest-component shortcuts. | Always-centered anchors let `grid_center` survive; one component lets partial-object rules survive. |
| `axis_cross` | 9×9, centered anchor, cells on both anchor row and column, 4 cells, 2 colors | Matches the third canonical profile and separates point reflection from horizontal-only or vertical-only reflection. | Diagonal-only supports can make one-axis behavior harder to diagnose. |
| `swap_pair` | 10..13 scale by band/block, off-center anchor, 4..8 cells, 3 colors, differently colored occupied antipodes | Supplies broader scale/cardinality and the counterexample needed to refute “move only into empty destinations.” | Unoccupied destinations allow `empty_destination_only`, which fits all public canonical pairs, to survive. |

Rotations are deterministic from the generator context so the semantic role remains fixed while orientations vary. Every reflection is constructed in bounds.

## D5 — Validate the real task domain, not only shape

- **Choice:** `self_check` enforces literal ARC colors, rectangular 7..13 grids, one center-near 9, 3..8 source cells, 2..3 non-anchor colors, in-bounds antipodes, recognized profile geometry, and non-identity output.
- **Alternatives rejected:** Accept negative/degenerate textures as ordinary data; clip out-of-bounds reflections; treat Python `bool` as a color integer.
- **Probes:** Targeted malformed-grid unit test, official self-check, defect lint, and distribution gate.
- **Failure modes / limits:** Recognition intentionally accepts only the four designed geometry classes; a lawful but novel geometry outside them is rejected.

## D6 — Declare executable rivals and witnesses

- **Choice:** Declare seven concrete rivals and six witness predicates. Mark `above_only` and `empty_destination_only` as canonical shortcuts only after verifying they fit all usable canonical pairs. `lesson_identifiable` evaluates the actual four demonstrations against the declared competitor functions.
- **Alternatives rejected:** Narrative-only comments; witness-frequency counts without rival execution; copying a rival-name list into a separate probe.
- **Probes:** Canonical-fit unit test, official semantic gate, and source-bound lesson census that reads `CANONICAL_SHORTCUTS` and `LESSON_COMPETITORS` directly.
- **Failure modes / limits:** The competitor set is finite and human-selected. An unlisted shortcut can still exist.

## D7 — Add a source-bound whole-lesson probe

- **Choice:** Build `workspace/lesson_probe.py` to mirror production lesson assembly, bind hashes, verify the independent oracle on canonical pairs, count unique inputs separately from overlapping pair occurrences, test 100 pinned lessons per band, and exhaust all cyclic starts of the small schedule.
- **Alternatives rejected:** Rely solely on the 12-lesson smoke gate; report individual witness frequencies as lesson identifiability; run model training to test a generator-level contract.
- **Probes:** `tests/test_lesson_probe.py` first failed because the tool did not exist, then passed; the final 100-per-band report is retained.
- **Failure modes / limits:** Full census outputs use the Python oracle. Live Racket evidence is retained separately; future rule edits must invalidate/re-run the probe through its source hashes.

## D8 — Keep the solve disclosure conservative

- **Choice:** Prepare the solve only after final generator bytes, consult only the visible challenge during the episode, record earlier exposure as `yes`, and report only 4/4 visible checks.
- **Alternatives rejected:** Calling it blind; consulting the rule again; inferring masked-query correctness from visible success.
- **Limit:** This solve is useful as an execution sanity check and work log, not independent evidence that an unexposed solver would infer the rule.
