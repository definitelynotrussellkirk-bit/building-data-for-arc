# Working notes: be5d9fa6fec1

## Baseline diagnosis

No associated prior notes were present. Version `2.1.1` used retry-based row construction, a height cap, and post-hoc row edits. Retained evidence:

- missing canonical `RULE_HASH`;
- weak `self_check` (only `12/48` destructive mutations rejected; minimal impostors accepted);
- ordinary texture domain included negative fixtures;
- exact profile support `3/60`, with hard `0/20`;
- override checker found `6,416` findings over `65,160` draws;
- independent 1,000-draw-per-band segmentation found below-minimum realized group counts and illegal mixed `1/8` rows (`checks/baseline-structure-probe.json`).

## Selected repair

Version `3.0.0` constructs one of five canonical morphology profiles exactly. Run heights are allocated without retries or mutation, row kinds alternate, both public controls are observable, and the complete selected grammar is enforced by `self_check`/`strict_canonical_like`.

The canonical Racket semantics were not changed. The task-specific base solution source text was synchronized to the equivalent canonical program so authority-sync is exact.

## Teaching contract

Three demonstrations plus one query use consecutive accepted samples. Six executable rivals cover row-index, one-based grouping, first-row-only, both color-specific variants, and recolor-all-nonzero. Every generated grid individually refutes every declared rival; task tests and the 300-lesson source-bound census also check every held-out query position.

## Known restriction

The selected distribution is narrower than the full semantic domain: five shapes, alternating row kinds, and no row repeat at distance two. This is intentional canonical anchoring, not a claim that the Racket rule requires those restrictions. A future expansion should add nonalternating lawful group schedules with equally explicit shortcut witnesses.
## Current reviewer considerations

Source SHA-256: `e72a835204505c76e3d317fdf8673912e55b982b021bee1c919bc27f10e9fb76`.

# Design decisions for `be5d9fa6fec1`

## D1 — Keep the selected Racket semantics

**Choice.** Preserve the canonical rule: partition rows into maximal equal-row groups, number groups from zero, and recolor every nonzero cell in groups whose index is divisible by three.

**Original rationale.** Unknown; retained notes were empty. The five canonical pairs and both old Racket spellings agreed behaviorally.

**Alternatives considered.** Rewriting the Racket program, changing group origin to one, or counting physical row indices. Rejected because the canonical pairs, canonical source, rule hash `0ff6975f3e81`, and parity probe all support the selected zero-based transition-group law.

**Probe/failure mode.** `reference_probe.intended_output` is independent of generator helpers; task tests compare it with every canonical label and with real Racket execution. One-based and row-index alternatives are explicit rivals.

**Limitation.** The Python oracle is regression evidence, not authority; Racket remains label authority.

## D2 — Synchronize source text, not behavior

**Choice.** Replace only the task-specific base solution's `raw_code` and `target_code` with the exact canonical Racket program text.

**Rationale.** Before defect lint reported two behaviorally equivalent source spellings and final intake requires a clear authority. Synchronizing removes ambiguity while preserving all outputs.

**Alternative.** Leave beautification divergence. Rejected because it creates needless provenance uncertainty. Changing the canonical ledger was also rejected because no semantic defect was found.

**Probe/failure mode.** Final `authority_sync` verifies exact hashes and execution parity; `rule_smoke` remains green.

## D3 — Use five canonical morphology profiles

**Choice.** `profile_id` selects one of five exact `(height, width, group-count)` triples: `0=(20,4,14)`, `1=(19,5,12)`, `2=(14,5,11)`, `3=(15,3,8)`, `4=(22,4,16)`.

**Original rationale.** The old generator tried broad widths and requested block counts, but no retained rationale explained why those ranges were preferable. Measured support was only `3/60` exact canonical-profile hits and `0/20` in hard.

**Alternatives considered.** Retain arbitrary widths/group counts; add only the five profiles as a minority; replay canonical inputs. Broad support was rejected because requested groups were not reliably realized and profile support was poor. Canonical replay was rejected; 500 generated samples have no exact canonical-input overlap.

**Probe/failure mode.** `analyze` independently observes shape and maximal group count. Every exact profile override is tested in every difficulty band.

**Limitation.** Shape support is intentionally narrow and should not be read as a limitation of the rule itself.

## D4 — Reduce the public axis surface to two observable controls

**Choice.** Keep only `profile_id` and `start_kind`. Both are recoverable from the generated grid by `observe_overrides`; invalid types/values and unknown keys fail loudly.

**Original rationale.** The old nine-axis declaration attempted broad control, but many controls were not jointly valid, were difficulty-conflicted, or lacked an observer.

**Alternatives considered.** Keep density, min/max block-height, texture aliases, and requested block count. Rejected because a training-data control should be pixel-observable and exact, or explicitly declared incompatible. Hidden micro-controls added a large false contract surface without adding distinct rule concepts.

**Probe/failure mode.** Exhaustive `5 profiles × 2 starts × 4 bands` exact-override test; ten invalid/unknown override cases; after override gate passes with unknown-key verdict `rejected`.

**Limitation.** Row-density variation remains stochastic rather than directly addressable.

## D5 — Allocate run heights constructively

**Choice.** Start every group at height one, force group zero to height two, then sample remaining capacity tokens so every height stays in `[1,3]` and the profile total is exact.

**Rationale.** This removes retries, clipping, and post-hoc mutation. A two-row first group directly separates transition-group counting from `row_index % 3` and first-row-only shortcuts.

**Alternatives considered.** Retry until requested group count appears; clip at 30 rows; build then edit a row to manufacture witnesses. All were rejected because the baseline census measured group counts below the declared minimum and mixed `1/8` rows.

**Probe/failure mode.** Every sampled grid is independently resegmented; exact group count, height range, and first-run height are asserted. Destructive split/tall/wrong-count mutations must be rejected.

**Limitation.** Group zero always has at least two rows, which is useful teaching evidence but a distribution regularity.

## D6 — Alternate lawful row kinds and avoid two-step row repeats

**Choice.** Groups alternate nonempty `0/1` and nonempty `0/8` rows. A row is not reused at the next occurrence of the same kind, so an `A–B–A` row sequence cannot obscure the intended group design.

**Rationale.** The canonical examples support both foreground roles; alternation makes every boundary explicit while still varying positions and densities. It also prevents post-hoc split signatures and color-role collapse.

**Alternatives considered.** Random kind schedules, all-eight/all-mix degenerates, rows mixing colors `1` and `8`, and all-zero rows. Rejected for this curriculum because they either weaken visible group boundaries or support color-specific/degenerate shortcuts. A future broader generator could admit nonalternating lawful schedules with explicit witnesses.

**Probe/failure mode.** Tests assert exact palette `{0,1,8}`, nonempty rows, alternating kinds, no mixed foreground row, and no distance-two row repeat across 180 draws per band.

**Limitation.** Alternation and no two-step repeat are stricter than the Racket law and may be incidental cues; this is explicitly documented in `REVIEW.md`.

## D7 — Weight difficulty by canonical profile, not by changing validity

**Choice.** Every band supports all five profiles. Easy favors lower group counts, hard favors higher group counts, and medium is balanced; `start_kind` is uniform.

**Rationale.** Difficulty should alter frequency without making an otherwise declared exact override invalid. The old band-local ranges rejected values that `AXES.valid` declared legal.

**Alternative.** Different valid domains by band. Rejected because the public contract has one valid domain and exact overrides should remain exact in every band.

**Probe/failure mode.** The same 10 exact combinations are generated and observed in `None`, easy, medium, and hard. Distribution tests also require every profile and both starts to appear in each 180-draw cohort.

## D8 — Make the selected grammar strict but canonical-owning

**Choice.** `self_check` and `strict_canonical_like` enforce profile shape/count, palette `{0,1,8}`, run heights `1..3`, lawful row kinds, and alternation.

**Rationale.** The former self-check accepted most structure-destroying mutations and minimal impostors. A strict checker is needed for training-data admission and mutation power.

**Alternative.** Keep a permissive checker and rely on generator behavior. Rejected because post-generation defects, hand-authored inputs, and override errors would remain invisible.

**Probe/failure mode.** Five canonical inputs pass. Malformed grids return diagnostics rather than exceptions, while mixed-row, zero-group, too-tall, split, missing-palette, and wrong-group-count mutations fail.

**Limitation.** Canonical all-`1` row patterns are accepted when lawful; generated `0/1` rows are narrower and always include background evidence.

## D9 — Declare a finite, executable teaching contract

**Choice.** Three demonstrations and one query are formed from consecutive accepted samples. Six named rivals are implemented for both semantic and lesson checks; every generated grid individually refutes each rival.

**Rationale.** The rule is vulnerable to row-index, indexing-origin, first-row-only, color-specific, and recolor-all explanations. Correct labels alone do not ensure a teachable bundle.

**Alternatives considered.** Prose-only rival claims, two demonstrations, or relying only on canonical pairs. Rejected because executable counterexamples and schedule-level checks are cheaper and falsifiable.

**Probe/failure mode.** Task tests cover 40 starts × 3 bands × 4 held-out query positions × 6 rivals. The source-bound census materializes 100 lessons per band and requires every query rotation.

**Limitation.** Six rivals are not a proof against every possible hypothesis.

## D10 — Keep an independent reusable probe

**Choice.** Add `workspace/reference_probe.py` rather than testing solely through generator-private functions.

**Rationale.** The original defect lived in the relationship between claimed structure and realized pixels. An analyzer that shares implementation helpers could repeat the same bug.

**Alternative.** Test only `self_check` and `rule_mirror`. Rejected because correlated code can create false confidence.

**Probe/failure mode.** The probe loads arbitrary generator paths, segments groups independently, owns separate rivals/oracle, supports portable canonical paths, and invokes actual Racket. `checks/baseline-structure-probe.json` demonstrates reuse against the frozen source.

<!-- arcpuzzles-current-voluntary-allocation:start -->
## Current voluntary allocation probe

User-requested extra probe retained at `generators/be5d9fa6fec1/evidence/voluntary-allocation-current/manifest.json`. It is outside the two formal ticket assignments: one reported seven-label3+4 Racket probe and bounded allocation proposal, not a new safety review, changed weight/policy, or training admission. Exact source and all private/public evidence are pinned. Current allocation-request pointer: `shared/tools/proposals/2d5456d5a6ef9927/voluntary/extra1/voluntary-allocation.json`.
<!-- arcpuzzles-current-voluntary-allocation:end -->

<!-- arcpuzzles-current-supplementary:start -->
## Current supplementary checks

Current source-bound ticket observations: `generators/be5d9fa6fec1/evidence/supplementary-current.json`. Results are reviewer-reported; blocked or unknown stays explicit. These observations do not approve a generator or variant, resolve audits, or admit data to training.
<!-- arcpuzzles-current-supplementary:end -->
<!-- review-f339646b581e5a8e:start -->
## 2026-10-24 — bounded robustness repair for review-f339646b581e5a8e

`generate` previously accepted an unknown `difficulty` until profile lookup/context construction failed indirectly. It now validates the difficulty at the public function boundary and raises `ValueError("unknown difficulty: ...")` for unknown strings, case variants, integers, and booleans. A parametrized regression covers `"unknown"`, `"DEFAULT"`, `0`, and `True`. The canonical rule, version `3.0.0`, and `RULE_HASH = "0ff6975f3e81"` are unchanged. The full task-local suite passes `88/88`; retained RED/GREEN evidence is under `checks/be5d9fa6fec1-unknown-difficulty/`.
<!-- review-f339646b581e5a8e:end -->

## Current native parametric proposal — row-run traversal

The canonical generator and exact rule `0ff6975f3e81` remain unchanged. New
`workspace/parametric/` implements `step_mode=fixed3|height_plus_one`; the default
program is byte-identical to the canonical authority. In the alternate rule,
maximal identical-row runs supply their heights, and the currently selected run
advances the traversal by its own height plus one. The next selected index therefore
determines which input-derived height is read next. The run table is computed
from the original input; painting does not resegment it.

This proposal broadens only its own sampler: adjacent distinct patterns of the
same color, nonadjacent A–B–A repetitions, varying densities and 1–3-row run heights.
Matched input streams isolate rule effects. Two constructive demonstrations
refute the declared finite shortcuts, including reusing the first height forever;
ordinary qualification uses three. Counts support 2–6 demonstrations and 1–4
independent, distinct queries. Query profiles include meaningful 8×3 and 30×30
bounds, not empty padding. There is no new production size override.

`probe.py` is the reusable bounded Racket-backed self-audit and public writer.
The native source inventory, qualification/execution and causal witness travel
with this return. Public bundles remain controller-side; `visible_turn` exposes
one query without count hints and matches single-query first-turn bytes.

Next action: integrate this exact task-local source, run native qualification,
inspect the height-dependent witness, then perform fresh owner acceptance.
Reviewer qualification does not mark the variants accepted or admit training data.
Finite rival coverage does not establish universal rule uniqueness.
