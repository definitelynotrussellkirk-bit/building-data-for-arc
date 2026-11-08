# Working notes: b83ad00fc681

Record design decisions, hypotheses, review findings, and unresolved questions here.
Imported associated notes retain original evidence/timestamps in `evidence/associated_notes.jsonl`.
## Current reviewer considerations

Source SHA-256: `30ec6f1ea881bb0ed60500f02ba73904ba22d24641c3930d14ee6ba2b567d3e2`.

# Decisions for `b83ad00fc681`

No selected-task associated note supplied a prior design rationale, so baseline intent beyond the canonical examples was treated as unknown. Each decision below names the alternative considered, the probe used, and the remaining limitation.

## D1 — Keep the Racket authority unchanged

**Choice.** Preserve the catalog program and pin `RULE_HASH = "46157a601fce"`; change only the Python generator, tests, notes/summary, and workspace probes.

**Rationale.** The canonical rule is coherent: read a visible top dictionary, identify each prototype by its unique minimum-color anchor, and stamp it at matching body markers. The baseline rule smoke and authority synchronization already passed; the defect was distributional and contractual, not a mislabeled authority.

**Alternative rejected.** Rewriting the Racket rule to accommodate broader/noisier inputs. That would add authority risk without repairing the actual fixed-dictionary shortcut.

**Probe.** Before/after rule smoke, Racket lint, and authority synchronization in the battery; independent Python/Racket parity on 39 inputs in `checks/sampler-audit-final.json`.

**Failure mode / limit.** The archival bank raw-code copy remains divergent, but selected execution parity is `PASS`; no archival file was edited.

## D2 — Preserve a four-row dictionary and fixed row-4 divider

**Choice.** Keep dictionary height at four and require exactly one full color-9 divider at row index 4, with color 9 otherwise limited to full separator columns.

**Rationale.** This is the stable structural cue shared by all canonical examples and keeps parsing unambiguous while allowing substantial variation inside panels and the body.

**Alternatives rejected.** Variable dictionary height, partial separators, extra color-9 noise, and divider relocation. Those are broader ARC variants, but they would change the teaching grammar rather than repair the assigned generator.

**Probe.** Destructive-mutation tests in `tests/test_generator.py`, strict parsing, 600-draw semantic gate, and 300-draw standalone audit.

**Failure mode / limit.** A solver may legitimately use the fixed row-4 cue; this is an intentional domain restriction documented in `INVARIANTS`, not a hidden accident.

## D3 — Use three or four randomized panels

**Choice.** Advertise and exactly honor `n_panels ∈ {3,4}`. Canonical-profile draws use three; broad draws may use four.

**Rationale.** Three preserves direct canonical support, while four breaks the assumption that only the public three-key dictionary exists. Both fit constructively within widths 15–20 with panel widths of at least three.

**Alternatives rejected.** Always three (leaves a panel-count shortcut) and five or more (would squeeze motifs or require a larger minimum width).

**Probe.** Exhaustive override matrix, profile-floor check, task tests, and sampler axis coverage.

**Failure mode / limit.** The dictionary never has fewer than three or more than four panels; the generator does not claim those variants.

## D4 — Randomize connected equal-size motifs of size three to five

**Choice.** Generate D4 variants from a small bank of connected bases; every lesson's panels share one exact `motif_size ∈ {3,4,5}` and each bounding box is at most 3×3.

**Rationale.** Geometry must vary to defeat memorized canonical shapes, but equal size keeps the intended correspondence visually clean. The 3×3 bound makes four or five nonoverlapping body placements constructive on the smallest canvas.

**Alternatives rejected.** Fixed canonical shapes; arbitrary random walks (risk duplicates, weak shapes, or retry drift); unequal per-panel sizes (adds an unnecessary dimension to the rule).

**Probe.** Exact motif-size overrides in every band, connectedness/size validation, deterministic-repeat tests, and the retained fixed-dictionary counterexample.

**Failure mode / limit.** Shape support is deliberately finite and compact; it does not cover disconnected or larger prototypes.

## D5 — Make the unique minimum color the key and anchor

**Choice.** Give each panel one distinct key; the key cell is the unique minimum color in that panel and all offsets are relative to it. Three-panel dictionaries use two keys sampled from 1–3 plus key 4; four-panel dictionaries use 1–4, with order shuffled.

**Rationale.** This preserves the canonical inference while forcing solvers to read each visible dictionary rather than associate key identities with fixed shapes.

**Alternatives rejected.** Fixed key-to-shape mapping, duplicate minima, or a separate legend. Fixed mapping is the strongest canonical shortcut; duplicate minima make anchor offsets ambiguous.

**Probe.** Canonical acceptance, strict parser, validator mutation tests, and the fixed-canonical-dictionary rival declared in all semantic interfaces.

**Failure mode / limit.** Minimum color is an explicit domain convention. Inputs with duplicate minimum cells are rejected rather than assigned an arbitrary anchor.

## D6 — Realize eight or nine distinct colors exactly

**Choice.** Advertise `color_count ∈ {8,9}` and ensure every selected decoration color appears at least once. Color 0 is background, color 9 is structural, keys and decoration colors are disjoint.

**Rationale.** The baseline advertised controls that were not reliably realized. Exact palette realization makes the axis observable and keeps canonical eight-color support while adding a broader nine-color case.

**Alternatives rejected.** Treating palette size as a request that may be missed, or allowing arbitrary sparse palettes. Both undermine exact override semantics.

**Probe.** `observe_overrides`, all single and joint override cases, and explicit task tests across bands.

**Failure mode / limit.** The support is only 8–9 realized colors; this is intentional and declared.

## D7 — Use grid heights 10–14 and widths 15–20

**Choice.** Expose `grid_h` and `grid_w` as exact axes. Every fourth sample index uses one of three canonical profiles `(11,15,8)`, `(12,15,8)`, or `(12,16,8)`; other draws cover the broader domain with difficulty biases.

**Rationale.** The minimum dimensions constructively fit a four-row dictionary, divider, five-row body, and five disjoint 3×3 slots. Canonical profiles satisfy the profile floor without collapsing broad variation.

**Alternatives rejected.** Baseline body-height/body-width pseudo-axes and rejection-heavy free sampling. The former were not faithful observables; the latter would make joint overrides unreliable.

**Probe.** 16,380-draw override report, per-band profile floor, 600-draw schedule audit, and 300-draw standalone coverage.

**Failure mode / limit.** Difficulty is a sampling bias, not a separate semantic grammar; exact overrides take precedence.

## D8 — Require four or five markers and every key at least once

**Choice.** Expose exact `marker_count ∈ {4,5}`. Seed the marker list with every key, then add repeated keys as needed and shuffle.

**Rationale.** Every dictionary entry should be demonstrated in each input; repeated keys show that the operation applies per marker rather than once per key. Four/five also permits all three- and four-panel combinations.

**Alternatives rejected.** One-to-three markers, missing keys, no-marker negatives, and marker colors lacking prototypes. Those baseline textures created underdetermined or invalid ordinary samples.

**Probe.** Strict self-check, exact override matrix, mutation tests, semantic gate, and lesson census.

**Failure mode / limit.** The validator accepts three to six markers so the public canonical examples remain valid, while the production sampler emits only four or five. This broader validator boundary is deliberate and tested separately from the exact production observer.

## D9 — Place markers in disjoint 3×3 slots

**Choice.** Construct five available slots in a horizontal 3×3 strip and use a shuffled subset; place each anchor so its entire motif fits inside its slot.

**Rationale.** It eliminates clipping and overlap by construction, keeps labels deterministic and easy to audit, and supports every legal joint override without retries.

**Alternatives rejected.** Random marker positions with rejection, overlapping stamps, clipped stamps, or overwrite-order semantics. Those introduce avoidable ambiguity about the intended output.

**Probe.** Exhaustive joint overrides, strict checks, independent oracle, and Racket parity.

**Failure mode / limit.** Stamp interactions are outside the generated domain. The task teaches dictionary lookup and anchored copying, not collision resolution.

## D10 — Declare the strongest canonical-fitting rival executable

**Choice.** Add one named rival, `fixed_canonical_dictionary`, to `SEMANTIC_RIVALS`, `CANONICAL_SHORTCUTS`, and `LESSON_COMPETITORS`, with a paired `fixed_dictionary_counterexample` witness.

**Rationale.** All public canonical examples repeat the same three prototypes, so memorizing them is more plausible and stronger than generic identity/flip shortcuts. Generated lessons must explicitly refute it.

**Alternatives rejected.** Relying only on visual diversity, or declaring many weak synthetic rivals while omitting the strongest canonical-perfect one.

**Probe.** Rival fits 3/3 canonical pairs; witness fired 600/600 in the semantic gate, 300/300 in the standalone sampler, and the rival was refuted in 300/300 production lessons plus 900/900 query rotations.

**Failure mode / limit.** This is a finite rival family. Other programs may still fit a finite lesson, so the reports avoid a universal-identifiability claim.

## D11 — Use two demonstrations and permit every pair as query

**Choice.** Set `EXAMPLES_NEEDED = 2`; production assembly uses two demonstrations and one query. The final census required all three rotations to distinguish the declared rival.

**Rationale.** Every lawful generated input already contains a complete visible dictionary and multiple requests, so one input is semantically rich; two demonstrations add independent prototype/key assignments and make the curriculum robust without unnecessary length.

**Alternatives rejected.** One demonstration (too brittle for training) and fixed query position without diagnostic rotations (could conceal an ordering-specific shortcut).

**Probe.** 100 lessons per band with `--rotate-query`: 300 lessons, 900 unique grids, and 900 held-out rotations with zero declared-rival ambiguity.

**Failure mode / limit.** Rotations reuse each materialized three-pair bundle and do not enumerate every seed or all cyclic starts beyond the sampled schedule.

## D12 — Fail closed on malformed calls and grids

**Choice.** Reject unknown overrides, non-integer axis values, out-of-range requests, malformed/ragged grids, stray color 9, empty panels, disconnected motifs, duplicate keys, unsupported markers, missing key use, and invalid palette counts.

**Rationale.** The baseline accepted an unknown override and mixed negative textures into ordinary paths. A strict contract makes source-bound tests meaningful and prevents silent drift.

**Alternatives rejected.** Ignoring unknown keys, coercing values, or returning degenerate grids as ordinary samples.

**Probe.** Invalid-override tests, mutation tests, malformed-grid tests, lint/defect-lint, and the full override stage.

**Failure mode / limit.** The API is intentionally strict; callers depending on ignored keys must fix their request rather than receive an approximate sample.

## 2026-10-25 — native parametric stamped-cluster family

- **Canonical authority preserved:** `generator.py` remains byte-identical at SHA-256 `30ec6f1ea881bb0ed60500f02ba73904ba22d24641c3930d14ee6ba2b567d3e2`; `finish=stamp_only` returns the exact canonical Racket bytes at SHA-256 `46157a601fce9d70e7669dc2c4ab64f6364540d8009bc32a99cb0bad6456c781`.
- **Chosen composition:** after complete keyed-dictionary stamping, collapse the produced output to binary occupancy, derive 4-connected stamped clusters, select the unique largest by occupied-cell count, and recolor that whole cluster to 9. The alternate program hash is `e2704863cac341238df81d479cd9572f816317a67b55662548076b95d355e93f`.
- **Teaching repair:** an initial sampler allowed `first_binary` to survive some two-demonstration prefixes. The retained regression now requires a smaller earlier cluster and a later unique winner, so all audit seeds reject that proxy with only two demonstrations.
- **Evidence:** 54 task tests; 18 authoring jobs; 61 protected-Racket audit evaluations; four declared rivals with zero survivors; 18 exact 30×30 checks; four native qualification jobs and 40 protected-Racket qualification evaluations; 16 public sequential views and 24 first-turn private-field invariance checks.
- **Causal witness:** post-stamp binary component sizes are `[16, 3, 21]`; replacing binary connectivity with same-color connectivity changes 22 final cells. Replay status is `reviewer_replayed`.
- **Limit:** the rival audit is finite and does not prove universal uniqueness. This reviewer reports the exact source ready for owner replay; it does not grant owner acceptance or training admission.
- **Next useful action:** owner native replay and exact-source acceptance using `checks/b83ad00fc681/qualification/qualification.json` and `checks/b83ad00fc681/causal/witness.json`.
