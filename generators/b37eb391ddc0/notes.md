# Working notes: b37eb391ddc0

## Review review-f6d5c5cd8273706c

Baseline SHA-256: `071f5905acf762484232dea14d28992ad83828e5edbb1e8b7ee26f37d0dc1643`.
Final SHA-256: `c113fd93cc524873595b4bf9808b87727c97548f68c0a7427424c782e393b47f`.
Canonical rule hash: `24318a9ceacd`; no authority source changed.

The baseline generated isolated same-colour diagonal pairs only when both companion corners were empty. Five plausible rules therefore fit every canonical demonstration: isolated-only completion, preserving occupied companions, first pair per colour, exactly two occurrences, and any nonzero diagonal. The exact authority witness `[[2,3],[0,2]] -> [[2,2],[2,2]]` disproves the first two.

Version 2.0.0 replaces stale independent axes with one exact linked `scene_profile` axis covering all three canonical `(height,width,palette-size)` profiles. Every generated scene has occupied-companion, repeated-pair, unequal-colour, and both-orientation witnesses. Broad `self_check` owns the lawful authority domain; stricter `teaching_check` owns the generated curriculum.

A first rich motif passed semantic tests but formed one foreground component. The distribution gate caught the canonical morphology mismatch. Safe distant singletons now produce four foreground objects for p3 profiles and six for p4 without creating accidental diagonals.

Final evidence: after battery 12/12 green; task tests 13/13; reference probe 300/300 deterministic unique samples with all five rival disagreements, 162/162 local rotations, and 28/28 Racket parity; lesson census 300 production lessons and 900 required query rotations with zero ambiguity or hook/scoring errors.

Known limit: all generated semantic interactions use one transformed 2×4 motif family and do not teach conflicts between two active writing colours. Finite rival checks do not prove unique induction against every possible rule.
## Current reviewer considerations

Source SHA-256: `c113fd93cc524873595b4bf9808b87727c97548f68c0a7427424c782e393b47f`.

# Design and verification decisions for b37eb391ddc0

## D1 — Repair the teaching distribution, not the authority

The selected Racket authority already matches every canonical label and, on `[[2,3],[0,2]]`, correctly returns a solid colour-2 block. The defect was distributional: baseline inputs only used isolated same-colour diagonal pairs with zero companions. I therefore left the authority unchanged, pinned `RULE_HASH = "24318a9ceacd"`, and changed only the selected generator, tests, notes, summary, and workspace probe.

Alternative rejected: changing the rule to preserve occupied companions. That would make the old generator self-consistent but contradict the supported Racket output and the authority’s original-input matching semantics.

## D2 / R2 — Collapse stale controls to one exact linked profile axis

The baseline advertised independent dimensions and pair-count controls that were either ignored or could not be varied independently without changing the actual task grammar. The repair exposes one exact `scene_profile` axis:

- `rich_7x8_p3`
- `rich_8x8_p3`
- `rich_8x9_p4`

Each profile links height, width, and palette size to one canonical signature. Every band deterministically cycles through all three profiles, and `observe_overrides` proves which profile was materialized. Unknown axes, invalid profile names/types, and unsupported difficulties raise immediately.

Alternative rejected: retain separate `grid_h`, `grid_w`, `palette_size`, and `n_pairs` axes. Their Cartesian product would advertise combinations the carefully packed diagnostic motif cannot lawfully guarantee, recreating silent clamping or dead controls. A linked exact profile is smaller but honest.

## D3 / R1 — Put all essential semantic witnesses in every sample

The core local motif uses one target colour at `(0,0)`, `(0,2)`, `(1,1)` and a companion colour at `(1,0)`, `(1,3)`, modulo horizontal/vertical reflection and translation. It guarantees:

1. two same-colour adjacent diagonal pairs for one colour;
2. both diagonal orientations;
3. an occupied wrong-colour companion that the target colour must overwrite;
4. an unequal-colour diagonal control that must not trigger.

This single motif simultaneously refutes five rules that fit all canonical demonstrations: `isolated_pairs_only`, `preserve_occupied`, `first_pair_per_color`, `exactly_two_occurrences`, and `any_nonzero_diagonal`.

Alternative rejected: make hard negatives probabilistic. A rare witness can disappear from a two-demonstration lesson; making every sample diagnostic ensures every two-demo window and every one-query holdout rotation contains direct refutation evidence.

## D4 / R3 — Preserve canonical morphology with safe singletons

The first rich-motif implementation formed one connected foreground object, whereas the canonical profiles have four or six foreground components. The independent distribution gate caught this after semantic tests were already green. I added one safe singleton for p3 profiles and three total singleton contributions for p4 (one palette-required colour plus two morphology singletons), all more than one Chebyshev step from existing cells.

This restores object counts to 4 for p3 and 6 for p4 without creating accidental adjacent diagonals. The failed gate is retained under `checks/dist_gate-attempt1/`; final evidence is in the after battery and `checks/reference-probe.json`.

Alternative rejected: split the target motif itself. That would weaken the repeated-pair and occupied-companion witnesses. Isolated safe singletons alter morphology without changing the semantic core.

## D5 — Separate lawful-domain validation from curriculum validation

`self_check` accepts any rectangular ARC grid with a productive same-colour adjacent diagonal and rejects malformed or no-op inputs. This broad validator owns canonical examples and authority-level counterexamples, including occupied companions. `teaching_check` calls the broad validator and then requires all four curriculum witnesses plus a known canonical-scale profile.

Alternative rejected: place all rich-distribution requirements in `self_check`. That would incorrectly reject lawful canonical or adversarial authority inputs merely because they are not generated teaching scenes.

## D6 — Mirror the authority and declare rivals executable

`rule_mirror` reads all source positions from the original grid, iterates colours in first nonzero row-major appearance order, and accumulates completed 2×2 writes. It is checked against all three canonical labels, 18 generated task-test inputs, the occupied-companion counterexample, and 28 retained real-Racket probe cases.

The five rivals are executable functions and are reused through `SEMANTIC_RIVALS`, `CANONICAL_SHORTCUTS`, and `LESSON_COMPETITORS`; the probe iterates declarations rather than copying names. All five fit all three usable canonical pairs and disagree on every one of 300 final-source probe samples.

## D7 — Use two demonstrations and support arbitrary query rotation

`EXAMPLES_NEEDED = 2`. The production sampler makes consecutive three-pair lessons from the deterministic profile schedule. Because each individual pair already refutes every declared competitor, any two demonstrations still refute them when any of the three pairs is held out as the query.

Verification was intentionally redundant:

- task test exhaustively checks local consecutive windows and all query indices over multiple seeds, starts, and bands;
- `reference_probe.py` checks 162 cyclic local rotations;
- required semantic gate checks 12 source-bound lessons with required rotations;
- production census checks 300 lessons and all 900 single-query rotations.

This supports arbitrary single-query rotation for the actual two-demo/one-query assembly. It does not prove identifiability against undeclared rivals or arbitrary lesson lengths.

## D8 — Build a reusable source-bound future-agent probe

`workspace/reference_probe.py` records source hashes, canonical shortcut fit, profiles, witnesses, rivals, determinism, uniqueness, object counts, lesson rotations, the exact authority counterexample, and optional real-Racket parity. `--racket` fails rather than silently falling back to the Python mirror. The retained invocation used `--count 100 --racket` and produced `checks/reference-probe.json`.

## D9 — Preserve failed iterations and source identity

I kept the test-first red run, initial lint failure, the morphology gate failure, and the interrupted full-battery checkpoint. The final full battery was resumed only after source/checkpoint identity matched; all claimed final checks bind to generator SHA `c113fd93cc524873595b4bf9808b87727c97548f68c0a7427424c782e393b47f`.

The post-repair solve was prepared after the generator stopped changing. Its `solve/summary.json` records the same generator hash. The blind solve is separately bound to its drawn task and was completed before any selected-task exposure.

## D10 — Known limits

- The generated target geometry is one 2×4 motif family under translation and reflection. This is deliberate compactness, but it is a visible regularity.
- The declared rival set is finite. Passing those rivals is not universal uniqueness evidence.
- Generated scenes do not contain two active target colours whose completed boxes conflict. The authority’s first-appearance write order is mirrored and parity-tested, but canonical demonstrations do not establish that teaching requirement.
- Profiles remain at canonical dimensions and palette sizes rather than expanding to all ARC sizes; the goal was faithful semantic coverage, not unconstrained scale diversity.
- Audit findings A1 and A2 are report-only; their generators were not modified under this assignment.

## Native parametric handoff — review-21a098f47523bb13 (2026-10-25)

A task-local native family now lives in `workspace/parametric/` without changing
production `generator.py` or the selected canonical authority.  The default
`completion_scope=all_pairs` returns the canonical Racket program byte for byte.
The alternate `completion_scope=cue_selected_color` locates the unique color-1
cue, enumerates active same-color adjacent diagonal pairs, selects the uniquely
cue-nearest pair, carries its color as an input-derived intermediate, and then
completes every original-input pair of that color globally.  Inputs are matched
across settings, deterministic, prefix-stable for 2–6 demonstrations and 1–4
queries, and include four distinct queries with distributed 30×30 content.

The minimum two demonstrations reject the declared all-pairs, selected-pair-only,
position/rank, fixed-color, and farthest-pair rivals.  A 64-seed finite audit
covered 384 setting/count lessons with no surviving harmful declared rival; this
is finite evidence rather than a universal uniqueness proof.  Native
qualification passed at 2, 3, and 6 demos for both settings and seeds 0/17,
totaling 136 protected-Racket evaluations.  Sixteen one-query public projections
passed saved-byte and leakage checks.  The source-bound protected counterfactual
substitutes the farthest pair's color for the cue-nearest pair's color and changes
10 output cells.

Retained evidence is under `checks/b37eb391ddc0/`; the current source inventory
is `workspace/parametric/evidence/manifest.json`.  The result is reviewer-ready
only.  Exact-byte owner integration, fresh native acceptance, and any training
admission remain separate decisions.

Owner reconciliation: Three exact disjoint rules share the accepted cue geometry. Added isolated color occurrences establish a unique rarest active color while preserving every original diagonal pair, unique cue-nearest pair, and selected-color global completion. The first two demos have different rarest colors. Supports 2–6 demos, four default queries and a 30×30 query. The original sampler remains available in native_family.py. The exact prior programs and incoming alternate are preserved. Fresh source-bound acceptance and causal evidence: `evidence/owner-variant-reconciliation/current.json`.
