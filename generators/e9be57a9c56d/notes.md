# Working notes: e9be57a9c56d

## 2026-10-23 parametric prototype review

This review adds a **task-local, unapproved prototype** only; production `generator.py` remains at version `3.0.0` and SHA-256 `b966566b12ca836cb93220215f1487130b6cecea073928ef94df5c5dd12d7273`. The canonical rule remains `f8100feef807`.

The proposed episode parameter is `extra_copy_gap ∈ {0,1}`. Setting `0` returns the canonical Racket source byte-for-byte. Setting `1` preserves template detection, same-color anchor selection, marker ordering, recoloring, and marker-gap reasoning, while adding one cell to every consecutive copy-chain step in both directions and both orientations. The value is selected once per episode; demo and query counts are independent.

`workspace/parametric/prototype.py` now provides reusable authoring support: deterministic episode construction, protected-Racket labeling for both settings, demonstration-only rejection of the opposite setting, four distinct queries, exact public-byte IDs, private metadata separation, duplicate-visible-payload rejection, source-bound manifests, and an evidence verifier that rejects source drift, unsafe/unrecorded paths, wrong hashes or byte counts, public label leakage, and private rule/parameter drift. Retained evidence uses seeds 10/11, three demonstrations, four queries, and one episode per setting under `checks/parametric-e9be57a9c56d-extra-copy-gap-v1/`.

Focused verification is 67/67 tests passed. A bounded adversarial pass covered 64 sampler inputs, 16 episodes, 112 episode inputs, 128 Racket/independent-geometry parity checks, both orientations, marker counts 3/4, template sizes 3..7, anchors 0..3, dimensions through 26×26, and 16 unique public IDs with no failures. The independent geometry shares the production parser, so this is not an exhaustive proof over all seeds or hypotheses.

The two assigned supplementary tickets were completed without peer source edits: `27f5eba1051c` retained one lawful Racket-confirmed witness against bounding-box-area ordering; `22d91d7a09d2` exactly replayed its existing local-table-versus-global-cycle audit witness and left that audit open.

## Review outcome

Version `3.0.0` replaces the v2 random rewrite. The baseline battery was `6 green / 2 advisory / 4 failed`: invalid texture-domain metadata and incomplete override observability failed lint/defect checks, `anchor_pos` was not fully provenance-bound, canonical profile support was absent, the semantic contract had no rival-bound claims, and the active augmented Racket target differed from the selected canonical source.

The repaired generator:

- exports only four exact, recoverable axes: orientation, marker count, template cardinality, and anchor position;
- rejects unknown/invalid controls and explicitly declares incompatible marker-count/anchor-index requests;
- cycles through the four canonical size/palette profiles while varying shape, reflection, colors, offsets, and difficulty-specific gaps;
- schedules non-2 template anchors with a color-2 distractor and schedules interior anchors;
- declares total `fixed_color_two_anchor` and `endpoint_only_anchor` rivals, witnesses, and a three-demo lesson hook;
- supplies a Python mirror for supplementary checks and an independent workspace oracle/probe for source-bound replay;
- synchronizes the active augmented Racket target to the existing canonical program without changing the canonical row or rule hash.

## Regression history

The first repaired battery still exposed public-profile shape and override-construction defects; those were fixed with focused tests. A later 300-lesson census exposed a subtler contract bug: the two rivals could return no grid when a wrong anchor projected off-canvas. Regression tests were added first (`task-tests-rival-red` and `task-tests-probe-red`), then both production and independent rivals were made total clipped-grid rules.

Final generator SHA-256: `b966566b12ca836cb93220215f1487130b6cecea073928ef94df5c5dd12d7273`.

Final evidence:

- inherited battery: 12/12 green with required query rotations;
- task-local portable suite: 53/53 passed, zero skips, including real Racket parity;
- large lesson census: 300/300 production lessons and 1,200/1,200 query rotations with no ambiguity, warning, materialization error, or scoring error;
- independent direct probes: 128 unique legal draws per band, all four canonical profiles at 32 each, fixed-color shortcut contradicted 96/128 and endpoint shortcut 64/128 per band.

See packet-root `REVIEW.md`, `DECISIONS.md`, and `QUESTION_ANSWER.md` for acceptance evidence and exact reproducer paths. Imported associated notes remain in `evidence/associated_notes.jsonl`.
## Current reviewer considerations

Source SHA-256: `b966566b12ca836cb93220215f1487130b6cecea073928ef94df5c5dd12d7273`.

# Decisions for `e9be57a9c56d`

## D1 — Replace the misleading public surface with exact observables

The exported axes are now only `orientation`, `n_markers`, `template_size`, and `anchor_pos`. Each is drawn through the keyed generation context, validated before construction, and exactly recovered by `observe_overrides` from the returned grid. Unknown keys, booleans masquerading as integers, out-of-range values, and unknown difficulty names fail fast. The only cross-axis incompatibility is explicit: an anchor index outside the requested marker count.

Rejected alternatives:

- Keeping `grid_h/grid_w` as controls was rejected because the old generator derived canvas size and did not honor those requests.
- Keeping `texture` and degenerate modes was rejected because `no_template`, `no_markers`, and `full_grid` were outside the task grammar while being advertised as normal values.
- Silent clamping was rejected because it makes override provenance and downstream audits non-falsifiable.
- Exposing low-level random quantities such as every gap was rejected because the assignment needed a truthful, compact contract rather than a maximal knob set.

Evidence: G1; `checks/before/result.json`, `checks/after-v4/result.json`, and `checks/task-tests-v4/result.json`.

## D2 — Ground the default distribution in canonical profiles

The canonical inputs occupy four `(height, width, palette_size)` profiles: `(23,17,4)`, `(16,22,4)`, `(23,14,4)`, and `(13,24,5)`. Default sample indices cycle through those exact triples, with a compatible orientation, marker count, and template size for each. Shapes, reflections, colors, offsets, and difficulty-dependent gaps still vary deterministically with seed and sample index.

Rejected alternatives:

- Relying on unconstrained random generation to eventually hit the profiles was rejected after the profile-floor check found zero support.
- Duplicating canonical grids was rejected because it would provide profile coverage without distributional diversity.
- Expanding to arbitrary canvas sizes in this repair was rejected because it weakens source support without teaching a new rule distinction.

The direct probe found all four profiles exactly 32 times in each 128-draw band, with 128 unique inputs per band. Evidence: G1/G5 and `checks/reference-probe-*.json`.

## D3 — Make the curriculum distinguish the actual semantic role

Canonical examples always make color 2 the template/anchor color, so “color 2 is the anchor” is a simpler rival that fits all four canonical pairs. Canonical examples also leave room for an endpoint-only anchor heuristic. The four-phase default schedule therefore uses three non-2 template-anchor phases and one color-2 phase, and any three consecutive draws include an interior anchor. When the template color is non-2, a singleton color-2 marker is deliberately present so the fixed-color rival makes a concrete different prediction.

Rejected alternatives:

- Always using color 2 was rejected because it directly preserves the strongest canonical shortcut.
- Varying color without including a color-2 distractor was rejected because absence of color 2 does not force the rival to disagree.
- Endpoint anchors only were rejected because they do not establish that color matching, rather than position, selects the anchor.
- Witness predicates without named rival predictions were rejected as weak semantic evidence.

Evidence: G2; `checks/shortcut-fixed-color/counterexample.json` and the final census.

## D4 — Three demonstrations, one query, and required rotations

`EXAMPLES_NEEDED = 3`. Production lessons are assembled from consecutive draws of the cyclic stream; each materialized lesson contains three demonstrations and one labeled query. Because a favorable fixed query position can hide an order-sensitive shortcut, every one of the four pair positions was also held out as query with `rotation_policy=require`.

Final measured verdicts on generator hash `b966566b12ca836cb93220215f1487130b6cecea073928ef94df5c5dd12d7273`:

- Production: `no_ambiguity_found`, 300/300 lessons, 1,200 pair positions, 0 scoring errors and 0 ambiguities.
- Query rotations: `no_ambiguity_found`, 1,200/1,200 rotations, 0 scoring errors and 0 ambiguities.
- Scope: the two declared rivals only; this is not proof against undeclared hypotheses.

The first 300-lesson run exposed partial rival outputs (290 production scoring errors and 1,177 rotation scoring errors). Rivals were then made total clipped-grid functions and the regression suite was extended before the clean rerun. Evidence: G4 and the two compressed census reports.

## D5 — Keep Racket authoritative and make the Python oracle independent

The selected canonical Racket program remains the label authority. The augmented active target was synchronized byte-for-byte to that existing program; no canonical row, rule hash, or rule behavior changed. `rule_mirror` is supplementary production code, while `workspace/reference_probe.py` independently re-implements parsing and geometry and can invoke the public Racket runner for parity.

Rejected alternatives:

- Treating the Python mirror as the authority was rejected because it could duplicate a generator-side mistake.
- Rewriting the canonical Racket rule was rejected because the defect was in generator support and authority drift, not in the selected task semantics.
- Deleting archival `raw_code` was rejected; it remains historical evidence and is explicitly classified as archival divergence.

Evidence: G3/G5 and `checks/after-v4/result.json`.

## D6 — Known limitations

The default schedule is deliberately concentrated on canonical profile support rather than every possible canvas dimension. Shape supports are connected, at most `3×3`, and cardinality `3..7`; markers number `2..5`, with gaps `2..5`. Exact overrides broaden combinations within that grammar, but this repair does not claim all combinatorial mixtures are equally frequent. Catalog approval and training admission remain outside reviewer authority.
