# Current notes: 520fe6e64fb6, v3.1.1

## Intended rule and authority

The original family is training `fc10701f`. Find the global bounding boxes of
all original 9 cells and all original 7 cells. Recolor 9 to 7 and original 7 to
background 6. Equal minimum columns select the vertical branch; every other
layout selects the horizontal branch, including off-alignment. A zero anywhere
on a between row/column triggers painting original background-6 cells to 2
within the orthogonal span of the **9** bounding box. Preserve zeros and other
colors. Connected components and equal filled rectangles are not rule requirements.

Canonical execution is unchanged: `RULE_HASH = 82e4ce2077ce`. Only the two bound
base-solution `target_code` fields were synchronized to the exact canonical
text. Archival `raw_code` and the canonical ledger remain byte-identical to the
packet baseline. The separate threshold prototype does not replace this rule.

## Current input and lesson choices

The 16 exact `scene_profile` controls remain available: four literal public
inputs and twelve general families. Seed must be an integer (not bool or a
coerced float/string); sample index must also be nonnegative. Difficulty and
explicit profile values are validated before either construction branch.

Default production alternates an irregular teaching anchor with a weighted
payload draw. Payload positions weight each public input twice and each general
family once, retaining approximately 20% literal public support over the full
stream. This is a deliberate curriculum restriction, not an exhaustive sampler
of every lawful grid. General dimensions remain band-dependent; public examples
retain their original sizes in every band. Fixed colors express rule roles and
are not interchangeable palette labels.

Anchors use unequal L shapes: 9 has a 2x3 bounding box and four cells; 7 has a
2x2 bounding box and three cells. Trigger zeros lie outside the 9 span. Each
anchor therefore refutes all four declared lesson rivals: equal filled
rectangles only, equal bounding-box dimensions/area only, the 7 object's span,
and span-local zero triggers. Only the first three fit all eight labeled
canonical occurrences (four unique pairs) and belong in `CANONICAL_SHORTCUTS`.

The lesson contract is three demonstrations and one query, including every
single-pair holdout of the four accepted pairs. Consecutive scheduled anchors
alternate 9-above-7 and 9-below-7 using vertical reflection. They are necessarily
distinct; a payload equal to an anchor is itself a refuter. Because production
deduplication is per episode, four accepted pairs retain at least two refuters
under successful construction/evaluation. Any one held-out query leaves a
refuter among its demonstrations. The random layout and payload profile are
not declared a periodic schedule. Explicit overrides can suppress the teaching
mix; they are authoring controls, not an automatic lesson guarantee.

## Reversal and regression evidence

The first repair, v3.1.0, used two randomly varied anchors without a structural
distinction. Its 12-stage battery and 300-lesson sample passed, but independent
review found easy seed 4484, start 1: anchor 4 duplicated anchor 2, accepted
indices became [1,2,3,5], and holding out index 2 was ambiguous. v3.1.1 adds the
opposite-order invariant, rather than relying on a new random seed/version.
`test_review_contract_520fe6e64fb6.py` covers both this accepted-pair regression
and the structural distinction across bands, seeds and phases. Exact failed
and repaired Racket evidence is retained in this review's
`checks/code-review/accepted-holdout-{finding,fixed}.json`.

`workspace/probe_shortcuts.py` runs the supported `arcpuzzles apply` command,
checks the actual declared shortcuts on every canonical occurrence, and retains
a generated counterexample with all rival outputs. The return's
`checks/shortcuts-final/` holds its final execution evidence; the small witness
is also retained in `counterexamples/review-3d5d6e194d722e1f/`.

## Parametric prototype and limits

`workspace/parametric/threshold.py` proposes episode-fixed `min_zeros` values
1, 2 or 3. Value 1 emits the exact canonical Racket source. Other values change
only the whole-line zero-count trigger; object roles, spans, branch selection
and recoloring remain fixed. Its README documents runnable commands, public
challenges, private Racket labels, rival checks and an intentionally ambiguous
negative control. This is proposed authoring work, not a production API or
approval for variants.

The generator intentionally requires at least one painted connector; this is a
teaching-domain restriction, not a statement that the reference cannot execute
no-op scenes. Named-rival checks and finite censuses do not establish universal
rule identifiability. Query holdout rotation does not mean spatial rotation
equivariance. Approval and training admission are maintainer decisions.

The retained prior audit `review-ee4db350396f0ec7:v0001` identified the missing
semantic contract and active-authority text mismatch on the original source.
This repair addresses those mechanisms with new evidence; its immutable
`evidence/review_index.json` record remains `needs_triage` for maintainer review.
Original associated notes remain in `evidence/associated_notes.jsonl`.

<!-- arcpuzzles-current-audit-assessment:start -->
## Current bounded audit assessment

Return: `review-ee4db350396f0ec7:v0001`. Disposition: **resolved**. Evidence basis: `reviewer_reported`.

Audited source SHA-256: `0977cdb9cea05fd63942e5989b4e6413c69b76799674f63788a3315ae295af55`. At disposition, the audited source differs from the current source; this assessment covers audited bytes only.

### Current decision

Explicitly resolve missing executable semantic contract and exact authority-text drift on55208e87 v3.1.1. Four real rival witnesses, duplicate-safe structurally distinct anchors and exact selected target text synchronization against unchanged canonical Racket (tokens/otherJSON independently checked). Reviewer28tests+744subtests portable/fresh,12/12battery,300lessons/1200holdouts unambiguous. Intermediate seed4484 failure retained; finite-rival/default schedule only.

### Assessment or prior finding

## 520fe6e64fb6

**Reproduced actionable findings; target left unchanged.** Source hash `0977cdb9cea05fd63942e5989b4e6413c69b76799674f63788a3315ae295af55`, rule hash `82e4ce2077ce`.

1. The full public battery fails semantic gate because no `strict_canonical_like`, `SEMANTIC_WITNESSES`, or `lesson_identifiable` contract is declared. This is not merely theoretical: the rival “apply connectors only when both 9/7 objects are equal-size filled rectangles; otherwise only recolor/erase the objects” fits all **8/8 canonical occurrences**. The generator does emit a valid refuter (`scene_profile=irregular_markers`, seed 1703, sample 2303); its Racket output paints three connector cells that the rival leaves background. Exact input/output/rival and provenance: `checks/audit/520fe6e64fb6/counterexample.json`; Racket receipt: `racket_irregular.json`. The distribution has useful evidence, but the missing contract means the lesson gate cannot verify or schedule it.
2. Authority sync also fails: active canonical and selected `target_code` texts form two exact groups, although whitespace-normalized text and execution parity agree. See `checks/audit/520fe6e64fb6/battery/checks/520fe6e64fb6_after_authority_sync.log`.

Battery result: 10 stages green, `semantic_gate` and `authority_sync` failed; summary at `checks/audit/520fe6e64fb6/battery/checks/520fe6e64fb6_after_battery_summary.json`. Suggested repair is to declare the rectangular-only rival/witness and exact-sync active Racket text, not to change behavior.

The disposition records an explicit decision. It does not imply a fresh execution, universal correctness, closure of other findings, or training admission.

[Retained evidence](counterexamples/review-ee4db350396f0ec7-v0001/audit_assets.json), manifest SHA-256 `6d87e4e868bd0c1ab58825318af89243c142c4668746849cecf6706a0826b11d`.
<!-- arcpuzzles-current-audit-assessment:end -->
## Current reviewer considerations

Source SHA-256: `55208e87beb462887f5ef092e800ec95ec95dcaf2ded80b321012207424ccdf0`.

# Decisions: 520fe6e64fb6

## Scope, authority, and lesson contract

This return repairs the selected canonical generator at version **3.1.1**, SHA-256 `55208e87beb462887f5ef092e800ec95ec95dcaf2ded80b321012207424ccdf0`. The selected Racket rule and `RULE_HASH = 82e4ce2077ce` are unchanged. The threshold extension described below remains a **proposed task-local prototype**; accepting the repair does not approve alternative rules or training admission.

The intended lesson contains **three demonstrations and one query**. Production uses the first three accepted pairs as demonstrations and the fourth as query, preserving generation order after duplicate filtering. Review also holds out each of the four accepted pairs in turn, keeping the remaining pairs in their relative order. These are pair holdouts, not spatial rotations. The identifiable-lesson claim is limited to the four declared executable rivals and the stated assembly policy.

## M1/M4: Preserve the rule; make the public contract exact

The rule uses fixed color roles: original 9 becomes 7, original 7 becomes background 6, and triggered connector cells become 2. Global marker bounds determine the interval and the 9-marker span. Equal minimum columns select the vertical branch; all other arrangements use the horizontal branch. A zero anywhere on a scanned row or column can trigger painting, but only original background cells inside the 9-span change. Restricting these semantics to equal rectangles or locally visible zeros would alter the authority.

Two active `target_code` strings, in `shared/data/base/solutions/training/fc10701f__520fe6e64fb6.json` and `shared/data/base/solutions/augmented/fc10701f__b1e2b0d3c0f8.json`, now exactly match the selected canonical program. Their `raw_code` fields and the canonical ledger remain unchanged. This removes textual authority drift without claiming a semantic Racket repair. Exact identity and the retained archives' whitespace-normalized equivalence are checked in [the contract tests](repo/generators/520fe6e64fb6/tests/test_review_contract_520fe6e64fb6.py).

Controls now reject lossy or misleading values: seeds must be actual integers; sample indices must be nonnegative actual integers; booleans, floats, and strings are not coerced. Unknown difficulty values are rejected before even a literal public profile can return. `None` still selects the documented default difficulty, but an explicitly supplied `scene_profile=None` is invalid. Unknown overrides remain errors. These choices make invalid requests observable instead of silently changing the requested experiment.

## M2: Distribution choices and their costs

The four literal public profiles retain the complete linked geometry and labels. Twelve general profiles preserve useful variation: both axes and marker orders, outside-span triggers, unequal and irregular markers, multiple components, horizontal off-alignment, and boundaries. The strict canonical-like predicate remains a separate description of the equal-filled-block manifold; it does not exclude lawful broader inputs from the main validator. The original author's rationale for the earlier frequencies, shapes, and validation choices is unknown. The rationale here is this review's, grounded in the selected rule and retained counterexamples.

The irregular teaching profile uses unequal L-shaped markers: the 9 marker has a 2-by-3 bounding box and four occupied cells; the 7 marker has a 2-by-2 bounding box and three occupied cells. Trigger zeros lie outside the 9-span, leaving the full connector span paintable. This combines four useful distinctions in a small scene:

| Declared rival | Evidence supplied by the irregular scene |
| --- | --- |
| `equal_filled_rectangles_only` | The markers are not filled rectangles. |
| `equal_bbox_and_area_only` | Both bounding-box dimensions and occupied areas differ. |
| `seven_span` | The required connector extends beyond the narrower 7-span. |
| `span_local_zeros` | An outside-span zero still triggers connector painting. |

The first three are canonical-consistent shortcuts. `span_local_zeros` already fails canonical evidence, so it is retained as a semantic rival without being mislabeled a canonical shortcut. The [contract tests](repo/generators/520fe6e64fb6/tests/test_review_contract_520fe6e64fb6.py) distinguish these categories and check the irregular witness against all four.

Default requested sample positions alternate an irregular anchor and a varied payload. Payload selection uses each public profile twice and each general profile once: eight public entries among twenty. Thus literal canonical draws have 40% probability at payload positions and approximately 20% across the unfiltered requested stream. This is a design probability, not a promised accepted-episode frequency: duplicate rejection can change that frequency. The weighting retains visible canonical material while reserving half the requested positions for informative anchors. It avoids making every scene irregular or letting sparse witnesses depend entirely on chance.

## M3: Reversal — raw alternation was insufficient

Version 3.1.0 passed its 12-stage battery and a 300-lesson census. Independent adversarial search nevertheless found a real accepted-lesson defect at **seed 4484, easy, requested start 1**. Sample 4 exactly duplicated anchor 2, so the production duplicate policy accepted `[1, 2, 3, 5]`. Only one retained pair refuted three canonical shortcuts. Holding out that anchor left demonstrations compatible with those rivals, although the production final-query check passed. Exact inputs, protected Racket labels, rejection history, and all holdouts are retained in [the finding](checks/code-review/accepted-holdout-finding.json).

The repair was therefore reopened. [The failing regression log](checks/rotation-regression/red.log) preserves both the actual duplicate case and the failure of a structural distinctness requirement. A version bump or another seed could have concealed the instance without repairing the reason it occurred.

Version 3.1.1 alternates the irregular scene's vertical marker order with `(sample_index // 2) % 2`. Consecutive scheduled anchors now have opposite orders and cannot be equal inputs. Reflection preserves the relevant bounds, outside-span trigger, and all four refutations. Under per-episode exact-pair duplicate filtering, a payload equal to an anchor is itself a refuter already present; its presence does not remove the teaching evidence. At most two non-refuting payloads can be accepted before two refuters, assuming generated inputs execute successfully. Consequently, holding out one pair leaves at least one refuter for each declared rival.

For the original failing seed, [the fixed protected-Racket evidence](checks/code-review/accepted-holdout-fixed.json) accepts `[1, 2, 3, 4]` with no duplicate rejection. Disagreement counts are two for each of the first three rivals and three for `span_local_zeros`; all four holdouts have no ambiguity reasons. The same receipt records six adjacent-anchor checks across the three difficulty bands and eight unique Racket-labeled inputs overall. This is a structural argument plus a bounded execution check, not a proof about undeclared rivals or arbitrary runtime failures.

## Alternatives rejected and limits retained

Increasing only random census size was insufficient: a finite clean census had already missed the accepted-stream failure. Merely testing four raw consecutive draws was also insufficient because those draws need not be the exported pairs. Removing duplicate rejection would change shared lesson assembly, so the repair instead makes the local schedule survive it. Restricting the generator to canonical rectangles would preserve the demonstrated shortcut. Supplying only irregular scenes would unnecessarily remove canonical and broader geometric coverage. Increasing demonstration count would change the intended three-demonstration teaching budget before addressing the actual defect.

Explicit profile overrides remain diagnostic controls, not a promise that every forced profile yields a teachable lesson. A public-only demonstration set followed by an irregular query is deliberately rejected as ambiguous. Fixed color roles are preserved; arbitrary palette swaps or spatial rotations are not justified by this branch rule. The role schedule does not assert that all scene layouts repeat with a two-position period.

The [final battery summary](checks/after-final/checks/520fe6e64fb6_after_battery_summary.json) records 12/12 passing stages. The [completed final census](checks/lesson-census-final-retry.summary.json), with its [compressed full report](checks/lesson-census-final-retry.json.gz), records 300/300 production lessons, 100 per difficulty band, and 1,200/1,200 pair holdouts with zero ambiguities or errors. It contains 976 pooled unique inputs. An [earlier final-source attempt](checks/lesson-census-final.summary.json) stopped after 166 lessons with `ENOSPC`; that incomplete infrastructure run is retained, and the successful retry used disk-backed temporary storage. Task-test command totals and final handoff checks are consolidated in `RESULTS.json`. A finite rival check establishes only that the named rivals cannot fit the retained demonstrations and disagree on the query.

## P1: Proposed threshold extension

The separate [threshold prototype](repo/generators/520fe6e64fb6/workspace/parametric/README.md) varies `min_zeros` over integers 1, 2, and 3. One setting is chosen for an entire three-demonstration/one-query episode. It changes only how many original zeros on the whole between-line trigger painting; object roles, branch selection, bounds, span, and preservation rules remain fixed. The default program returns the exact canonical source bytes. Public challenges omit the parameter, program, and query answer.

Teaching inputs deliberately contain informative lines with zero counts 0, 1, 2, and 3. This narrower sampler makes the three settings distinguishable; it is not a new canonical-domain restriction. The [final receipt](checks/parametric/threshold-s17-final/receipt.json) and [validation](checks/parametric/validation-final.json) record 56/56 default-parity checks over 40 unique inputs, including eight canonical label occurrences and 48 selected-generator cases. Three proposed episodes supply twelve pair holdouts and twenty-four executed rival comparisons, with no ambiguous accepted holdout. An intentionally uninformative negative control remains ambiguous against two rivals and is excluded from accepted episodes. These results support a reviewable proposal, not a production parametric API or universal identifiability claim.
