# Working notes: 4f1ec6a61342

Record design decisions, hypotheses, review findings, and unresolved questions here.
Imported associated notes retain original evidence/timestamps in `evidence/associated_notes.jsonl`.

## Review ccacfd8306e55d7a, October 4, 2026

Original distribution rationale is unknown. The baseline advertised but did not
honor full axis domains; adjacent dividers removed a room, and self_check did
not count actual chambers or enforce a unique target. The review replaces those
paths with finite capacity-aware rectangular partitioning and independent tests.

Only four observable axes remain. Unsupported cosmetic controls now raise
ValueError instead of silently doing nothing. All advertised joint tuples are
constructive, including 7x9 with six rooms and control six. Target seeds are
placed exactly, without clipping. Non-target counts may repeat.

Default sample_index alternates count_witness (even) and core (odd). Core favors
13x15, four rooms, controls 1..3, and count multiset {0,1,2,3}, with newly sampled
cross dividers and seed coordinates. Other sizes, counts and controls retain
support. Count witnesses use controls 4..6 and 2..4 rooms, include a repeated
seed column in the target, and place at least one larger-count distractor.
Additional distractors vary below and above the target so it has no fixed
second-largest rank. All four declared rivals are refuted on every default
count witness. Every consecutive three-example window contains a witness;
each four-pair window has two witnesses, so any one held-out pair leaves one.
This guarantee concerns default draws without rejected inputs. Actual production
acceptance and rotations are separately measured by the public lesson census.
Arbitrary user overrides do not carry this default schedule guarantee.

The initial repair passed all 12 battery stages while an undeclared clamped-rank
rival still made a query ambiguous. Its exact Racket-verified witness is retained
under checks/intermediate-clamped in the return. The final version declares this
rival and supplies a larger-count distractor. This is finite evidence against
declared alternatives, not proof of uniqueness among all possible rules.

The canonical program and examples are unchanged. Exactly two comments were
removed from the selected target_code authority to match canonical/raw_code
bytes; existing execution parity and final authority checks cover this sync.
RULE_HASH remains f73a1c6442ab. Control five intentionally remains five in output.

The manifold remains rectangular rooms and fixed semantic colors; irregular
chambers, target zero, and multiple matching chambers are outside this sampler.
Tests and the independent workspace probe can be rerun without a sibling checkout.
## Current reviewer considerations

Source SHA-256: `439090ba19392e993a0168533970d9da82e6cf6117e505292f907a1a82dabb34`.

# Decisions — 4f1ec6a61342

The immutable assignment is review-ccacfd8306e55d7a. No prior return was used as
a lead: the selected task had only its imported generator and placeholder notes.
Original distribution rationale is unknown. Current canonical pairs and exact
baseline executions ground the changes. Finding R1 covers exact controls and
validation; R2 covers canonical support and teaching; R3 covers authority
synchronization. These IDs match REVIEW.md.

| Choice | Reason and rejected alternative | Evidence / remaining limit |
|---|---|---|
| Preserve canonical Racket semantics | The rule solves all five canonical pairs. Its control-five behavior preserves the gray control cell. Changing the rule to fit old prose would change authority unnecessarily. | Canonical ledger hash remains unchanged. Selected target_code loses exactly two comments to match canonical/raw_code; no semantic change. |
| Four exact observable axes | Height 7..18, width 9..20, chambers 2..6 and target 1..6 are meaningful controls. Retaining inert palette/density aliases would preserve misleading API claims. | Full joint matrix: 12,960 executed cases over three bands, seed17/sample0; no failures. Cosmetic and unknown keys now raise ValueError. |
| Constructive capacity-aware partitions | Original adjacent dividers could erase a room; requests for five/six rooms failed or fell back. A finite partition feasibility calculation reserves enough space before sampling. | No min(count,capacity) truncation or unbounded rejection. Minimum7x9/n6/control6 is exercised. Rectangular rooms remain the manifold. |
| Frequent canonical cross component | All five canonical pairs use four asymmetric cross chambers and counts {0,1,2,3}. Midpoint-only dividers excluded this topology. | Odd default indices favor13x15/n4 and controls1..3; positions and seed cells are newly sampled. Other legal values retain support. Final profile floor18/60, with support in every band. |
| Alternating teaching component | Individual witnesses are insufficient if a lesson can omit them. Even default indices each distinguish all four declared rivals. | Every consecutive3-demo window contains one; every4-pair window has two, so any single holdout leaves one. Production rejections and actual indices are checked separately in the Racket census. |
| Larger-count distractor | The first repair passed the battery but introduced a clamped-rank shortcut. The saved intermediate lesson proves a concrete ambiguity. | The target is not always the largest chamber by seed count. Additional high-count distractors vary its rank, avoiding a fixed second-largest replacement. |
| Repeated target seed column | Occupied-column counting fits every canonical pair. Two target seeds share a column in each even default draw. | The counterexample is pixel-observable and verified against Racket. Some broader core inputs still allow separated seeds. |
| Fixed semantic palette | Gray5 is the wall, red2 is counted, and the control is a numeric value. Arbitrary color permutations would change the task. | Three or four input colors arise naturally. Control5 is intentionally also a wall color. |
| Independent probe and portable tests | Reusing generator component helpers would risk reproducing the same defect in the test oracle. | The probe separately flood-fills cells, reads actual AXES and rival declarations, and hashes its sources. Its initial control-five bug went red before repair and is preserved. |

## Genuine failed iterations retained

1. Baseline battery: four failures, two advisories, six green stages. Focused
   regressions:76 failed/25 passed against original generator b7a242af10bdaf2b3e0683989a3a89628a4eeaa919b85d9bd317f12dc0eb82de.
2. Intermediate v3.0.0:12 stages green and101 tests passed, but the undeclared
   clamped-rank counterexample remained. It was checked through the supported
   Racket apply API before the source changed.
3. Clamped-rank regressions:2 failed/99 passed. A subsequent fixed-second-largest
   rank probe also failed before distractor counts were broadened.
4. The independent probe's control-five oracle test failed before repair.
5. Portable test attempts failed on missing isolated pytest before a correctly
   provisioned interpreter completed them. These are environment failures, not
   generator failures or passing test skips.

## Scope and limitations

The reviewed generator produces one matching rectangular chamber and controls
1..6. Target zero, multiple matches, irregular components and arbitrary semantic
palette changes are outside its declared domain. The default teaching guarantee
does not automatically extend to every user-selected override population.

The four declared rivals are plausible and each fits all five canonical pairs.
Zero ambiguity in the finite census is not a proof against arbitrary new rules.
Difficulty changes default size weighting; every band retains legal joint-axis
support. The exhaustive matrix repeats exact pixel populations across bands
when all four axes are fixed, so 12,960 executions are not claimed as 12,960
globally unique inputs.

The blind solve and post-repair solve are separate records. Query correctness
remains withheld. The post-repair record declares earlier exposure because the
parent reviewer read the rule; its fresh solver receives only visible examples.
No model training, quality uplift, or training admission is claimed.

## Review review-c35808d5ca73a62c, October 24, 2026

This return adds a native parametric family without changing `generator.py` or
canonical authority. The default `mode=direct` returns the exact canonical
Racket program byte-for-byte. The alternative `mode=height_relay` keeps the same
matched chamber inputs but composes two input-dependent selections: the control
first identifies a cue chamber; that chamber's row height then becomes the seed
count used to select a distinct chamber for filling.

The constructive sampler supports independent 2–6 demonstration and 1–4 query
counts. Ordinary qualification uses three demonstrations and four queries. The
fourth query is a substantive 30x30 chamber layout, while the profile rotation
also retains the minimum 7x9 case, horizontal and vertical partitions, 4–6
chambers, varying control counts, cue heights and distractor placements.

A shortcut audit initially found that all relay destinations were the farthest
eligible chamber. A failing regression was retained; the lesson schedule now
uses a sibling, farthest and middle eligible destination across the three visible
demonstrations. The minimum 7x9 lesson also reserves a six-seed distractor above
the canonical control five. Staged tests finish at 123 passing tests. A bounded
64-seed audit checks 128 episodes and nine named finite rivals; none fits all
three demonstrations, all 448 cross-setting input pairs match, and all 256 query
outputs differ. This finite rival list is evidence, not a uniqueness proof.

Native qualification on seeds 0 and 17 re-executes 40 labels through protected
Racket. Each setting is the sole demonstration survivor, both programs answer all
four queries, and the default program hash matches canonical authority. The
source-bound 30x30 causal witness measures cue height 5; a protected-Racket
height+1 counterfactual changes the final output. Saved public projections contain
three labeled demonstrations and four input-only queries, hash only their exact
visible bytes, and pass the packet checker. Negative files correctly reject a
query-answer leak, a wrong public ID and a duplicate input; changing private
settings or receipts does not change public IDs.

The resulting native adapter, promotion contract, source inventory,
qualification and causal witness are reviewer-ready. Owner integration must still
replay qualification and perform fresh native acceptance on the exact live bytes;
no training admission or measured learning benefit is claimed.
