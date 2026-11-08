# Working notes: 6c2353a2cdee

## 2026-10-02 review — assignment `review-e5ff77276ca08f17`

Imported source SHA-256: `5e623a27a3cbf9011119819d67c0ca8b81cae0913472ea5e9011ef95d8075951` (`1.2.1`). Final source SHA-256: `f411a382a0d7248ee69bd02292daf6d78035d303c09ee6b6487f7feba9931a7d` (`2.0.0`). Selected rule hash: `9fc3fd333ca6`; Racket authority unchanged.

### Root cause

The old generator reproduced the outer 7×17 layout but not the canonical panel grammar. All 15 canonical panels are single connected 5–8-cell templates spanning rows 1–3. Across 120 deterministic old-source draws (360 panels), only 12 panels were connected, 359 touched a border, and component count had median 4. The broad marginal distribution gate passed, so this required a task-linked topology probe.

The imported validator/contract also had no rule pin, advertised dead/singleton axes, accepted unknown overrides, accepted weak impostors, emitted code `5` in ordinary data, and supplied no semantic lesson contract. The before battery was 8 green / 1 advisory / 3 failed (`lint`, `defect_lint`, `override`).

### Selected design

- Generate three distinct, connected, rotationally asymmetric templates of 5–8 cells.
- Span rows 1–3; ordinary widths are 2–4, with an occasional width-4 case.
- Easy defaults to 5–6 cells, medium to 5–8, hard to 7–8; exact overrides remain 5–8.
- Use a four-step code schedule over `1`–`4`; retain code `5`/`6` only in the Python authority mirror.
- Retry until output visibly contains `2`, `4`, and `8` and all declared lesson competitors disagree.
- Reject unknown/invalid overrides; observe exact panel-size overrides from a grid.
- Declare strict likeness, seven witnesses, branch witnesses, schedule profiles, and three executable rivals.

### Evidence

`workspace/distribution_before_after.json` uses 40 draws per difficulty band, seed base `7331`, sample indices `0..39`. Final generation is 360/360 connected panels, 16/360 border-touching, and 120/120 draws with all count colors. `workspace/distribution_probe.py` is covered by a task-local regression test; `workspace/generator_before_review.py` preserves the exact imported source for comparison.

The final official aggregate is 12/12 green. Semantic gate: 600/600 strict, 5/5 canonical accepted, 7/7 witnesses, 3/3 rival claims, 12/12 lessons identifiable. Task-local tests: 22 passed. A 600-draw independent stress run found no generation/validation failures.

### Limitations

The morphology envelope is inferred from five canonical inputs. The deterministic schedule may be learnable through sample-index periodicity. Ordinary codes intentionally stop at `1`–`4` because no canonical example establishes `5`/`6` as training-distribution branches. Earlier rule exposure means the retained visible-only solve is not blind.

Imported associated notes remain in `evidence/associated_notes.jsonl`.
## Current reviewer considerations

Source SHA-256: `f411a382a0d7248ee69bd02292daf6d78035d303c09ee6b6487f7feba9931a7d`.

# Decisions for `6c2353a2cdee`

## D1 — Match the canonical panel grammar, not only the global grid shape

**Choice.** Each panel is one asymmetric, 4-connected template with 5–8 cells, spans rows 1–3, and has width 2–4. A width-4 template is scheduled occasionally rather than making every panel fill the frame.

**Rationale.** All 15 canonical panels satisfy that grammar. The imported generator instead scattered independent cells across the full 5×5 panels. The source-bound probe measured only 3.3% connected panels before versus 100% canonical, while the official marginal distribution gate still passed. G1 therefore came from a task-linked topology mismatch, not a cosmetic preference.

**Alternatives rejected.** I rejected (a) preserving independent Bernoulli/scattered cells, because it teaches a visually different decomposition problem; (b) copying the five canonical shapes literally, because that would sacrifice input diversity; and (c) allowing arbitrary connected full-frame blobs, because border contact and row support would remain unlike the retained examples.

**Probe and failure mode.** `workspace/distribution_probe.py` measures components, row support, width, cell count, border contact, code grammar, and count-color visibility for canonical, before, and final sources. The main limitation is small canonical support: five examples cannot prove that every lawful instance must follow this profile.

## D2 — Use codes `1`–`4` in ordinary training and a four-example coverage schedule

**Choice.** Ordinary samples use three distinct codes drawn from a cyclic schedule: `(1,2,3)`, `(4,1,2)`, `(3,4,1)`, `(2,3,4)`. Every four consecutive starts expose all codes and omit each one once.

**Rationale.** The canonical examples use codes `1`–`4`, and a four-demonstration lesson should identify all four rotations rather than leave a branch unsupported by chance. The selected authority’s code-5/code-6 branches are retained in the Python mirror for parity, but they are not ordinary generator outputs because no canonical example establishes them as training-distribution branches.

**Alternatives rejected.** IID code selection could produce lessons that omit a transform. Continuing to emit code `5` would broaden beyond the observed task and confuse a model about the intended code vocabulary. Hard-coding one fixed triple would leave one code permanently absent.

**Probe and failure mode.** Task-local tests check every cyclic four-example start from 0 through 7. The structured schedule is narrower than IID sampling and could make sample-index periodicity learnable; the semantic gate therefore also checks varied seeds/sample indices and all difficulty bands.

## D3 — Make multiplicity and code direction visible in every ordinary draw

**Choice.** Generation retries until the output includes `2`, `4`, and `8`, and until all declared rivals disagree with the authority.

**Rationale.** A lesson that never shows double/triple overlap cannot distinguish the real count map from a binary union. Symmetric templates or ineffective code rows can also make clockwise/counter-clockwise or “ignore codes” rivals accidentally fit. Ordinary draws now make those distinctions visible.

**Alternatives rejected.** Merely declaring witnesses without enforcing them would allow low-frequency teaching. Adding decorative colors would not establish the transform/count semantics. Requiring only aggregate witness frequency would not guarantee complete four-example lessons.

**Probe and failure mode.** The final semantic gate checked 600 draws and 12 complete lessons, not only marginal witness counts. Retrying can bias the shape distribution toward overlap-rich configurations; the retained distribution report makes that bias measurable.

## D4 — Difficulty controls panel size, not the rule

**Choice.** Easy defaults to 5–6 cells per panel, medium/unspecified to 5–8, and hard to 7–8. Exact overrides retain the full 5–8 legal range in all bands.

**Rationale.** This changes visual density while preserving geometry, code semantics, and output mapping. It produces a real difficulty effect without introducing dead “texture” axes.

**Alternatives rejected.** Grid size, separator geometry, palette count, and code vocabulary are rule grammar rather than safe difficulty knobs. The imported singleton axes claimed variability they could not demonstrate.

**Probe and failure mode.** Regression tests compare easy and hard across 12 sample indices. Larger templates may not always be cognitively harder because they create more overlap evidence; difficulty here is a deterministic density curriculum, not a validated human difficulty score.

## D5 — Keep only exact, observable axes and reject unknown overrides

**Choice.** The public axes are `panel0_cells`, `panel1_cells`, and `panel2_cells`, each exact in `5..8`. Unknown keys and invalid values raise `ValueError`; `observe_overrides` recovers the three exact values from a grid.

**Rationale.** These axes change visible data and are invertible. The imported generator exposed singleton or dead axes and silently accepted typos, causing G2 and the baseline override failure.

**Alternatives rejected.** I did not keep compatibility aliases for dead axes because that would continue to advertise nonexistent control. I did not silently ignore unknown values because it makes experiment metadata untrustworthy.

**Probe and failure mode.** The official override matrix is green and task-local tests pin exact endpoints plus unknown-key rejection. Removing old nonfunctional axis names is intentionally breaking for callers that relied on silent no-ops; those callers should fail loudly and update.

## D6 — Add an explicit semantic contract and executable rivals

**Choice.** The generator declares strict canonical likeness, seven witnesses, branch witnesses, three semantic rivals, schedule profiles, and `lesson_identifiable`. The Python `rule_mirror` implements the selected authority for cheap local comparisons.

**Rationale.** The baseline semantic gate could only return advisory/no-contract. G3 required executable claims: what must appear, which plausible wrong rules must be refuted, and whether complete lessons are identifiable.

**Alternatives rejected.** String-only descriptions are not falsifiable. A rival list copied into an external test would drift from the generator’s own declarations. Comparing only individual examples would miss lesson assembly failures.

**Probe and failure mode.** The official semantic gate iterated the declarations and tested 600 draws plus 12 lessons. The rival set is useful but not exhaustive; future reviews can add plausible shortcuts without changing the authority.

## D7 — Do not change the Racket authority

**Choice.** Keep the selected Racket/canonical authority unchanged and pin its current rule hash in the generator.

**Rationale.** Canonical input/output pairs and the Python mirror agree with the authority. The defect was generation/validation/lesson coverage, not rule execution. Changing the rule would have expanded scope and invalidated existing canonical evidence.

**Probe and failure mode.** `rule_smoke`, `racket_lint`, `authority_sync`, canonical mirror tests, and execution parity are green. The authority-sync report notes archival divergence in an old raw-code bank while selected execution is synchronized; this was not modified.

## D8 — Retain a reusable source-bound distribution probe

**Choice.** Add `workspace/distribution_probe.py`, the imported source snapshot `generator_before_review.py`, and the exact JSON report.

**Rationale.** Future agents need a cheap way to detect the same task-linked drift without reconstructing this review. The tool records source hashes, seed policy, denominators, per-band results, and canonical ledger hash.

**Alternatives rejected.** A prose-only observation would be difficult to reproduce. Folding this task-specific logic into a global gate during the repair would be broader and riskier than first retaining a proven local probe.

**Probe and failure mode.** `tests/test_distribution_probe.py` watches the baseline fail the canonical topology expectation and the final source pass it. The probe is task-specific by design; the generalization recommended in Q1/F1 should extract region schemas rather than hard-code this task’s coordinates globally.

## 2026-10-25 native parametric build — assignment `review-61c809e9a3a3127e`

The production generator remains byte-for-byte unchanged at
`f411a382a0d7248ee69bd02292daf6d78035d303c09ee6b6487f7feba9931a7d`.
A native family now exposes episode-fixed `rotation_direction`:

- `clockwise` is the exact canonical Racket program (SHA-256
  `9fc3fd333ca6354e9946bcb87d58b9edf450115a7b3622052fabd962a6e08c09`);
- `counterclockwise` swaps the code-2 and code-4 quarter-turn meanings while
  retaining panel extraction, identity/180-degree branches and overlap encoding.

Inputs are matched across settings and stable under independent 2–6 demo and
1–4 query requests.  The first two demonstrations eliminate the alternate
setting and eight retained finite shortcuts.  Four private queries include a
30×30 fixed-coordinate stress case with dense decoys on all four boundaries;
the authoritative panel/code region remains the source task's upper-left 7×17
grammar rather than padded or rescaled panels.

Sequential dependency: Step A extracts panels/codes and materializes three
input-dependent transformed supports; Step B consumes those supports to count
coverage and render 2/4/8.  A qualification-bound wrong-intermediate replay
uses the swapped quarter-turn interpretation and changes eight final cells.

Retained evidence: 42/42 staged tests; protected self-audit with eight jobs,
130 Racket evaluations and 256 deterministic stress episodes; native
qualification with four jobs/32 labels; 16/16 one-query public projections; and
owner-format causal replay status `owner_replayed`.  Exact-source owner
acceptance and training admission remain separate and were not performed.
