# Working notes: 1b54d2fb6f09

## review-31118be85ee0aad5

Prior lead: unresolved audit `review-44f307c1cb52a1c8:v0001` identified a canonical-fitting minimum-length shortcut. I reproduced it against the issued source SHA-256 `f68362ca7830c3a81d60e303441cc6509ba54785f85a2dcdfe6aeda2306e1e9d`: across 600 ordinary draws (200 per band), zero contained a straight red component of length two. The shortcut “recolor endpoints only when a straight red segment has length at least three” fit all five labeled canonical pairs.

Root cause: `_choose_red_components` used minimum length four for its first straight slot and minimum length three for all later slots. The authority applies to every gapless straight red component of length at least two, so this excluded a lawful boundary and left the canonical ambiguity unchallenged.

Repair in version 3.1.0:

- make the first straight slot exactly length two in every ordinary draw;
- retain a second straight slot of length at least four so the red interior remains a visible negative for recolor-all;
- declare `skip_length_two_segments` as the only canonical-fitting shortcut;
- add the rival to lesson competitors, add a length-two semantic witness, and require it in lesson identifiability;
- keep the Racket authority and `RULE_HASH = c2a92b447e5a` unchanged.

Final generator SHA-256: `fca80e3f28617ab4754ea5eafcb20b17b555408b3199040e2faf89837b070f0f`.

Evidence:

- `checks/root-cause/baseline.json`: 0/600 issued-source draws contained length two.
- `checks/after-distribution/report.json`: 600/600 final-source draws contained exactly one length-two segment and refuted every declared canonical shortcut.
- `checks/question/length-two-boundary/`: ordinary generated witness plus supported Racket receipt.
- `checks/task-tests/result.json`: 11/11 focused tests passed.
- `checks/after/result.json`: all 12 battery stages green.
- `checks/lesson-census.json`: 300/300 production lessons and 1,500/1,500 query rotations passed.

Limitations: the measured rival set is finite, the random census does not exhaust all seeds, and masked solve labels remain unavailable. No approval state was changed.
## Current reviewer considerations

Source SHA-256: `fca80e3f28617ab4754ea5eafcb20b17b555408b3199040e2faf89837b070f0f`.

# Decisions for review-31118be85ee0aad5

## Scope and authority

Repair only `repo/generators/1b54d2fb6f09/`; retain the assigned blind solve, review question, and both audit draws. Version moves from 3.0.0 to 3.1.0 because the ordinary support and teaching contract change. The canonical Racket authority and `RULE_HASH = c2a92b447e5a` are unchanged. No canonical data, catalog status, shared source, audit target, or approval state was edited.

The issued-source SHA-256 was `f68362ca7830c3a81d60e303441cc6509ba54785f85a2dcdfe6aeda2306e1e9d`. The final generator SHA-256 is `fca80e3f28617ab4754ea5eafcb20b17b555408b3199040e2faf89837b070f0f`.

## Root cause and repair choice

The prior unresolved audit was used only as a lead and was remeasured. The baseline probe sampled 600 ordinary inputs, 200 per band: none contained a straight red component of length two. `_choose_red_components` requested minimum length four for slot zero and minimum length three thereafter. Consequently, the rival “apply the rule only to segments of length at least three” fit all five labeled canonical pairs and every ordinary generated input.

I chose a minimal support repair:

| Decision | Reason | Rejected alternative |
|---|---|---|
| Make the first straight slot exactly length two | Guarantees a counterexample to the strongest canonical-fitting rival in every ordinary draw. | Merely lowering the random minimum to two could leave many complete lessons without the witness. |
| Make the second straight slot length at least four | Preserves a visible red interior, keeping the recolor-all rival falsifiable in the same example. | Allowing every slot to be length two would repair the boundary but weaken interior teaching. |
| Keep later slots length at least three | Retains length/count diversity without adding unnecessary packing pressure. | Forcing multiple length-two components adds correlation without teaching a new distinction. |
| Declare only `skip_length_two_segments` in `CANONICAL_SHORTCUTS` | It is the only named rival that actually fits every canonical pair. | Keeping all semantic rivals under the canonical-shortcut label would make the declaration false. |
| Add the rival to `LESSON_COMPETITORS`, a semantic witness, and `lesson_identifiable` | Binds the repaired support to exported lesson checks rather than to an informal distribution claim. | A sampler-only patch could regress silently while checks remain green. |
| Leave the Racket rule unchanged | The authority already handles lawful length-two components correctly. | Changing the rule would alter the task instead of repairing generator coverage. |

## Test and evidence policy

Tests were written before the production edit. Against the issued source, the task-local file produced 10 expected failures and one existing pass. After the minimal change it passed 11/11. The tests cover ordinary draws in all bands, exact count overrides, a small explicit boundary witness, truth of the canonical-shortcut declaration, four-example rival coverage, and all five query rotations of generated five-pair windows.

A separate final-source probe iterates the generator's actual `CANONICAL_SHORTCUTS` and `LESSON_COMPETITORS` declarations. Across seeds 0..19 and sample indices 0..9 in each band, 600/600 inputs were validator-clean, 600/600 had exactly one length-two segment, and 600/600 refuted every declared canonical shortcut. This finite sample does not prove all seeds or unknown rivals.

The completed battery reports 12/12 green stages. Its semantic smoke used four demonstrations plus one query, 12 materialized lessons (four per band), and all 60 one-query rotations; all passed. The larger source-bound census used the production sampler with 100 lessons per band, four demonstrations plus one query, and `--rotate-query`: 300/300 production lessons and 1,500/1,500 rotations passed, with 1,500 unique inputs. The random census does not exhaust every seed or cyclic schedule start.

The first before-battery attempt was interrupted by the outer execution window after six green stages; it remains recorded as `running`/incomplete and is not presented as a baseline pass. The direct baseline support probe is the evidence for the repaired defect.

## Solve and audit boundaries

The blind task `02a33ab58da6` was solved before opening repair material; one attempt passed 3/3 visible examples. The post-repair solve was prepared from final generator hash `fca80e3f...`; earlier exposure was declared, reference consultation during the solve was denied, and one attempt passed 4/4 visible examples. Masked labels remain unavailable in both records.

The audits of `c1e45a501ca9` and `70a3e6be3283` are read-only. Both reproduce control-contract defects on their assigned hashes while the retained inputs remain validator-clean and execute correctly under their canonical Racket rules. They are not part of the selected repair.

## Remaining limits

The named rival set is finite. The 600-draw support probe and 300-lesson census are measured samples, not exhaustive proofs over all seeds. The generator continues to guarantee a length-two witness in every ordinary draw, which is deliberate teaching structure but also a distribution correlation. Masked solve correctness and downstream model-learning gains are unknown.
