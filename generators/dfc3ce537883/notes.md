# Working notes: dfc3ce537883

Record design decisions, hypotheses, review findings, and unresolved questions here.
Imported associated notes retain original evidence/timestamps in `evidence/associated_notes.jsonl`.
## Current reviewer considerations

Source SHA-256: `a92953fceef84dbeb161142b0a3d0e3de646cdc6da5839952e44f1c72ac64fde`.

# Decisions for `dfc3ce537883`

## D1 — Pin the authority; do not edit it

**Choice.** Add `RULE_HASH = "6177794736be"` and leave the canonical Racket program unchanged.

**Rationale.** The existing rule correctly mirrors nonzero, non-divider cells from the left of the full-height color-9 divider to equal-distance positions on the right. Baseline rule-smoke and authority-sync were already green; the defect was an unpinned generator, not a wrong endpoint.

**Rejected alternative.** Rewriting or “simplifying” the Racket source would add authority risk without fixing the distribution, override, or teaching defects.

**Probe/failure mode.** Authority drift is checked by `rule_smoke`, `racket_lint`, `authority_sync`, the task-local hash assertion, and real-Racket parity in the focused tests. A future canonical program change must deliberately update the pin and rerun all of them.

## D2 — Advertise only exact, pixel-observable controls

**Choice.** Replace the old ten-control surface with six real axes: `grid_h`, `grid_w`, `n_cells`, `n_colors`, `layout`, and `axis_position`. Reject unknown, retired, mistyped, and out-of-range overrides before generation. Recover every requested value from the returned grid with `observe_overrides`.

**Rationale.** The baseline exposed singleton controls, silently ignored palette/texture names, and structural aliases that could not be verified from pixels. Exact controls are useful only when they alter lawful output and round-trip without relying on RNG bookkeeping.

**Rejected alternatives.** Keeping inert controls as “future options” would preserve false API promises. Marking all of them diagnostic would avoid some lint findings but would not improve training variation or make exact overrides useful.

**Probe/failure mode.** Boundary tests cover every axis in every difficulty band. Invalid values include booleans for integer axes, float counts, retired names, unknown keys, and enum misspellings. `checks/task-tests/result.json` records 28/28 passing tests.

## D3 — Separate malformed fixtures from the lawful distribution

**Choice.** Keep eight deterministic malformed scenes under the `texture` probe API, but remove them from ordinary `AXES` and require that a texture probe be explicitly requested. `self_check` rejects each fixture.

**Rationale.** The baseline ordinary texture domain mixed lawful palettes with `no_divider`, `no_left_content`, and `both_sides_filled`, then cross-product override tests generated thousands of predictable mismatches. Negative fixtures are valuable for validators, but not as ordinary training examples or claimed exact axes.

**Rejected alternative.** Deleting malformed probes entirely would lose useful regression coverage. Treating them as lawful degenerates would teach identity/undefined behavior and weaken the domain contract.

**Probe/failure mode.** `mutation_fixtures()` links each near-miss to this task and the regression suite asserts that all are rejected for a structural reason.

## D4 — Use constructive geometry over retry-and-underproduce placement

**Choice.** Generate connected components by frontier growth inside a mirrorable source region. Generate split scenes in two row-separated regions, guaranteeing exactly two components. Choose divider positions only where all mirrors are in bounds.

**Rationale.** Construction makes every declared cross-product legal at the minimum canvas and avoids silent underproduction after a capped retry loop. It also makes exact counts and connectedness directly observable.

**Rejected alternative.** Random cell placement plus rejection is shorter but can silently change requested counts, bias shapes toward easy placements, or fail near domain boundaries.

**Probe/failure mode.** Cross-product boundary tests run the minimum and maximum of every exact axis, and `self_check` verifies cell count, colors, component count, empty right side, divider uniqueness, and mirror destinations.

## D5 — Preserve canonical support explicitly

**Choice.** Reserve the `canonical` schedule profile for centered, connected, monochrome inputs of sizes `5x9`, `5x10`, or `6x11`, with 3–4 source cells. Cycle through the three canonical sizes across schedule periods.

**Rationale.** The repair should broaden the task without moving all mass away from its official scale and visual grammar. Explicit support is easier to measure than hoping random draws happen to resemble canonical examples.

**Rejected alternatives.** Making every sample canonical would retain both shortcut ambiguities. Removing canonical profiles entirely could make the generator semantically correct but distributionally ungrounded.

**Probe/failure mode.** `strict_canonical_like` is executable; profile-floor passed in every band. A test asserts the expected canonical profile on each cycle.

## D6 — Schedule independent teaching witnesses, not just frequencies

**Choice.** Use the four-profile cycle `canonical`, `split_multicolor`, `split_monochrome`, `connected_multicolor` and `EXAMPLES_NEEDED = 4`. Test every cyclic five-pair start and every possible held-out query.

**Rationale.** Individual witness frequency does not ensure that a complete lesson contains a counterexample. The selected cycle repeats each witness twice in every five-pair window, so one query removal cannot erase all evidence against either shortcut.

**Rejected alternatives.** Purely random variation could pass aggregate diversity while producing ambiguous lessons. Making every noncanonical pair both split and multicolor would entangle witnesses and narrow the distribution unnecessarily. A longer cycle would increase audit burden without improving this two-rival contract.

**Probe/failure mode.** The focused test `test_every_five_pair_schedule_survives_any_query_rotation` is exhaustive over schedule starts. The production census then sampled 300 lessons and 1,500 rotations with no ambiguity.

## D7 — Declare finite, executable rivals and witnesses

**Choice.** Add the rivals `largest_component_only` and `monochrome_copy`, their paired witnesses `split_source` and `multicolor_source`, and `lesson_identifiable` that checks demonstrations against the true endpoint rule.

**Rationale.** Both wrong rules fit the official monochrome connected pairs, so label correctness alone cannot prevent shortcut training. Executable rivals turn the concern into a reproducible lesson-level gate.

**Rejected alternative.** Natural-language warnings or witness counters alone cannot establish that a complete lesson refutes a rival on the query. Claiming uniqueness would overstate finite checks.

**Probe/failure mode.** Tests first verify that each rival really fits every usable canonical pair, then that each named witness creates an exact disagreement. The census iterates the generator's actual declarations rather than a copied rival-name list.

## D8 — Add a reusable source-bound probe

**Choice.** Add `workspace/reference_probe.py` for canonical-pair shortcut checks, cyclic lesson assembly, rival evaluation, and optional supported Racket CLI parity.

**Rationale.** Future agents need a small, task-local way to reproduce the semantic argument without importing private runner functions or reverse-engineering the large battery output.

**Rejected alternative.** Embedding all analysis only in one-off shell commands would make later review less reproducible. Moving it into shared infrastructure would exceed this assignment's allowed patch scope.

**Probe/failure mode.** The helper resolves runtime paths portably in the staged task-test environment; the retained first green attempt documents the initial path bug and the final portable test run validates the correction.

## Known limits

- The declared rival set is deliberately small and task-specific. Passing it does not prove a unique rule under unrestricted program induction.
- The five-pair guarantee assumes the current production policy of four demonstrations and one query drawn from consecutive accepted samples. The 300-lesson source-bound census verifies that policy as currently implemented.
- The generator does not cover more than two source components, more than three colors, or larger canvases. These are explicit domain boundaries rather than silent limitations.
- Off-center dividers are constrained to leave at least three mirrorable columns on each side; this supports the current source-count grammar and ensures in-bounds reflections.

## D9 — Native parametric family and promotion handoff (2026-10-24)

**Choice.** Add a separate native adapter under `workspace/parametric/` with
`followup = mirror_only | fill_contacted_frame`.  `mirror_only` is the exact
canonical Racket program byte-for-byte.  The alternative first performs the
same mirror, then uses the mirrored color-2 probe to select the uniquely
adjacent hollow color-3/4 frame and fills its bounding box by frame size
(3x3 -> color 1; 4x4 -> color 5).

**Teaching contract.** The setting is fixed for the whole episode.  The adapter
supports 2–6 demonstrations and exactly four distinct queries.  At the minimum
two demonstrations, target frame color and frame size both vary, which refutes
the retained constant-fill and fixed-frame-color rivals.  Inputs are sampled
independently of the private setting, and the public first-turn projection is
identical to single-query use without future-query or total-count hints.

**Sequential dependency.** Step A mirrors the left-side content across the
full-height color-9 divider.  Its input-dependent intermediate is the mirrored
color-2 probe and the frame it uniquely contacts.  Step B consumes that selected
frame to choose the bounding box and size-derived fill color.  A protected-Racket
wrong-frame counterfactual changes the final 30x30 output; the retained witness
is `checks/dfc3ce537883/sequential-dependency.json`.

**Evidence.** The focused/native task suite passes 42/42.  Protected Racket
parity covers canonical, alternative, and wrong-intermediate programs on a hand
case and substantive 30x30 case.  Native qualification passed both settings at
seeds 0 and 17 and bound exact source bytes in
`checks/dfc3ce537883/qualification/{qualification,execution}.json`.  The
source-bound inventory is `workspace/parametric/evidence/manifest.json`.

**Limits.** The finite self-audit covers `constant_fill_1`, `fixed_color_3`, and
`fixed_color_4`; it is not a uniqueness proof.  Reviewer status is **ready for
owner admission**, not accepted or training-enabled.  The owner must re-run
qualification and acceptance after integrating these exact bytes.
