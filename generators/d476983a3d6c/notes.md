# Working notes: d476983a3d6c

Record design decisions, hypotheses, review findings, and unresolved questions here.
Imported associated notes retain original evidence/timestamps in `evidence/associated_notes.jsonl`.
## Current reviewer considerations

Source SHA-256: `80d94a6e64895839b4da9c63524f47d7ea1568fa2714a8f846933ccd166fb497`.

# Decisions for `d476983a3d6c`

## D1 — Keep the Racket authority unchanged

**Input choice.** Repair the generator and its teaching contract only. Keep the selected canonical Racket rule unchanged.

**Original rationale.** The original generator’s exact rationale is not recorded. The retained canonical program is executable, matches all canonical pairs, and already defines the subtle behaviors that were missing from the sampler: singleton preservation and row-major sequential overwrite.

**Alternatives considered.** Rewrite the rule to match the old summary’s narrower “non-aligned marker pairs only” domain; alter processing order; or make singleton cells disappear. All were rejected because they would change verified canonical behavior rather than repair coverage.

**Probe.** `rule_mirror` was checked against all three canonical pairs. `racket_lint` and `authority_sync` remained green, and the authority-set hash stayed unchanged.

**Failure mode / limitation.** The archival raw rule source remains divergent from the selected synchronized source, as it already was before this repair. Execution parity passed; no archival source was edited.

## D2 — Use four explicit semantic scene profiles

**Input choice.** Replace loose pair-count/command/palette controls with:

1. `cmd1_three_pairs`
2. `cmd2_two_pairs`
3. `cmd1_two_pairs_singleton`
4. `cmd2_three_pairs_singleton`

These profiles specify the exact command, paired-color count, and singleton count. Construction additionally requires visible aligned handling and/or overlap witnesses according to the scheduled profile.

**Original rationale.** Unknown. The prior sampler chose command and non-aligned pairs independently and excluded singleton colors from ordinary draws.

**Alternatives considered.** Keep fully independent axes; create a large Cartesian product; or add “degenerate textures.” Independent axes made lesson-level coverage accidental, a large product was unnecessary, and invalid/degenerate textures previously polluted the public domain.

**Probe.** Across 100 draws per difficulty band, each scene profile appeared exactly 25 times. Every band contained 50 aligned scenes, 50 singleton scenes, and 75 path-overlap scenes. Every four-demo generated lesson and every held-out-query rotation passed the declared semantic contract.

**Failure mode / limitation.** Profiles intentionally couple several semantic features. This favors reliable teaching over independent factorial experimentation. Consumers needing independent factor sweeps should add diagnostic-only tooling rather than weakening the lesson schedule.

## D3 — Use a four-slot schedule with duplicated decisive evidence

**Input choice.** Schedule scene profiles by `sample_index % 4`; build lessons from four consecutive demonstrations plus the next query. Each decisive rule feature appears in at least two of the five labelled pairs.

**Original rationale.** Unknown. The baseline had no lesson contract or stated assembly policy.

**Alternatives considered.** Random profile selection; one witness per five-pair lesson; or a longer curriculum. Random selection gives no per-lesson guarantee. A single witness can disappear when it becomes the query. A longer lesson was unnecessary because four demonstrations already satisfy the packet’s declared minimum.

**Probe.** The official census held out each of the five labelled pairs once. Across 300 lessons and 1,500 rotations there were zero ambiguous rotations, hook warnings, or scoring errors against the declared rivals.

**Failure mode / limitation.** This is evidence against the declared rival family only. It does not prove identifiability against every possible program or every model-specific shortcut.

## D4 — Separate size variation into observable grid profiles

**Input choice.** Use disjoint `small`, `canonical`, and `large` dimension sets. Schedule grid profiles as `canonical, canonical, small, large` so canonical-shaped examples remain common while broader sizes are exercised.

**Original rationale.** The baseline exposed independent `grid_h` and `grid_w` ranges, but several other axes were not observable and the documented summary still said “Fixed 10×10.”

**Alternatives considered.** Keep exact height and width axes; use one unrestricted size range; or only emit canonical dimensions. Exact dimensions add many low-value combinations, one range makes profile provenance weaker, and canonical-only sampling would under-test dynamic coordinate logic.

**Probe.** Per 100 draws in each band: 50 canonical, 25 small, and 25 large grids, all distinct. `observe_overrides` exactly recovers the requested profile.

**Failure mode / limitation.** Exact dimensions are no longer direct public overrides. This is deliberate: size profile is the semantic control, while dimensions remain deterministic internal variation.

## D5 — Preserve canonical color semantics and first-appearance order

**Input choice.** Treat only `(0,0)` as the command cell; discover nonzero colors in row-major first-appearance order; connect colors appearing exactly twice; leave singleton colors unchanged; let later pair paths overwrite earlier paths.

**Original rationale.** These behaviors are encoded by the selected canonical Racket program but were not fully represented in the previous generator summary/distribution.

**Alternatives considered.** Sort colors numerically; process pairs in construction order; forbid overlap; or clear singleton cells. Each alternative disagrees with a canonical pair or creates an unsupported semantic restriction.

**Probe.** The Python mirror matches all canonical outputs. Generated overlap scenes are accepted only when reverse-priority output differs visibly. The `reverse_pair_priority` and `drop_singletons` rivals are refuted by the generated curriculum.

**Failure mode / limitation.** Color first appearance is deliberately correlated with marker placement because it is the authority’s processing order. The profile probe includes exact counterexamples but does not exhaust all marker geometries.

## D6 — Avoid foreign-marker path interiors

**Input choice.** Reject constructed scenes when a path interior crosses another color’s original marker. Path-to-path overlap is allowed and encouraged.

**Original rationale.** Unknown. This restriction was introduced to keep the intended overwrite signal interpretable: overlap should arise between painted paths, not by erasing an input marker before its own color is processed.

**Alternatives considered.** Allow every collision; forbid all collisions; or repair collisions after placement. Allowing marker erasure creates unnecessary perceptual ambiguity. Forbidding all collisions removes overwrite evidence. Post-hoc repair risks silently changing the sampled profile.

**Probe.** `self_check` validates the marker/path condition, while generated overlap scenes still visibly refute reverse processing priority.

**Failure mode / limitation.** The canonical rule is total on some grids outside this curated grammar. The generator intentionally samples a teachable subset, not every lawful input accepted by the Racket program.

## D7 — Make overrides exact and reject unknown controls

**Input choice.** Public overrides are limited to `scene_profile` and `grid_profile`; unsupported difficulty values and unknown keys raise immediately. `observe_overrides` reports both realized values.

**Original rationale.** Unknown. The prior generator accepted unknown keys and advertised dead or unprobeable controls.

**Alternatives considered.** Retain compatibility aliases; silently ignore legacy keys; or mark them diagnostic. These options preserve misleading API surface and weaken source-bound override testing.

**Probe.** The strict override gate sampled 1,800 combinations without a finding. Focused tests exercise every valid profile and invalid-key/value rejection.

**Failure mode / limitation.** This is intentionally a breaking cleanup of unsupported override names. No cataloged caller contract for those names was found in the packet.

## D8 — Pin a task-local semantic contract

**Input choice.** Declare nine executable rivals covering fixed command orientation, partial pair iteration, aligned-pair omission, singleton deletion, reversed priority, no-op output, and command clearing. Add witnesses and `lesson_identifiable`.

**Original rationale.** The baseline had no semantic declarations.

**Alternatives considered.** Depend only on aggregate diversity or informal notes; declare an extremely large speculative rival set; or omit canonical-shortcut checks. Aggregate diversity cannot prove teaching value, an unbounded rival catalog would be brittle, and canonical ambiguity is specifically relevant here.

**Probe.** Semantic gate: 600/600 strict draws, 9/9 witnesses, 9/9 rival claims, 12/12 production lessons identifiable, and 0/60 ambiguous smoke-test rotations. Larger census: 300/300 lessons and 0/1,500 ambiguous rotations.

**Failure mode / limitation.** The contract is finite and task-local. New plausible rivals should be added only with executable behavior and a generated witness.

## D9 — Add a reusable profile probe

**Input choice.** Build `workspace/profile_probe.py` to inspect declared axes/rivals directly, perform a balanced distribution census, check canonical-fit shortcuts, retain generated counterexamples, and exhaust requested held-out-query windows.

**Original rationale.** No equivalent task-local tool existed.

**Alternatives considered.** Keep one-off notebook snippets or copy rival names into the probe. One-off snippets are hard to replay; copied names drift from production declarations.

**Probe.** The retained run used 100 draws per band and 32 lesson starts, yielding 300 distinct scenes and 480 passing held-out rotations.

**Failure mode / limitation.** Its intended outputs use the Python mirror. Official rule authority is separately checked by the Racket semantic battery, census, and exact shortcut witness.

## D10 — Test portability and handoff as part of completion

**Input choice.** Use `reviewer_support.find_root`, `canonical_path`, and `canonical_pairs`; generate an exact Git patch; apply it to a fresh extraction in an isolated Git root; rerun focused tests there.

**Original rationale.** The new test suite had to survive the packet’s copied portable runtime rather than rely on the authoring tree shape.

**Alternatives considered.** Direct relative-parent guesses or testing only in the working tree. Both can pass locally and fail during intake.

**Probe.** `git apply --check` and `git apply` exited 0. The fresh generator hash matched exactly and 9/9 tests passed.

**Failure mode / limitation.** The fresh extraction’s random assignment draw is unrelated to this frozen assignment; the handoff check validates the repository delta and selected task tests, not re-drawing the assignment.

## Current native family — proposed, owner acceptance pending

`workspace/parametric/` adds exact-canonical `routing_mode=command` and
`avoid_painted`, which compares both L paths against the current accumulated
canvas before painting each next pair. Original marker positions and first
appearance order remain authoritative; ties read the original corner command.
The input-dependent intermediate is the canvas after preceding routes. Reading
the original canvas instead changes later decisions in the retained causal case.

The native sampler supports 2–6 demonstrations and 1–4 distinct queries with
matched inputs across settings, independent count prefixes, and full-span
30×30 query geometry. The first two examples are a bounded demonstration-only
cover of the independent executable rival bank; no queries guide selection.
Current commands in the task-local README reproduce checks and qualification.

Initial multiplicity profiles still encoded the command through a more detailed
count rule. The repaired sampler independently draws command and template axis,
and the teaching bank explicitly refutes that exact-profile shortcut as well
as the inherited parity shortcut. A separate seed-72 regression showed that
later boundary-marker placement could collide with earlier markers; boundary
endpoints are now reserved first. Before/after evidence is retained in
`checks/d476983a3d6c/` in the reviewer return.

The production generator SHA remains
`80d94a6e64895839b4da9c63524f47d7ea1568fa2714a8f846933ccd166fb497`.
Its source-bound unresolved audit is not cleared by this separate native
curriculum. Next action is owner qualification and acceptance of the exact
integrated native sources; no training admission is implied. Coverage remains
finite and the 512-candidate teaching cap can refuse an untested seed explicitly.
The independent minimum-demo review added seven confirmed predicates covering
command restoration, ignored nonpairs, first-pair routing, positive-cost ties
and capped collision counts. They are now required demonstration refutations.
The previous 256-candidate limit failed seed 8; raising it to 512 reaches the
observed cover at candidates 68 and 335 without increasing demonstration count
or changing previously successful prefixes. Earlier finite passing audits are
retained with their narrower bank/seed/source scope rather than treated as
evidence for the final source.
