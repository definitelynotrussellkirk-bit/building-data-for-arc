# Working notes: 0b6b3a286ad0

Record design decisions, hypotheses, review findings, and unresolved questions here.
Imported associated notes retain original evidence/timestamps in `evidence/associated_notes.jsonl`.

## Current parametric review — review-f03127eed7712b25

The task-local `workspace/parametric/` candidate preserves production 4.0.0
(`58cb428fafff0c88ea547b63ba14c852bcf48283dabb131cb8c4b252e2bc336a`)
and the exact canonical program. `lookup_depth=1` returns that program's original
bytes; depth 2 uses the first selected value grid as the query for a second lookup.
The candidate supports 3–6 demonstrations and 1–4 queries independently. Three
core demos separate composition from direct lookup, inversion, fixed intermediate
and constant-answer rules; two demos cannot exclude all those alternatives in
this construction. See the prototype README for the explicit grammar and limits.

Self-review repaired fixed first-query order and a key-color-minority shortcut.
Query order now varies deterministically by seed, while selected teaching states
repeat the true motif to make its color either rarer or more frequent at both
hops. Each repair has a regression observed failing before and passing after.
Production geometry and production teaching schedules below remain unchanged;
the candidate separately broadens inputs through substantive 30×30 cases.

The current-source sampler/rival audit, focused tests, native qualification and
wrong-intermediate replay are returned under `checks/0b6b3a286ad0/`, with small
inventory-bound receipts in `workspace/parametric/evidence/current/`. The public
projection tool retains four queries privately and emits one query per visible
view; its verifier and rejection tests are reusable by future reviewers. Finite
rival elimination does not prove universal uniqueness. Profile roles and key-mask
families remain bounded, and no whole-board rotation coverage is claimed.

Next owner action: inspect the exact delta and source-bound dependency argument,
then run native qualification and acceptance on the integrated bytes. Reviewer
readiness does not constitute owner acceptance or training admission.

## Earlier production decisions (retained)

## Current reviewer considerations

Source SHA-256: `58cb428fafff0c88ea547b63ba14c852bcf48283dabb131cb8c4b252e2bc336a`.

# Design decisions — `0b6b3a286ad0`

The decisions below distinguish the baseline's documented intent from assumptions introduced in this review. Evidence paths are relative to the packet root.

## D1 — Keep the Racket rule authoritative and unchanged

**Baseline rationale.** The baseline already described the intended rule correctly: crop the five panels, search for `KEY1` with template zeros as wildcards and no transform, return `VALUE1` on a match and `VALUE2` otherwise. Authority sync passed before the patch.

**Decision.** Do not alter canonical data, selected Racket source, or archival Racket source. Implement a Python `rule_mirror` only for tests and semantic diagnostics; all retained exact counterexamples use the public generation API so their reported outputs come from canonical Racket.

**Alternatives rejected.** Rewriting Racket to require `KEY2` would make the implementation agree with the new teaching domain but would change the actual task. Expanding Racket with layout validation would similarly mix generator-domain policy into output authority.

**Probe and failure mode.** Before and after `authority_sync` and `rule_smoke` pass. The remaining boundary is explicit: generator-valid `VALUE2` boards always contain `KEY2`, but Racket-valid boards need not.

## D2 — Restrict geometry to the two canonical profiles

**Baseline rationale.** Version 3.1.2 varied height, panel widths, crop dimensions, and query width for combinatorial variety, with only a 30-column cap. The original reason for the exact numeric ranges beyond general variety is unknown.

**Decision.** Emit only `6×25×5` and `7×26×5`, with divider columns `3,8,12,17`, crop dimensions `3×3`, `4×4`, `3×3`, `4×4`, and query width `height+1`.

**Alternatives considered.**

- Keep broad dimensions and merely repair metadata: rejected because baseline had `0/60` exact-profile support and median object-count drift.
- Mix canonical profiles with larger exploratory layouts: rejected for this version because it weakens the profile floor and introduces a second distributional question before the semantic curriculum is stable.
- Declare a profile opt-out: rejected because the canonical layouts are easy to support exactly.

**Probe and failure mode.** Final profile floor is `60/60` exact with `20/20` per band; all three canonical inputs pass the same strict validator. The limitation is lower geometric breadth.

## D3 — Make `KEY2` real evidence for every `VALUE2` lesson

**Baseline rationale.** The baseline explicitly called `KEY2` decorative and generated the else branch primarily as “no `KEY1` match.” That is faithful to the minimum executable Racket condition.

**Decision.** Every `no_match`, `rotated_decoy`, and `near_miss` query contains an exact `KEY2`. This follows the visible key-value pairing in every canonical else demonstration and blocks an easy “`KEY1` versus arbitrary noise” representation.

**Alternatives considered.**

- Preserve decorative `KEY2`: rejected because the generated task would visually advertise a second mapping while rarely requiring the learner to use it.
- Change authority to select `VALUE2` only on `KEY2`: rejected under D1.
- Sometimes omit `KEY2`: rejected for the selected strict teaching domain; this can be revisited as a separately declared extrapolation split.

**Probe and failure mode.** `test_v2_textures_embed_key2_and_never_accidentally_match_key1` covers 72 forced draws; semantic census records exact-key2 else support on 362/600 final draws. The validator rejects queries containing neither key or both keys.

## D4 — Use a deterministic five-example cyclic curriculum

**Baseline rationale.** `EXAMPLES_NEEDED = 4` and random texture choice were intended to cover both outcomes and several decoys, but there are five semantically distinct textures. Four randomly drawn examples cannot guarantee coverage of all five competitors.

**Decision.** Schedule `match`, `no_match`, `rotated_decoy`, `near_miss`, `wildcard` by `sample_index mod 5`; set `EXAMPLES_NEEDED = 5`. Every cyclic start has one of each texture.

**Alternatives considered.**

- Weighted random textures: better marginal variety, but lesson-level identifiability remains probabilistic.
- Four examples with one multi-purpose board: rejected because combining wildcard and decoy evidence makes the board harder to parse and can create ambiguous matches.
- More than five examples: unnecessary once each declared rival has a minimal clean witness.

**Probe and failure mode.** The task test checks 10 cyclic starts in each band. The semantic gate materialized 12 lessons and found 12/12 identifiable, with all six competitors eliminated. The cost is a longer lesson than the canonical two-example presentation.

## D5 — Use finite connected masks and preserve canonical visual grammar

**Baseline rationale.** Random 2–3-cell keys and 2–5-wide values maximized shape variety. It also produced morphology drift and layouts unlike the canonical examples.

**Decision.** Use a finite library of connected, exact-bounding `3×3` key masks and connected `4×4` value masks, expanded by unique rotations/reflections. Filter rotationally symmetric `KEY1` masks so a rotated-decoy witness is observable. Use distinct key colors and a shared value color, yielding exactly five colors including background and divider.

**Alternatives considered.** Procedural polyomino generation was possible but would require more rejection logic to guarantee full bounding boxes, connectivity, asymmetry, no accidental matches, and canonical palette/profile constraints. A small reviewed library is simpler and deterministic.

**Probe and failure mode.** Final morphology marginals align with canonical values; 200 task-test draws require at least 190 unique inputs, and the battery reports 100% unique inputs across its 300 pairs. Finite masks still bound out-of-domain morphology.

## D6 — Encode semantics as executable observers, rivals, and mutations

**Baseline rationale.** The baseline `self_check` only counted divider columns. It could not distinguish correct lessons from wrong-branch, accidental-match, malformed-crop, or palette errors.

**Decision.** Build one parser, `semantic_observables`, and derive `self_check`, strict canonical validation, override observation, test mirror, witness predicates, rival rules, lesson identifiability, and mutation fixtures from it.

Declared rivals are fixed `VALUE1`, fixed `VALUE2`, “either key selects `VALUE1`,” rotations count, one-cell near misses count, and zero-strict matching. The strongest canonical-fitting rival is separately declared in `CANONICAL_SHORTCUTS`.

**Alternatives considered.** Independent validators for each gate were rejected because duplicated parsers drift. A permissive structural checker plus prose notes was rejected because the original semantic gate had no contract to execute.

**Probe and failure mode.** Final semantic census is 600/600 strict; every witness fires in every band; each witness/rival claim holds on 60/60 checked fired cases. Eight task-specific malformed boards are rejected. A shared parser can still share a bug with its derived mirror, so Racket smoke tests and public-API counterexamples remain necessary independent checks.

## D7 — Make override behavior exact and difficulty modest

**Baseline rationale.** The baseline exposed `panel_h` and `texture`, but difficulty narrowed `panel_h` bounds in ways that made declared valid overrides fail; unknown keys were silently accepted.

**Decision.** Reject unknown overrides, consume both declared axes through `gen_ctx`, and report their realized values through `observe_overrides`. Easy fixes height 6, hard fixes height 7, and medium/default alternate the two profiles unless explicitly overridden.

**Alternatives considered.** Declaring many incompatibility combinations was rejected because both exact axes can be supported cleanly. Making difficulty change semantic decoy type was rejected because the lesson schedule, not difficulty, must guarantee competitor coverage.

**Probe and failure mode.** Final override stage has no findings, no warnings, and rejects its unknown-key probe. Difficulty affects lawful content selection but is not claimed to measure reasoning hardness.

## D8 — Keep `EXAMPLES_NEEDED` a literal integration contract

**Original rationale.** Writing `EXAMPLES_NEEDED = len(TEXTURES)` made the semantic relation self-documenting and was runtime-correct. The dependency on static AST reading was not documented in the generator interface and was discovered only during solve preparation.

**Decision.** Use literal `5` and add `test_examples_needed_is_a_literal_for_solve_episode_static_reading`.

**Alternatives considered.** Extending `solve_episode.py` to evaluate simple static expressions would be more flexible, but shared tooling is outside the selected-task edit scope. The tooling recommendation is recorded as F1.

**Probe and failure mode.** The blocked intermediate solve is retained under `checks/prior-solve-generator-116bb4a37919/`; final preparation reads five examples successfully. The literal can drift from `TEXTURES`, so another test asserts `EXAMPLES_NEEDED == len(SCHEDULE_PROFILES) == 5`.

## D9 — Test behavior, lesson windows, and integration locally

The new task-local suite covers canonical recognition and output parity, exact overrides, all else textures, wildcard semantics, every five-slot cyclic start, witness/rival behavior, deterministic fresh grids, a 200-draw diversity floor, mutation rejection, difficulty profiles, and the static solve contract.

The final direct command passes 10/10 tests. The full battery independently exercises Racket authority, profile support, semantic lesson assembly, diversity, overrides, grammar, and source synchronization.

## Known limitations and future checks

- Add a separately labeled extrapolation split before teaching Racket-valid “no key at all” else cases; do not silently mix them into the canonical-linked curriculum.
- If procedural masks replace the finite library, rerun accidental-match rejection, all cyclic starts, profile support, and output-bound checks.
- If a shorter lesson is desired, prove every cyclic window refutes the same declared competitor set rather than relying on per-texture frequency alone.
- Maintainer replay should score the masked solve and independently inspect the source-bound patch; local success is not admission.
