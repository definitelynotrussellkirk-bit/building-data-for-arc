# Bounded allocation-quality proposal

Ticket: `ticket-a42cea8093566f13`  
Seed: `0929ff05eb795686ac76a43365d8d5721759b161f24e37d019b29714eddc0307`  
Sample: `8b6a2892a064`, `022556f7ee2c`, `a178821cc6bf`

The current 10% evaluation focus, all other authoring probabilities, catalog weights, approvals, and training boundaries remain unchanged.

## Observed records

### 8b6a2892a064

Catalogued reviewed-safe/improved record with a broad scene-profile axis and focused tests, but no current review_index. Current notes say a recovered proposal lacks its genuine audit seed, so receipt continuity is weaker than the catalog status alone suggests; no four-query parametric receipt is retained.

- Source: `repo/generators/8b6a2892a064/generator.py` @ `7b70d101c08c1389680591f2d5f203ad54067525ea783199e4e4b8d6e59b4c4b`
- Catalog: sources `['augmented', 'training']`, mix weight `1.0`, safety `reviewed_safe`
- Contract: `1` axis, `3` demonstrations (fallback assumption; source declares no `EXAMPLES_NEEDED`), hooks `['generate', 'observe_overrides', 'rule_mirror', 'self_check']`
- Bounded generation: `7/7` distinct inputs; four prospective queries `4/4` distinct; no fresh Racket-label claim

### 022556f7ee2c

Unverified bank record with three unresolved/needs-triage source-bound audits reproducing the same three-demo sequential-ray teaching shortcut. Three advertised axes and distinct default draws do not compensate for a known lesson ambiguity; prioritize repair before additional volume.

- Source: `repo/generators/022556f7ee2c/generator.py` @ `96b3765a7272974851f1fa8b9fdc36a29a153e37d96ea79963d82503e3337c00`
- Catalog: sources `['bank:0e3c36a9dbcc']`, mix weight `1.0`, safety `unverified`
- Contract: `3` axes, `3` demonstrations, hooks `['generate', 'self_check']`
- Bounded generation: `7/7` distinct inputs; four prospective queries `4/4` distinct; no fresh Racket-label claim

### a178821cc6bf

Independently checked accepted repair with five exact axes, rule mirror, override observation, a lesson-identifiability hook, retained shortcut counterexample, and focused tests. It is the strongest sampled candidate for a bounded four-query Racket-labelled conversion, but no such receipt is retained.

- Source: `repo/generators/a178821cc6bf/generator.py` @ `27b24a2de22bc10ad14f247234c6bfdd2b83d94c2e1013f43ae084141cf32f68`
- Catalog: sources `['training']`, mix weight `1.0`, safety `reviewed_safe`
- Contract: `5` axes, `2` demonstrations, hooks `['generate', 'lesson_identifiable', 'observe_overrides', 'rule_mirror', 'self_check', 'strict_canonical_like']`
- Bounded generation: `6/6` distinct inputs; four prospective queries `4/4` distinct; no fresh Racket-label claim

## Alternative allocation experiment

Preserve every draw probability, approval, and training boundary, but add a bounded post-draw follow-up queue: among each three already-drawn records, spend at most one extra slot on the highest source-bound value class—unresolved lesson defect first, then independently reviewed family lacking four-query Racket receipts, then receipt-continuity repair, then new volume.

**Experiment.** For four consecutive 3-assignment batches, permit one <=20-minute evidence-gap follow-up. Require exact source binding, retained Racket labels for four distinct queries when supported, demonstration-only competitor checks, and visible-payload deduplication.

**Success rule.** Adopt the follow-up queue only if at least 2 of 4 interventions produce a source-bound, competitor-checked receipt with four distinct Racket-labelled queries (or a documented hard support limit), zero silent duplicates, and median measured follow-up time <=20 minutes.

**Stop rule.** Stop after four interventions, or earlier if the first two both exceed 20 minutes, cannot obtain an independent authority label, or leave a query-changing competitor unresolved.

## Coverage limits

- The sample is three uniform manifest records, not a stratified estimate of the 162-target normal pool or approved dataset mixture.
- No sampled record is labelled ARC-GEN or RE-ARC; no source-family quality or volume claim about either corpus follows.
- The dynamic check used Python generation/self_check only; it did not create fresh Racket labels or prove lesson identifiability.
- Four distinct generated inputs are not equivalent to four distinct Racket-labelled, demonstration-identifiable queries.
- Catalog primitive lists are metadata, not measured executed grammar coverage.
- Catalog mix_weight 1.0 does not imply authoring priority, approval, safety, or training admission.
- Existing reviewer-reported findings remain source-bound and were not re-executed by this allocation probe.
