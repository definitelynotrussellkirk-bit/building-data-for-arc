## F1: Trial source-bound repair quotas before increasing source volume

**Proposal only; no draw policy, approval, or training admission changed.** The reproducible evidence is in checks/allocation/audit.json, with exact source and evidence SHA-256 values. Reproduce from the outer packet directory with:

    .venv-review/bin/python WORK/checks/allocation/audit.py --work-root WORK

### Sample and actual allocation

Seed e00421814a7b8e18266cc1ee1b4f12e0f565cfa4dce7ed5b870534a92524b974, using random.Random(int(seed,16)).sample(sorted(manifest["generators"]),3), selected **8a6282b87245, 531e65dffc0a, 9d6ff77830f1** from 3,941 IDs. None is in this packet's main authoring target pool.

The normal pool contains 252 approved original families needing parameters; tiers of 555 originals needing repair/parameters and 1,767 other unapproved generators are deferred. The 10% public-evaluation focus draws one of 120 anchors, but only one anchor maps to two direct related generators. The other 119 retain a normal target for an inspired extension. Nominally 99.9167% of repair targets therefore remain in the 252-entry normal pool, while 0.08333% go to the two direct related generators. The authoring focus itself remains 10%.

Catalog mix_weight is a separate dataset setting: 3,925 entries have weight 1 and 16 have weight 0. The dataset consumer applies approval and other filters before weighted attempts; failures and deduplication alter accepted frequencies. All three sampled entries have weight 1, but only 531e65dffc0a is approved in the pinned packet. Positive weight does not establish eligibility or training admission. This audit inspected the actual consumers in repo/src/arcpuzzles/datasets.py and catalog.py, as well as review_full_draw.py.

### Concrete quality and cost evidence

| Sample | Current source and retained evidence | Allocation implication |
|---|---|---|
| 8a6282b87245, source 8576b8c1..., public-training/augmented origin | Current generator.py prohibits overlapping object column spans. Its source-bound reproduction under counterexamples/review-8e2f7f4db37de5d2-v0002/retained/checks/audit/8a6282b87245/ records 0/60 collision scenes and 60/60 matches to independent edge snapping. All 60 saved inputs are distinct. A lawful separating witness differs in 16 cells. Its combined audit failed with no task tests and no semantic contract; lint and grammar stages are pending. | More default volume cannot teach collision-aware packing. The retained witness makes this an actionable repair candidate. Diagnosis is already partly done, but repair time and final teaching success remain unknown. |
| 531e65dffc0a, source 704565e2..., internal bank origin | Current v2.1.0 alternates teaching and broader scenes, checks 6 geometric plus 12 code-mapping rival entries, bounds teaching construction at 256 attempts, and honors exact input controls. Notes report 104 task tests, 53,910 override draws and 1,200 unique production inputs. They also preserve an intermediate failure of 37/183 linear windows and 159/732 rotations. These counts are retained reviewer reports, not new runs. The inspected workspace/distribution_before_after.json is v2.0.0 and is excluded as evidence for v2.1.0. | Stronger teaching support required multiple repair iterations and substantial validation. The grammar is still one small monochrome prototype; exact overrides bypass teaching. Single-query rotations establish neither a four-query export nor arbitrary rule-parameter coverage. |
| 9d6ff77830f1, source af7185e2..., internal bank origin | Current generator.py defaults and advertises k=1..3, while self_check rejects no-marker grids. Its current-source audit records a missing canonical k=0 branch. Shapes are height-5 rectangles with isolated single-cell holes, and width depends on hole count. This audit confirmed source restrictions; the canonical/Racket result remains retained reviewer-reported. | A known branch repair is more targeted than adding samples that all omit it. Width/hole-topology confounding is a static coverage concern requiring a rival test before it is called a reproduced shortcut. No fresh lint, rejection-rate, four-query or rule-parameter result is available. |

Exact paths and complete source hashes are indexed in audit.json. The unresolved 531e65dffc0a override audit is explicitly bound to superseded source and is not asserted as a current defect. Its old audit status has not been silently resolved. Missing or pending lint/grammar evidence is not a pass.

For 531e65dffc0a, independent overlapping windows used 576 candidate grids but only 241 globally distinct grids, according to retained notes. That count is distinct from the reported 1,200 unique production inputs. Reusing labels across windows can reduce Racket cost, but overlapping windows cannot be counted as independent data. No elapsed-time measurements support a cross-family repair-cost comparison. The 8a audit's semantic stage took two seconds in its retained receipt; that is not its total review or Racket cost.

No sampled metadata identifies an ARC-GEN or RE-ARC lineage, so this audit makes no quality claim about those sources. Both an original-related family and internally authored bank families exhibit coverage concerns. Provenance alone does not establish quality.

### Concrete alternative and estimated quality per cost

Test a **70/20/10 split within normal authoring**:

- 70% approved original families needing meaningful rule-parameter work.
- 20% original families with current-source, actionable repair evidence.
- 10% other source families with current-source, actionable repair evidence.

Preserve the independent 10% public-evaluation authoring focus. Select within each bucket using immutable source hashes, recorded witnesses and a rotation across reasoning categories; exclude superseded or unsupported leads. This retains most parameter work while reserving some effort for known omissions.

For illustration only, assume respective probabilities of a qualified improvement of 0.65/0.60/0.50, review times of 60/45/30 minutes, and Racket times of 10/8/5 minutes. The current allocation yields 0.65 qualified improvements per reviewer hour. The proposal yields 0.625 improvements in 54 review minutes, or 0.694/hour (**6.8% higher**), with 9.1 estimated Racket minutes per assignment. These are planning assumptions, not estimates fitted from three tasks or empirical claims about a model.

The conclusion is sensitive to repair cost: if all three buckets require 60 reviewer minutes, the proposal yields 0.625/hour, **3.85% below** the baseline. Under the listed costs and other-repair success probability 0.50, original-repair success must exceed 0.40 to improve yield. Existing evidence supports a bounded test, not immediate adoption.

A qualified improvement must add a previously missing reasoning distinction or meaningful rule setting and retain source-bound canonical/domain checks, distinct inputs, Racket labels for four independent queries, and finite-rival identifiability of every query from its demonstrations alone. Record actual demo count, rejected draws, source/rule hashes, and separate production/rotation policies. Input-axis variety, a palette change or a provenance label alone does not qualify.

### Bounded stopping test

Use 20 future scheduled reviews: 10 current-policy and 10 alternative, with alternative quotas 7/2/1, assigned before inspection. Preserve the authoring-focus draws and immutable assignments. Cap each target at 90 reviewer minutes and 15 Racket machine minutes; cap the whole pilot at 30 reviewer hours and five Racket machine hours.

Check 12 unique default lessons per difficulty band, each with four distinct Racket-labelled queries. Meaningful rule prototypes should cover two settings within the same budget. Record per-query finite-rival checks, sample rejections, deduplication and canonical-domain failures. Check schedule residues/rotations when claimed. Missing or timed-out evidence is incomplete, never a pass.

Stop an individual target at either cap. Pause an arm after two newly introduced canonical-domain regressions or two omitted known-branch counterexamples, retaining every failure. Stop the pilot at the assignment or resource cap. Recommend only a limited follow-up if the alternative yields at least 10% more qualified improvements per review hour without increased Racket cost per improvement or weaker quality checks. Otherwise retain the current policy or report inconclusive. This small pilot makes no population-significance, current-model-performance or human-difficulty claim.

**Shared change most directly suggested by this audit:** add a source-bound allocation receipt joining review_full_draw.py tier/focus probabilities with catalog.py eligibility, unresolved current-source findings, four-query/parameter evidence, validation time and deduplication yield. Display authoring allocation and dataset weights separately. Do not rank by source volume, approval label or a stale successful report alone.
