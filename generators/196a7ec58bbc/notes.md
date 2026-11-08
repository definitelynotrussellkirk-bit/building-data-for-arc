# Working notes: 196a7ec58bbc

## Current native candidate

The exact canonical default and production generator are unchanged. The native
adapter reuses the retained handedness implementation and adds `source_mode`:
whole input or the unique largest same-color four-connected nonzero component.
Selection supplies an object-only tight square crop; rotated quadrant tiling
consumes that matrix. This is geometric composition, not iterative-state simulation.

The first two demonstrations now select sides five and four. The earlier pair
both selected five, allowing a fixed-five crop to fit both demos and miss a
3×3 query. `checks/196a7ec58bbc/review-fixed-source-size.json` retains that
six-application protected-Racket counterexample; the second profile and the
`fixed_five_crop` rival regression repair it without increasing demo count.
The 4×4 dense-mask connectivity failure was also repaired and retained in tests.

Current evidence: 44 focused tests; 192/192 bounded Python sampling requests;
240 protected teaching applications for 12 rivals across two seeds/four settings,
with the first two demonstrations rejecting every tested rival; 224 protected
native qualification applications over the entire six-demo/four-query bank;
two selector interventions built and replayed by the native witness helper.
Exact receipts are `checks/196a7ec58bbc/{native-teaching-v2/report.json,
sampler-v2.json,qualification/qualification.json,causal/witness.json}`.
Earlier reports remain before-repair evidence, not current-source qualification.

Ordinary count is three demonstrations/four queries; supported counts are 2–6
and 1–4 independently. Native input sizes sampled are 2, 3, 9, 11, 12, 15. The lawful
upper boundary is 15×15 input and 30×30 output, because the whole-input canonical
rule doubles dimensions. The large comb has substantive content across the
canvas; this does not add production size overrides. Palettes, orientations,
positions, bar lengths and distractors vary. Across the bounded 16-seed sampler,
156 distinct inputs and 63 distinct queries occurred; cross-seed uniqueness is
not promised for tiny profiles.

`checks/tools/export_qualified.py` projects source-bound native labels into
16 separate actor files from four seed 0 controllers. Only the current actor file
is visible; answers, settings, future inputs and directory inventory stay private.
The exporter tests include exact first-turn equality for one/four query counts.

The native candidate is reviewer-ready. Exact-source owner acceptance remains
pending; no training admission is claimed. The finite rival set is not a proof
of universal identification. Production audit dispositions below are unchanged.

## Review `review-1e5bbd7c27fe6e1c`

The prior retained return `review-e1259b2e06dc7ffe-v0001` was used only as an audit lead. Its seed-33 evidence showed a lesson where a reflection/transposition rule fit all three demonstrations but differed on the query.

### Baseline findings

- Before battery: 9 green, 2 advisory, 1 failed.
- Defect lint: invalid seed/sample-index scalars accepted (33 warnings).
- Profile floor: exact 23/60, envelope 36/60, with zero exact easy-band support.
- Semantic contract: not declared; retained reflection ambiguity reproducible.
- Inherited task test used nonportable path assumptions in copied runtimes.

### Repair decisions

- Preserve the canonical Racket program and `RULE_HASH=24bc23963715`.
- Require exact integer seeds/indices and a nonnegative sample index.
- Admit generated 2×2/two-color layouts only with 3:1 counts, four distinct rotations, and a rotation-vs-reflection disagreement. Continue accepting the canonical diagonal 2:2 answer-equivalent exception.
- Anchor a two-color profile at sample-index residue 0 modulo 4 to guarantee support in the 20-draw gate without collapsing the rest of the distribution.
- Declare an executable `mirror_quadrants` competitor and require every ordinary grid and three-demo lesson to refute it.
- Make retained task tests portable through `reviewer_support` and add regression coverage for all repaired contracts.

### Final evidence

- Final generator SHA-256: `716d964e83da3769819ffa8e4c51ed38ffd7e375643fd97a4bb574db67b69af1`.
- Battery: 12/12 green (`checks/after`).
- Task tests: 12 passed, 29 subtests (`checks/task-tests`).
- Profile floor: 24/60 exact, 31/60 envelope; exact easy/medium/hard 3/20, 9/20, 12/20.
- Semantic smoke: 12/12 lessons identifiable and 48/48 query rotations non-ambiguous.
- Large census: 300 lessons; 1,200/1,200 production placements and 1,200/1,200 rotated placements non-ambiguous; 1,126 unique inputs.

### Parametric prototype

`workspace/parametric/` proposes episode-level quadrant handedness with clockwise canonical default and counterclockwise alternate. Exact Racket replay matches all 8 labels across two retained episodes; every demonstration refutes the opposite setting, queries are setting-sensitive, and public challenges are answer-masked. This remains a proposed prototype, separate from the selected generator.

### Remaining limits

Declared-rival checks are finite and do not prove unique induction against every possible program. The modulo-4 anchor assumes the exported sampling schedule visits the anchored residue; the standard contiguous schedule and all residues modulo 2–8 were measured. The parametric evidence covers two episodes rather than the full seed space.


## Current external prototype work

Review `review-7b9ac74f2385b249` supersedes the earlier pending note without
changing the selected generator or canonical authority. The isolated handedness
prototype now accepts independent positive exact demonstration/query counts
(default `3/1`; retained evidence `3/4`), rejects requests above 64 total pairs,
and samples distinct lawful inputs with a 4,096-attempt bound.

Public export now uses `reviewer_support.public_challenge_bytes` and
`public_challenge_id`: v2 files are `challenge-<visible-content-sha256>.json`,
batch order is stable, duplicate visible payloads are rejected, and hidden
settings, seeds, programs, metadata, and query answers do not affect identity.
The documented `--public-dir` CLI exposes that writer directly. The four original
v1 episode files remain byte-for-byte as archival evidence, including their known
setting-revealing names; they are hash-pinned and excluded from the corrected v2
`episodes/public/` export, while complete v2 episodes remain private.

The v2 retained verifier executes 14/14 labels through the matching Racket
programs for two settings, with three shared demonstrations and four distinct
queries per setting. Every query changes under the rival setting after the
demonstrations identify the episode setting. Evidence: 
`workspace/parametric/evidence/manifest.json`,
`checks/parametric/196a7ec58bbc-handedness-v2.json`, and
`checks/parametric/adversarial-v2.json`. This remains bounded prototype support,
not production selection, variant approval, or an all-seed identifiability proof.

<!-- arcpuzzles-current-audit-assessment:start -->
## Current bounded audit assessment

Return: `review-e1259b2e06dc7ffe:v0001`. Disposition: **resolved**. Evidence basis: `reviewer_reported`.

Audited source SHA-256: `fd5cfa1eb371b00f440aa229c1e759dffbb66a74a10e8dd2b4f1dd8bfcdaa5f0`. At disposition, the audited source differs from the current source; this assessment covers audited bytes only.

### Current decision

Current716d964e83da3769819ffa8e4c51ed38ffd7e375643fd97a4bb574db67b69af1 addsreflectionrival/lessonhookandportablecanonicalhelpers. Ownerfocusedhookcheckrejects exactoldseed33witness (evidence/current-repair/mirror-audit-check.json); newworking/freshportable12tests+29subtests are reviewer-reported. Thisresolves retainedmirror/portabilityfinding onfd5cfa1e only;finiteotherhypothesesnotproved.

### Assessment or prior finding

## 196a7ec58bbc

**Findings-only audit: reproduced lesson ambiguity and blocked task-test portability. No target or shared source changed.** Generator version 2.0.0; source SHA-256 `fd5cfa1eb371b00f440aa229c1e759dffbb66a74a10e8dd2b4f1dd8bfcdaa5f0`; executed canonical rule `24bc23963715`. Raw canonical program SHA-256 is `b8c0009358927f3fbcfb6bf93fa8a19e3b5e80a76efeca70034cff45562abd78`; executed callable SHA-256 is `1d7f81bc5a729909ef45815cf2fa04e42f9a86667484863720aadbfd713ddb6b`.

**A196-1 — Reproduced teaching ambiguity.** Four distinct rotations do not ensure a lesson distinguishes rotated quadrants from reflected quadrants. Official generation with seed 33, easy difficulty, starting sample index 0, three demonstrations and one query accepted indices `[0,1,2,3]` without rejection. Each demonstration has input 2 rows × 2 columns and output 4 rows × 4 columns. Demonstration inputs are `[[8,2],[2,7]]`, `[[9,0],[0,7]]`, and `[[3,1],[1,5]]`; query is `[[0,7],[5,8]]`. All four inputs pass `self_check` and have four distinct rotations. Each demonstration is transpose-symmetric, so the rival that mirrors left/right and then top/bottom fits every demonstration, but disagrees with the Racket query answer in four cells. The production lesson has `lesson_check.status: not_declared`.

For the retained authoring query, input is 2 rows × 2 columns and verified output is 4 rows × 4 columns. The Racket query output is `[[0,7,5,0],[5,8,8,7],[7,8,8,5],[0,5,7,0]]`; the mirror rival predicts `[[0,7,7,0],[5,8,8,5],[5,8,8,5],[0,7,7,0]]`. Supported `arcpuzzles apply --check-generator-domain` independently confirmed all 4/4 labels and domain checks. Of the four query holdouts of these same retained pairs, exactly 1/4 is ambiguous against that rival; these rotations are not independent draws.

Canonical-fit scope is explicit: unconditional mirror tiling fits only 2/4 canonical labeled pairs. A size-conditional rival, mirroring 2×2 inputs and using rotations otherwise, fits all 4/4, across the three train pairs and one test pair. It is a finite declared alternative, not a claim about which hypothesis a model will choose. A bounded Python-label probe of seeds 0–4999, easy difficulty, three demos/one query, found 6/5000 ambiguous candidate lessons, 4990 refuted, and 4 answer-equivalent on all pairs. Only the retained seed-33 lesson was independently materialized and labeled through Racket. Inputs were deduplicated within each lesson; global unique-input count was not measured.

Evidence: `checks/audit/196a7ec58bbc/verified-counterexample.json`, `checks/audit/196a7ec58bbc/seed33-racket-apply.json`, `checks/audit/196a7ec58bbc/seed33-production.jsonl`, and `checks/audit/196a7ec58bbc/reflection-probe.json`. Reusable probes are retained alongside them. Suggested follow-up: declare reflection competitors and make each production lesson include a demonstration that distinguishes reflection from rotation whenever its query needs that distinction; retain the canonical diagonal checker exception and evaluate query rotations.

**A196-2 — Reproduced task-test portability blocker.** Strict combined audit exited 1. Both requested stages terminated, but neither passed: task tests exited 2 at preflight because `tests/test_generator_196a7ec58bbc.py` computes `ROOT` from fixed `parents[1]`, producing the missing `generators/196a7ec58bbc/data/canonical/puzzles.jsonl` path in the collected portable layout. Test counts are null: no test cases ran. The semantic stage exited 2 because no semantic contract is declared, so it did not score its requested lesson population. The task owns the test source; the legacy root test is only a mapped mirror. Suggested follow-up is `reviewer_support.find_root`, `canonical_path`, `canonical_pairs`, and `load_selected_generator`, without changing shared tooling.

Evidence: `checks/audit/196a7ec58bbc/combined/result.json`, `checks/audit/196a7ec58bbc/combined/checks/196a7ec58bbc_audit_summary.json`, and `checks/audit/196a7ec58bbc/combined/checks/196a7ec58bbc_audit_semantic_gate.json`.

The audit did not rerun a full battery, alter the reference rule, or test larger inputs beyond the declared 2×2/3×3 envelope. Correct Racket labels for the reproduced inputs are established; universal identifiability, medium/hard lesson behavior, and task-test assertions remain unverified. Exact commands, working directories, exits, hashes, and a corrected scratch-verifier attempt are retained in `checks/audit/196a7ec58bbc/commands.json`.

The disposition records an explicit decision. It does not imply a fresh execution, universal correctness, closure of other findings, or training admission.

[Retained evidence](counterexamples/review-e1259b2e06dc7ffe-v0001/audit_assets.json), manifest SHA-256 `d9c6f78ca25465d8aec7df3ee374450a2b5f5dc818aa4565621c05ff7764f727`.
<!-- arcpuzzles-current-audit-assessment:end -->

Owner conflict reconciliation: retain the four exact object-source/handedness
programs and add the independently returned marker-to-top-left normalization
as a fifth disjoint rule. No unverified Cartesian combinations are introduced.
The native rule enum has five entries; the adapter also accepts the old setting
dictionaries. All settings share matched marker-bearing, object-rich inputs.
The canonical default and production generator remain byte-identical. Current
owner evidence: `evidence/owner-variant-reconciliation/current.json`.
