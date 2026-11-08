# Working notes: 20b53e0c4957

## Current rule and authority

Two full-height color-5 columns split the input into panels A, B, and C. A is a solid rectangle. B is a nonempty strict subset of A in the same panel coordinates. The authoritative transformation computes `A - B`, expresses those removed cells relative to A's occupied bounding-box origin, and erases the same relative offsets from a copy of C at C's occupied bounding-box origin. C may already contain holes, which are preserved. The Racket authority was not changed; `RULE_HASH = "9217dc891941"` pins the canonical source used by the final checks.

## Review lead and reproduced defects

I used retained return `review-30f42b66093700f5:v0001` as a lead, then reproduced its claims against the pinned baseline generator SHA-256 `58a47cd3170341e7726dfc00d66f91319782b05c49ca8fb269eba692de902161`.

The prior normal sampler filled all three panels, making A's and C's bounding-box origins identical and making the intended rule observationally equivalent to simpler whole-B recoloring/copy shortcuts. The baseline validator also accepted an A=B no-op and an empty C panel. Finally, its advertised `n_removed=1..20` axis exceeded the values its difficulty-local draw paths could construct. The baseline lint stage also lacked the canonical rule pin.

Minimal retained repair witnesses are in `counterexamples/review-67927c57be9a8517/repair_witnesses.json`; focused tests replay them.

## Final design decisions

- A and B share a translated solid rectangular object; B removes 1..6 cells.
- C has the same bounding-box dimensions, is translated independently, uses another canonical color, and has one independent interior hole.
- Every accepted generated input must refute three canonical-fitting shortcuts: recolor B in place, normalize/paste B at C, and use raw A/B panel coordinates instead of bbox-relative coordinates.
- The exact public control surface is deliberately small: `panel_h`, `panel_w`, `n_removed`, and `palette_id`. All are observable and honored across every difficulty band.
- Every fourth unoverridden sample is exact canonical input size 4x14 (4x4 panels), supplying the profile-floor witness without weakening ordinary broad sampling.
- `self_check` accepts all three canonical inputs while rejecting missing dividers, empty panels, A=B, B outside A, wrong colors, excessive holes, and malformed grids.

## Evidence and limits

Final generator SHA-256: `7e1efe378d3881fc28a56741ac00bc76ca7fe6b766289b7e536e6c02315a098a`.

The source-bound final battery is 12/12 green in `checks/after-final/`. Task-local tests are 45/45 green in `checks/task-tests-final/`. A 300-lesson, three-band census with three demonstrations and one query found 0/300 production ambiguities and 0/1200 query-rotation ambiguities over 1,187 unique inputs (`checks/lesson-census.json`). Fixed-seed enumeration of all four declared schedule residues likewise found 0/12 lesson and 0/48 rotation ambiguities (`checks/schedule-period-s0.json`).

These finite declared-rival checks do not prove universal identifiability against every hypothesis or every seed. The generator intentionally supports only solid rectangular A objects, one or two pre-existing C holes in validation, 1..6 transferred removals, panel sizes within the declared bounds, and the three retained canonical color pairs. Expansion beyond that domain should add explicit controls, witnesses, and exact-override tests rather than silently broadening the current contract.

<!-- arcpuzzles-current-audit-assessment:start -->
## Current bounded audit assessment

Return: `review-30f42b66093700f5:v0001`. Disposition: **resolved**. Evidence basis: `reviewer_reported`.

Audited source SHA-256: `58a47cd3170341e7726dfc00d66f91319782b05c49ca8fb269eba692de902161`. At disposition, the audited source differs from the current source; this assessment covers audited bytes only.

### Current decision

Repair addresses previous no-removal/empty-C validator acceptance, full-panel bbox-transfer support shortcut, and misleading removal range via translated A/C bboxes, mandatory C hole, strict validation and honest exact1..6removal controls. Reported45tests and300lesson/1200rotation census support bounded resolution. Missing old probe dependency remains separate open tooling issue. Exact repaired source=7e1efe378d3881fc28a56741ac00bc76ca7fe6b766289b7e536e6c02315a098a. Explicit maintainer resolution on reviewer-reported source; original probe dependency request remains open. Evidence=/home/user/Desktop/ARCpuzzles/var/review/new-return-tools-review/passive-tools-review-67927.json sha256=7c50c960d41492aeaef4661dd24a2ab9f5e29c504e8b9841ec764fb8c89e0630

### Assessment or prior finding

## 20b53e0c4957

### Identity and scope

- Immutable generator: `checks/audit/20b53e0c4957/context/generator.py`, version 2.0.1.
- SHA-256: `58a47cd3170341e7726dfc00d66f91319782b05c49ca8fb269eba692de902161` (matches assignment).
- Canonical `program_solution` UTF-8 SHA-256: `9217dc89194178fe9456119a975e48aae03f999ae4e039673dee23979d363025`.
- Read selected source, canonical task including Racket rule and examples, notes, SUMMARY, and workspace README. No tests or alternate implementations were present in the supplied target directory. No private solve files were read. Audited source was not edited.
- Focused probe: 12 normal generated samples (seed 19, indices 0–3, difficulty None/easy/hard), three explicit degenerate textures (seed 7, index 0), one handmade validator-only bbox witness, and three advertised-axis override calls. This is not an exhaustive seed sweep.
- Reproduce using the portable command below; the probe accepts explicit context, runtime, output, and retained-reference paths.
- `evidence.json` contains exact arguments, grids, self-check results, local mirror outputs, rival outputs, hashes, and rejected override errors. `input.json` contains five ordered grids for authoritative reference application.

### A20.1 — Concrete validator false negatives for intentional negative controls

**Severity: medium. Domain: generator-produced, explicit degenerate texture overrides only.**

`generate(7, 0, texture="identical_a_b")` and `generate(7, 0, texture="no_panel_c")` both return grids for which `self_check(grid) == []`. The former has no removal at all and violates the declared nontrivial-removal invariant. The latter has no occupied C object and violates both the declared C invariant and the validator's own promise that all three panels contain non-{0,5} cells. The predicate at source lines 32–34 checks occupancy globally; it never checks each panel. It also never compares A and B. The explicit `no_separators` negative control is correctly rejected, so these two passes are reproducible inconsistent validation, not merely the observation that the generator provides negative textures.

The authoritative Racket application returned a valid all-zero 3x3 output for the empty-C case, with no exception. The local mirror deliberately marks an empty bbox as a local error and does not replicate this tolerance; it is not evidence of a reference failure. This finding concerns certification of a grid that violates the declared generator invariants, not a runtime failure or normal-domain label mismatch.

Suggested remedy for review: check exact three-panel shape/divider geometry, require occupied A and C, check the declared A/B relationship and nonempty removal set, and reject the explicitly degenerate fixtures. Any decision to accept empty-removal instances should be reflected consistently in metadata and validation.

### A20.2 — Proven shortcut equivalence across the ordinary generator domain

**Severity: medium coverage concern. Domain: every ordinary generated instance, by source construction; distinguishing witness is validator-only.**

The rival implemented in `probe.py` splits by width, ignores A completely, and outputs B with every nonzero cell replaced by C's top-left color. It matches the local canonical transcription on all 12 normal samples. More strongly, source lines 111–122 establish its equivalence for all ordinary instances: A and C occupy their full panels, hence both bbox origins are (0,0); the removed set is exactly the zero cells of B; C has a single color everywhere. Varying colors, panel dimensions, or hole positions cannot distinguish this rival. The retained canonical examples also use that same solid-panel family.

This is a coverage finding rather than an incorrect ordinary reference output. The generator can teach "recolor B" without requiring comparison with A or bbox-relative transfer, although its written rule describes those operations.

The handmade `bbox_shift_shortcut_witness` uses 4x4 panels. A occupies rows/columns 1–2; B removes A's local top-right cell; C occupies rows/columns 0–1. It passes the current self-check but is outside the ordinary generator's full-panel invariants. The local transcription yields:

```json
[[7,0,0,0],[7,7,0,0],[0,0,0,0],[0,0,0,0]]
```

The rival yields:

```json
[[0,0,0,0],[0,7,0,0],[0,7,7,0],[0,0,0,0]]
```

The authoritative Racket application confirms the displayed canonical output at input index 3; the rival differs. It also confirms the rival on one ordinary sample (index 4) and on the three explicit degenerates (indices 0–2). Do not describe this handmade witness as produced by the ordinary generator. If broader bbox transfer is the intended skill, generate A/C objects with independently varying margins or shapes and include cases where B's zeros include cells never occupied by A. If the solid-panel subdomain is intentionally the whole target, this rival is a simpler exact solution on that subdomain and the skill claim should be scoped accordingly.

### A20.3 — Advertised `n_removed` range contains unreachable override values

**Severity: low metadata/override contract defect. Domain: generation API; no grid is produced.**

`AXES["n_removed"]["valid"]` advertises `1..20`. A documented-valid `n_removed=20` override is rejected at seed 7, index 0 for each of None, easy, and hard difficulty. The errors respectively report allowed ranges `[2,6]`, `[1,3]`, and `[3,9]`. Since all recognized difficulty branches have a maximum of 9, values 10–20 are unreachable through any branch. This is independent of panel capacity; hard panels have at least 25 cells. The exact errors are in `evidence.json`.

Suggested remedy for review: expose difficulty-specific accepted ranges accurately, or use declared validity bounds for overrides while keeping default random draw bounds narrower.

### Limits and negative result

No ordinary generator/reference disagreement was found by the local mirror on these 12 samples. All 12 ordinary outputs passed self-check. The supported reference command completed successfully on five grids: three explicit negative textures, one validator-only witness, and one ordinary generated sample. All five outputs are valid and have no errors. The four defined local mirror predictions match exactly; the empty-C local mirror check is intentionally undefined, while Racket returns zeros. The rival matches four of five authoritative outputs and fails the validator-only witness. The remaining 11 normal samples were checked against the local mirror, not executed through Racket. No claim is made about an exhaustive ordinary distribution, unsupported override values, or external production callers' treatment of negative textures.


### Authoritative reference binding and exact command

The root executed the supported tool in cwd `/dev/arc-review-9aaf365d53aa/WORK/repo`:

```sh
arcpuzzles apply 20b53e0c4957 --input ../checks/audit/20b53e0c4957/input.json --out ../checks/audit/20b53e0c4957/racket.json
```

The returned report is preserved as `racket.json`. `probe.py` verifies its generator hash, all five index/input bindings, and the executed canonical rule ID against the canonical program hash prefix. The report returns `executed_rule_hash = catalog_rule_hash = 9217dc891941`, `rule_hash_matches_catalog = true`, and exact executed `rule_text_sha256 = a137ab41d0db02ecbd4954ce846853226641065a8ee64389f95b3812973f6d62`. This returned rule-text hash is preserved separately from the raw canonical task `program_solution` SHA-256; they describe different serialized text representations and are not substituted for one another. The report file hash, exact commands, all predictions, output hashes, and precise `test_counts` are included in `evidence.json`.


### Portable replay in the return bundle

The audit folder contains a minimal `context/` with exactly `generator.py` and `canonical_task.json`. The generator copy is byte-identical to the immutable assigned source. `probe.py` accepts `--context`, `--shared-runtime`, `--out`, and `--racket-report`; its defaults use the adjacent context and output folder, the original scratch runtime path, and `OUT/racket.json` when present. Explicit paths make the replay independent of scratch layout. Bytecode caching is disabled so replay does not add files to the immutable context.

From the return bundle's `WORK/repo` directory:

```sh
python ../checks/audit/20b53e0c4957/probe.py \
  --context ../checks/audit/20b53e0c4957/context \
  --shared-runtime shared/runtime \
  --out ../checks/audit/20b53e0c4957 \
  --racket-report ../checks/audit/20b53e0c4957/racket.json
```

This regenerates `input.json` and `evidence.json`, checks predictions against the retained official report, and verifies every report input/index binding. It does not execute a new Racket apply. The explicit-path scratch replay was completed successfully; all original observations, source/rule hashes, authoritative results, and counts were compared against the previous evidence and remained identical. The actual replay command and resolved paths are recorded in `evidence.json`.

Counts remain: 12 ordinary generation calls and passes; three explicit negative textures with two self-check passes and one rejection; one handmade validator-only grid and pass; three documented override calls and rejections; five authoritative reference grids with five valid outputs and zero errors; four defined local mirror matches plus one locally undefined empty-bbox case; and four rival matches plus one rival mismatch. Authoritative input/output shapes by index are `3x11 -> 3x3`, `3x11 -> 3x3`, `3x11 -> 3x3`, `4x14 -> 4x4`, and `4x17 -> 4x5`.

The disposition records an explicit decision. It does not imply a fresh execution, universal correctness, closure of other findings, or training admission.

[Retained evidence](counterexamples/review-30f42b66093700f5-v0001/audit_assets.json), manifest SHA-256 `7b329a3d3a44951db61f4fd90c29f0d2fcf78318d87a1057092399155a572776`.
<!-- arcpuzzles-current-audit-assessment:end -->
## Current reviewer considerations

Source SHA-256: `7e1efe378d3881fc28a56741ac00bc76ca7fe6b766289b7e536e6c02315a098a`.

# Decisions for 20b53e0c4957

## D1 — Keep the canonical Racket authority unchanged

**Prior choice:** unknown; the selected baseline did not pin `RULE_HASH`.

**Decision:** retain the existing bbox-relative A-minus-B transfer rule and pin `RULE_HASH = "9217dc891941"`.

**Rationale and probes:** canonical-pair tests independently transcribe the rule and match all 3 labels. The official final `rule_smoke`, `racket_lint`, and `authority_sync` stages are green. The defect was in the input distribution and validator, not in the authority.

**Rejected alternative:** rewrite the authority to “recolor B” because that matched the baseline's ordinary samples. That would codify an accidental shortcut and disagree with a shifted-bbox lawful input.

**Failure mode / limit:** any later authority edit invalidates this pin and all source-bound semantic evidence.

## D2 — Reverse full-panel sampling; use translated sub-bounding-box objects

**Prior choice:** A, B, and C occupied their whole panels. This made their bbox origins coincide and erased the distinction between bbox-relative transfer and raw-coordinate/whole-B rules.

**Decision:** A is a solid translated rectangle; B is its strict subset in the same coordinates; C has equal bbox dimensions but an independently translated origin.

**Evidence:** retained audit lead `review-30f42b66093700f5:v0001`; final replay artifact `generators/20b53e0c4957/counterexamples/review-67927c57be9a8517/repair_witnesses.json`; `test_every_generated_example_is_a_bbox_transfer_witness`; semantic-gate witness counts 600/600 for each declared rival.

**Alternatives considered:**

- Keep full panels and add a few sparse diagnostic textures: rejected because ordinary training data would still teach the shortcut.
- Translate only C while allowing arbitrary A/B shapes: deferred; rectangles give a small exact domain that is easy to validate and still exposes the intended relative-coordinate law.

**Failure mode / limit:** rectangular support is narrower than every conceivable lawful input. Broadening shape topology needs new exact axes, validator rules, and rivals.

## D3 — Give C an independent interior hole

**Prior choice:** C was fully occupied.

**Decision:** every ordinary generated C object starts with one interior hole not induced by B.

**Rationale:** this distinguishes “modify C” from “construct/recolor B” and proves that unrelated C structure must survive. The hole is never selected as a B removal, so the lesson contains two separable causes of absence.

**Rejected alternative:** make C solid and rely only on translation. Translation refutes raw-coordinate rivals, but a normalized B-paste rival can remain plausible in some layouts.

**Failure mode / limit:** generated C has exactly one hole; validation permits zero through two so canonical examples remain accepted. More complex C texture is untested.

## D4 — Reduce the exact override contract to four observable axes

**Prior choice:** the generator advertised several generic or singleton axes and `n_removed=1..20`, while difficulty-local draws could not construct much of that domain.

**Decision:** expose only `panel_h=4..8`, `panel_w=4..7`, `n_removed=1..6`, and `palette_id=0..2`; add `observe_overrides`; reject unknown and mistyped controls.

**Evidence:** cross-product focused tests exercise boundary combinations in every difficulty band; final override stage is green.

**Rejected alternative:** preserve decorative axes (`density`, `texture`, etc.) as aliases. They add apparent control without changing the input and make automated coverage misleading.

**Failure mode / limit:** exact overrides intentionally do not control object height/width, origin, hole coordinate, or individual removed cells. Those remain deterministic random choices.

## D5 — Bound removals at 1..6

**Prior choice:** advertised 1..20, with ordinary branches reaching at most 9 and some values impossible for sampled panel geometry.

**Decision:** use 1..6, with band defaults easy 1..3, medium 2..5, hard 3..6, and exact overrides honored across bands.

**Rationale:** a minimum 3x3 object minus the reserved C-hole offset always leaves at least 8 removable candidates, so 6 is constructively safe across the whole declared panel domain. It provides difficulty variation without rejection-heavy edge cases.

**Rejected alternative:** raise the upper bound conditionally with larger objects. That creates joint-axis incompatibilities and a more complicated observer contract with little semantic gain.

## D6 — Add a four-step canonical-size schedule

**Decision:** every fourth unoverridden sample uses 4x4 panels, producing an exact 4x14 canonical input profile; other starts retain broad band-specific panel sizes.

**Rationale:** this satisfies the native per-band profile floor without making all data canonical-sized. `LESSON_SCHEDULE_PERIOD = 4` makes the schedule explicit and auditable.

**Evidence:** profile-floor stage green; fixed-seed enumeration in `checks/schedule-period-s0.json` covers all 4 residues across 3 bands (12 lessons, 48 rotations).

**Rejected alternative:** probabilistic canonical-size hits only. A 20-draw floor could fail nondeterministically or leave some bands unsupported.

**Failure mode / limit:** fixed-seed residue enumeration is not all-seed proof. Any schedule change must regenerate the census receipt.

## D7 — Qualify every generated input against three canonical-fitting rivals

**Decision:** declare and execute `recolor_b_absolute`, `copy_b_to_c_bbox`, and `absolute_removed_positions`; accept a candidate only when all disagree with the local authority mirror.

**Rationale:** all three fit every canonical pair, so merely matching canonical labels cannot distinguish them. Qualification prevents accidental reintroduction of the baseline shortcut.

**Evidence:** tests independently verify that each rival fits all canonical pairs and loses on every sampled final input. The final semantic gate reports each witness firing 600/600.

**Rejected alternative:** rely on aggregate frequency (“usually translated”). A single ambiguous example can participate in an underdetermined lesson; candidate-level qualification is cheap here.

**Failure mode / limit:** this is a finite named rival set, not universal uniqueness. New plausible shortcuts should be added as executable competitors, not only prose notes.

## D8 — Make `self_check` relational and canonical-compatible

**Prior choice:** validation mostly counted global colors and explicitly bypassed selected degenerates.

**Decision:** validate grid shape/colors, exact dividers, nonempty single-color panels, A solidity, B as a nonempty strict subset of A, removal count, A/C bbox equality, C color role, and bounded pre-existing C holes. Return diagnostics rather than raise on malformed inputs.

**Evidence:** focused near-miss tests, both retained degenerates, all 3 canonical inputs, 128 ordinary generated inputs, and final battery self-check/strict-profile stages.

**Rejected alternative:** require the exact generated domain (for example exactly one C hole and height >=4). That would falsely reject canonical examples and conflate generator support with lawful authority support.

## D9 — Require lesson-level evidence, not only input-level labels

**Decision:** use 3 demonstrations plus 1 query, declare `LESSON_COMPETITORS`, and run both production and query-rotation diagnostics. Preserve the first post-repair battery failure caused by missing schedule enumeration, then satisfy it with a source-bound receipt rather than suppressing the warning.

**Evidence:** `checks/after/` (intermediate warning), `checks/schedule-period-s0.json`, `checks/after-final/`, and `checks/lesson-census.json`.

**Limits:** 300 random lessons and one fixed-seed complete schedule are finite. The reports support “no ambiguity found against declared rivals,” not “the rule is uniquely identifiable under all hypotheses.”

## D10 — Leave peer-audit targets unchanged

Tasks `71d5c4ac6ea3` and `76e1a5257af0` were audit-only. I retained exact generated lessons and official Racket outputs showing underdetermination, plus strict audit/lint receipts, but made no source edits. Their findings are separated in `AUDIT.md` so intake cannot mistake them for part of this repair.

## D11 — Add a native matched-input two-setting family without changing production

**Decision.** Add `workspace/parametric/` with exact canonical default `hole_policy=preserve` and an alternate `repair_then_transfer` rule. Both settings share identical generated inputs; episodes support 2–6 demonstrations and four distinct queries. A lawful 30x29 query supplies the size-stress case.

**Rationale.** The canonical output depends on an input-derived A-minus-B mask and C's state. The alternate setting changes only whether C's occupied bounding box is repaired before applying that same relative mask, so it creates a real sequential branch rather than a cosmetic parameter.

**Evidence.** `checks/20b53e0c4957/qualification/qualification.json`, `checks/20b53e0c4957/causal/witness.json`, and `workspace/parametric/evidence/manifest.json`. The bounded protected-Racket audit executes five named rivals and retains zero demonstration-fitting/query-changing survivors for the sampled episodes.

**Limit.** This is reviewer-ready prototype source only. Owner exact-source qualification, acceptance, and any training admission remain separate.

## D12 — Preserve public first-turn semantics

**Decision.** Export each four-query episode as four sequential single-query views with no total-query-count hint, then test hidden-field invariance and visible-change positive controls.

**Evidence.** `checks/20b53e0c4957/first-turn.json` covers 16 public views, four first turns, 24 private-field mutations, and four positive controls.

**Limit.** These are finite interface checks; they do not measure downstream learner behavior.
