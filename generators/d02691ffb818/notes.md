# Working notes: d02691ffb818

Record design decisions, hypotheses, review findings, and unresolved questions here.
Imported associated notes retain original evidence/timestamps in `evidence/associated_notes.jsonl`.
## Current reviewer considerations

Source SHA-256: `7f2ef14910b4a3563467940e6c85c2c9c38c97e881e56dc7f139363f241e6d70`.

# Decisions for d02691ffb818

## D1 — Preserve the total Racket rule and pin its authority

**Original rationale:** The baseline summary already described clipped diagonal X stamps, and baseline rule smoke passed. The missing `RULE_HASH` made that relationship unenforced.

**Decision:** Leave all Racket/canonical sources unchanged and set `RULE_HASH = "3eec1d7807b1"` in the generator.

**Alternatives rejected:**

- Change the Racket rule to reject border or nearby markers. This would encode the baseline generator's restriction rather than the canonical transformation.
- Replace the selected rule with the divergent archival raw-code text. Both execute all five canonical pairs, but the selected canonical/target sources are already exact matches.

**Probes:** baseline/final rule smoke, authority sync, independent Python oracle over all five canonical pairs.

**Failure modes and limitations:** Canonical examples do not determine every off-distribution behavior, so the pin binds source identity while executable witnesses test the selected teaching domain. The archival divergence remains documented rather than silently normalized.

## D2 — Replace imported/dead axes with three exact observable controls

**Original rationale:** The imported generator advertised generic palette, texture, density, position, and color-count axes. Several were singleton, aliases, diagnostic degenerates, or ignored; the baseline override gate produced 9,066 findings and accepted unknown keys.

**Decision:** Advertise only `grid_h`, `grid_w`, and `markers`; validate types/ranges before generation; route all three through keyed `GenCtx` draws; expose `observe_overrides`; reject unknown keys.

**Alternatives rejected:**

- Keep dead axes as metadata-only controls. That preserves a misleading API and makes typo acceptance look successful.
- Declare thousands of incompatibilities. The combinations were not semantically incompatible; the implementation simply failed to honor its public domains.
- Retain degenerate `texture` values as public axes. They were better represented by explicit semantic witnesses and validator mutation checks.

**Probes:** final 64,800-draw override contract, exact 5×5 with 2 and 14 markers in every band, unknown-key rejection, source-bound tests.

**Failure modes and limitations:** Exact dimensions are limited to 5–20 and marker count to 2–14. Values outside those selected training bounds are rejected even though the total rule could execute some of them.

## D3 — Use a three-slot canonical/edge/clustered curriculum

**Original rationale:** Baseline interior separation made output visually clean but removed two lawful behaviors. Every canonical pair is compatible with both “ignore border markers” and “drop clustered markers.”

**Decision:** Cycle `sample_index % 3` through:

1. canonical shape, 2–4 separated interior markers;
2. edge layout with an output-relevant clipped border stamp; and
3. clustered layout with a nearby marker pair.

Three consecutive demonstrations therefore contain canonical support and intended counterexamples to both canonical-fitting shortcuts.

**Alternatives rejected:**

- Pure random profile choice. A three-example lesson could easily miss one rare branch.
- Put clipping and overlap into every example. That would move too far from the observed canonical distribution and weaken canonical-profile support.
- Keep only canonical-looking inputs. This maximizes superficial similarity but leaves the strongest rivals unrefuted.

**Probes:** profile floor, semantic gate schedule counts, all cyclic starts in 300- and 3,000-lesson censuses, diversity gate.

**Failure modes and limitations:** The cadence is deterministic. A consumer with hidden sample-index metadata could learn the schedule, although normal puzzle inputs expose only the grid; within each slot, dimensions, counts, and positions remain seed-driven.

## D4 — Separate lawful-domain validation from canonical resemblance

**Original rationale:** Baseline `self_check` mixed rule validity, difficulty defaults, and aesthetic separation. It rejected four canonical inputs and lawful clipping/overlap.

**Decision:** `self_check` validates rectangular binary input, selected shape/count bounds, and the teaching-domain exclusions. `strict_canonical_like` separately reports canonical shape, count, border, and spacing properties.

**Alternatives rejected:**

- Continue difficulty-specific count validation. Difficulty is a default sampler policy, not an input-law constraint.
- Treat border/overlap as invalid. Both are explicitly defined by the pinned rule.
- Accept every total-rule input as training data. Mutation gates showed that a singleton, solid 2×2, and four-cell straight line are low-information teaching scenes.

**Probes:** all canonical inputs, explicit border and overlap cases, destructive mutation gate, task-local impostor regressions.

**Failure modes and limitations:** The three excluded layouts are curriculum choices, not mathematical invalidity. They should be revisited if a future lesson policy deliberately needs minimal examples.

## D5 — Declare executable rivals, witnesses, and lesson identifiability

**Original rationale:** The baseline had comments about simple rivals but no executable contract. The semantic gate therefore returned `NO_CONTRACT` and could not test whole lessons.

**Decision:** Declare five rivals, three witness predicates, witness-to-rival mappings, the two canonical-fitting shortcuts, and `lesson_identifiable`, which rejects any demonstration set that leaves a declared competitor alive.

**Alternatives rejected:**

- Rely only on prose. Prose does not bind names to executable disagreement checks.
- Count witness frequency only. Individual witness presence does not prove that a complete lesson refutes every rival.
- Use the generator's own mirror as the only oracle. The review probe instead uses an independent Python geometry implementation, while Racket remains label authority.

**Probes:** canonical shortcut fit 5/5, semantic rival claims 60/60, 300-lesson required census, 3,000-lesson extended census.

**Failure modes and limitations:** The declared rival family is finite. The contract measures identifiability against plausible known alternatives, not all computable rules.

## D6 — Define clipping witnesses by output disagreement, not structure

**Original rationale:** The first witness returned true for any border marker. The full 600-draw census found a grid where border stamps were completely covered; `ignore_border_markers` produced the same output, so the claimed witness held only 59/60 times.

**Decision:** A clipping witness fires only when the correct output differs from the output after dropping every border marker.

**Alternatives rejected:**

- Border presence alone. The retained counterexample disproves it.
- Require a corner marker. A non-corner boundary marker can also provide a valid clipped witness.
- Require every border stamp cell to be unique. That is stronger than necessary; one output-relevant cell suffices.

**Probes:** failing exact grid regression, final semantic gate 60/60, independent render comparison.

**Failure modes and limitations:** The predicate evaluates a specific rival. It does not by itself guarantee that every scheduled edge draw fires, which motivated D7.

## D7 — Constructively guarantee an output-relevant edge example

**Original rationale:** After D6, the extended old-source census found one unidentifiable lesson in 3,000: easy lesson 274, start 3014. Its edge demo had markers `(0,0)` and `(1,1)`; the interior marker covered the border marker's entire clipped stamp.

**Decision:** Pick a border anchor and exclude every diagonally adjacent marker position that could paint the anchor center. If a low-information layout is repaired, require the repaired edge points to preserve an output-relevant border contribution.

**Alternatives rejected:**

- Retry randomly until the witness fires. Constructive reservation is deterministic and cannot exhaust by chance.
- Leave the rare failure because 300 lessons passed. One surviving shortcut is exactly the kind of mislabeled teaching ambiguity the review is meant to remove.
- Add a validator rejection only. That would detect the bad draw but not make generation reliable.

**Probes:** exact seed/sample regression (red then green), old-source 3,000-lesson reproducer, final-source 3,000-lesson census with 0 survivors.

**Failure modes and limitations:** The guarantee is specific to `ignore_border_markers`, the declared strongest border shortcut. Other, more elaborate boundary rivals remain possible.

## D8 — Build a source-bound reusable lesson probe

**Original rationale:** The required battery lesson sample is a smoke check. A deterministic schedule also requires testing all possible lesson-start residues, not just pooled witness counts.

**Decision:** Add `workspace/review_probe.py`. It loads the exact generator bytes, iterates actual `CANONICAL_SHORTCUTS` and `LESSON_COMPETITORS`, uses an independent oracle, records unique inputs/domain bounds, and tests every cyclic start.

**Alternatives rejected:**

- Copy rival names into an external one-off script. That can silently drift from source declarations.
- Use overlapping rolling windows. The recorded policy uses independent seeds and non-overlapping lesson starts for clearer denominators.
- Call Racket for all 12,000 extended draws. Python geometry is sufficient for cheap census work after canonical and sampled Racket parity checks.

**Probes:** unit test imports the tool; 100 lessons/band required run; 1,000 lessons/band extended run.

**Failure modes and limitations:** It is task-specific and depends on a simple independent oracle. `FEEDBACK_TO_CODEX.md` proposes lifting the complete-lesson pattern into the shared semantic gate.

## D9 — Keep version 2.3.0 for the complete undelivered repair

**Original rationale:** Version 2.3.0 was introduced in this review before any return was delivered. The later edge guarantee corrected the same review candidate rather than changing an already released 2.3.0 artifact.

**Decision:** Retain `VERSION = "2.3.0"` and bind all final evidence to the final source SHA.

**Alternative rejected:** Bump to 2.3.1 solely for an internal intermediate that was never returned. Source hashing, fresh replay, and solve provenance already prevent confusion with the superseded bytes.

**Failure modes and limitations:** Anyone caching an unpublished intermediate by version string alone could confuse it with the final candidate; the retained SHA-bound evidence avoids that ambiguity.

## D10 — Add a native cue-selected satellite-count radius family

**Original rationale:** The repaired production generator teaches only the canonical fixed-radius X stamp. This round required a nearby episode-fixed rule parameter with a real input-dependent A-to-B dependency, short distinguishing lessons, four private queries, and exact native qualification without weakening the canonical default.

**Decision:** Add a separate native parametric family under `workspace/parametric/` with `radius_rule={fixed_one,cue_satellite_count}`. `fixed_one` returns the exact canonical Racket bytes. In `cue_satellite_count`, Step A selects the blue marker nearest the unique red cue; the intermediate is that marker's number of green cardinal satellites; Step B uses that count as the diagonal radius for every orange X stamp. The input grammar is identical across settings, supports 2–6 demonstrations and 1–4 prefix-stable queries, and reserves the fourth query as a substantive 30x30 case.

**Teaching decision:** Construct the first two demonstrations with selected radii 2 and 3 while retaining one- and four-satellite distractor markers. Across the declared eleven-rule candidate set, only the chosen rule survives those demonstrations for every audited seed. This blocks fixed-radius, global-count, farthest-marker, row-major, cue-distance, selected-only, and per-marker shortcuts within the finite audit.

**Public-export correction:** A first saved-file check showed that hashing compact JSON without the required trailing newline produced the wrong public IDs. `public_bytes`/`public_id` are now regression-bound to `reviewer_support.public_challenge_bytes` and `public_challenge_id`; the two retained first-turn files pass the repository checker byte-for-byte.

**Evidence:** 12 focused parametric tests and 28 staged task tests pass. The source-bound self-audit covers 24 episodes, 148 labeled pairs, 12 matched-input requests, 12 30x30 episodes, and 84 protected-Racket evaluations. Native qualification covers two settings × seeds 0/17 with 40 protected-Racket evaluations. The protected wrong-intermediate replay substitutes the farthest marker's satellite count 1 for the cue-selected count 3 and changes 30 final cells. A separate fast stress covers 64 seeds, 640 visible inputs, 1,280 labels, 2,816 finite-rival evaluations, and 64 30x30 queries with no failures.

**Limits and next action:** The rival family and seed set are finite; no universal uniqueness or measured training gain is claimed. Reviewer status is ready only. The owner must integrate these exact bytes, rerun native qualification and fresh acceptance on the live source, and separately decide training admission.
