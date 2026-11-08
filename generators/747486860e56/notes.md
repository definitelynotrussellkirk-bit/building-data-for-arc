# Working notes: 747486860e56

## Current assignment update — review-e119992824f89f40

Version `4.1.0`; final generator SHA-256 `008f30c17748241bfc1bc3678dda6f34faba375edea6cc20a447a3823a9aa8ad`. The intended rule remains unchanged: preserve the uniquely largest multicolor eight-connected nonzero object, count every other nonzero cell, choose their plurality with row-major tie breaking, orient from the unique residual corner, erase residuals, and paint a triangle of leg `K-1` last. Canonical Racket rule hash `0ab2a183017a` and source SHA-256 `a58ea15310948d7982ff568d08859b9515f2dfd3087a3b892a3558aed877fedf` remain authoritative.

This assignment reversed one inherited request-handling choice: malformed scalar controls had been allowed to flow into the sampler. `_validate_request` now rejects non-integer or boolean seeds, negative/non-integer sample indices, and difficulties outside `None|easy|medium|hard`; both `generate` and `schedule_profile` use the same check. Valid requests retain the prior byte-for-byte sampling path, so the version and canonical rule did not change.

The two assignment-selected `racket_target.target_code` fields are now exact canonical-source copies. The supported sync tool correctly refused an automatic apply because the legacy strings were different programs textually; a bounded comparison over 586 lawful inputs and 1,758 live Racket evaluations found no output mismatch before replacement. Their archival `raw_code` values and every non-selected field remain unchanged.

A task-local proposed parameter prototype lives under `workspace/parametric/`: `residual_minus_one` is the canonical `K-1` default and `residual_count` uses leg `K`. Both settings have live Racket-backed episodes whose demonstrations distinguish the setting. The alternative is not connected to production, `AXES`, authority, or approval, and requires `K <= min(height,width)`.

Final evidence on the current source is 12/12 green in the schedule-receipt-bound battery, 135 selected task tests passed with one inherited-receipt skip, 300/300 production lessons and 2,100/2,100 rotations without a declared-rival ambiguity or scoring error, plus all 9 seed-zero schedule starts and 63 rotations. These are finite checks against declared rivals, not a proof against every possible hypothesis or all seeds. The strongest retained canonical-fitting shortcut is corner-vote exclusion; the current exact witness and 113/600 gate frequency show the generator still refutes it. No selected-generator issue remains open; the separate audit findings concern `48fee61713bb` and `8387b52c80df` and did not modify those tasks.

## Inherited review record — review-4c48d7aaa24ba47f

## Inherited rule and authority account

Version `4.1.0`, reviewed under `review-4c48d7aaa24ba47f`. The selected canonical Racket program is unchanged: normalized rule hash `0ab2a183017a`, exact program SHA-256 `a58ea15310948d7982ff568d08859b9515f2dfd3087a3b892a3558aed877fedf`. Only the selected `racket_target.target_code` strings in the assignment-listed training and augmented solution files were synchronized to those existing canonical bytes. Archival `raw_code`, all other fields, and the complete canonical ledger were preserved.

The main object is the largest **multicolor, eight-connected** nonzero component. All nonzero cells outside it count and vote, even if they touch each other or reuse a main-object color. For K residual cells, the triangle's leg is K−1. Choose the residual plurality, breaking tied frequencies by first row-major occurrence among tied colors. The residual corner determines orientation. Erase the residuals, preserve the main object with its original colors, and paint the triangle last, including over the main object.

Canonical evidence has ten labeled pair occurrences but only five unique pairs. It includes diagonal main connectivity, touching residual cells, non-majority pluralities, a frequency tie, and main-color reuse. The old descriptions “isolated dots,” “one color,” and “majority” were too restrictive; the old final phrase “sides n” also conflicted with its own K−1 definition. The previous author's rationale is unknown: the imported working notes were empty and the associated-notes file was empty.

## Generated envelope and controls

Inputs have rectangular integer grids, zero background, colors 0–9, dimensions 6–24, a uniquely largest component with at least four cells, 3–8 residual cells, and exactly one residual corner. The triangle fits without clipping. These are declared generation limits, not claims about every input the Racket program can execute. Equal-largest components, absent/multiple residual corners, empty residuals, and clipping are excluded.

Exact controls are `grid_h`, `grid_w`, `corner` (`tl`, `tr`, `bl`, `br`), and `n_markers`. Their observer measures the actual grid. `None` means omission under the shared `gen_ctx` convention. Unknown or obsolete keys are rejected, including the previously inert palette, anchor, position, texture, and isolation aliases. A dimension of six cannot accommodate eight residual cells' leg-seven triangle; that joint setting is explicitly incompatible. Validation inspects grid facts independently of metadata.

Fresh connected shapes and broad dimensions are mixed with the observed canonical size/palette profiles in every band. “Strict canonical like” denotes this stated lawful envelope, including multicolor and overlap extensions justified by the unchanged rule; it does not mean every draw copies a canonical picture. `MIN_STRICT_FRAC = 1.0` is checked against this domain.

## Curriculum and reversals

Use six demonstrations and the standard same-seed production assembler. The period-three schedule is `corner_vote`, `tie_low`, `tie_high`. Core profiles include residual counts 3, 5, 6, and 7; odd counts carry a strict majority, while six-cell cores carry a unique 2/6 plurality. Default tie profiles use 2/2/1/1 counts and put singleton losing colors at the first residual position and the corner. Thus the first residual cell itself does not identify the winner; the earliest occurrence **among tied colors** does.

An episode independently selects mono/multicolor main objects and critical/neutral corner roles from its seed. In critical contexts, removing the corner vote changes the winner in core examples; in neutral contexts the corner is a losing color. Tied scenes teach numeric-order independence, residual contact, and paint-overlap semantics. Monochrome-main or corner-exclusion rivals may agree with every label in the corresponding answer-equivalent episode. A rival that would change a query must still be refuted by the remaining demonstrations.

The intermediate `4.0.0` design paired monochrome cores with a winning corner and multicolor tie scenes with a winning first residual. A newly tested rival, `monochrome_corner_else_first`, matched every label in its retained 300-lesson census despite fitting only 2/10 canonical pair occurrences. The current independent context bits and singleton-loser tie positions remove that measured shortcut. Rescoring the old labels still gives a query-ambiguity pass; `workspace/audit_rival_coverage.py` exposes the distinct distribution coverage gap. The final census refutes that rival in all 300 lessons and all 2,100 holdouts.

Independent boundary review also found four `4.0.0` cases in which residual cells became the selected largest component and silently changed the requested residual count. The construction now accepts only when the observed main equals the intended main and the actual residual count equals the request. The exact old inputs and calls are in `counterexamples/main_identity_regressions.json`; tests reproduce all four. The guard was first verified with the old version's unchanged seed stream, before the curriculum/version update.

## Verification and limits

Final generator SHA-256: `3e48bc38b429d18b6c54e8cf6af2daa1aae65ef6f55c71b513d797111868023b`.

The final required-rotation battery passes all twelve stages. Its semantic domain check accepts 600/600 generated draws and all ten canonical pair occurrences; its lesson smoke check accepts 12/12 lessons and 84/84 holdouts. The larger shared census covers 100 lessons per band, 300 total, 2,100 distinct inputs, and 2,100 holdouts without a declared-rival ambiguity, scoring error, or materialization error. Fixed-seed enumeration covers all three starting residues in all three bands: nine lessons, 63 holdouts, 23 unique inputs because the windows overlap. An independent 2,160-case boundary census covers seeds 0–9, indices 0–2, all six counts and four corners, and three extremal dimension pairs per count; it found no remaining grid-contract failure.

The portable task-test stage reports 103 passed and one skipped. That skip is the optional test requiring the retained original review census, which is deliberately absent from the isolated source runtime; the same real receipt is separately exercised by the receipt tool. The tests use portable reviewer helpers rather than fixed source-depth guesses.

These are finite checks against six distinct declared rivals, repeated across sixteen declaration namespaces. They do not prove identification against every imaginable rule or support arbitrary seed mixing, multiple-query rotations, or a curriculum forced through exact marker-count overrides. Same-seed contexts intentionally preserve some answer-equivalent rivals. Exporters must retain the six-demo policy and inspect any changed lesson assembly. The canonical ledger and all audited task sources remain outside the semantic repair.

Full command receipts, failures, audits, solve histories, and the final fresh-packet replay are retained in the associated return ZIP. The broader repository run also found two supplied-source assertion/diagnostic mismatches and one interpreter-path-sensitive failure, each reproduced on the untouched packet; they were not repaired through this task's scoped delta.
## Inherited reviewer considerations

Source SHA-256: `3e48bc38b429d18b6c54e8cf6af2daa1aae65ef6f55c71b513d797111868023b`.

# Decisions for 747486860e56

Assignment `review-4c48d7aaa24ba47f`; final generator `4.1.0`, SHA-256 `3e48bc38b429d18b6c54e8cf6af2daa1aae65ef6f55c71b513d797111868023b`. Racket rule `0ab2a183017a` and its canonical ledger are unchanged. Counts below refer to this source unless explicitly marked baseline or intermediate. Evidence is retained in this return; large JSON receipts are losslessly compressed with an original-path mapping in `checks/COMPRESSION.json`.

## D1 / R1: Derive the object and vote semantics from the selected authority

The inherited description asked for a single-color diagonal pattern and isolated marker dots with a majority color. The selected program instead uses multicolor eight-connectivity, chooses the largest object, and then counts every nonzero cell outside it. The residual plurality wins, including frequency ties settled by first row-major occurrence among tied colors. The triangle's leg is the residual count minus one; the triangle is painted after the main object and can overwrite it. These distinctions matter on the existing examples: touching residual cells and a frequency tie already occur, and residual colors can also occur in the main object.

The ten canonical labels are two orderings of five unique pairs. The baseline validator rejected all ten pair occurrences. Requiring pairwise isolation, excluding the main color from residuals, requiring a strict majority, or using four-connectivity would preserve that defect. The revised self-check measures the actual grid independently of generation metadata. Multicolor and overlap samples are deliberate extensions supported by the unchanged authority, not newly invented output rules. The original author's reasons for the tighter restrictions are unknown: the imported notes and associated-notes file supply no rationale.

## D2 / R2: Advertise four observable exact controls

Keep `grid_h`, `grid_w`, `corner`, and `n_markers`; measure them from the grid. Dimensions span 6–24, counts span 3–8, and all four corner orientations are available. Reject unknown or obsolete controls instead of silently accepting an ineffective value. `None` means omission, following the shared generator-context convention. The earlier test assertion that `None` should fail was itself wrong; its four failures are preserved in `checks/focused-after-initial.log`, and the test was corrected to the public API.

The generator declares the dimension-six/count-eight combination incompatible because a leg-seven triangle cannot fit. It otherwise validates exact integer values and reconstructs the main and residual roles before returning. Avoiding this explicit incompatibility by clipping the triangle would change the supported envelope and obscure the intended size relationship. Silently increasing dimensions or reducing the requested marker count would violate exact controls.

Independent review found that merely validating a returned grid was insufficient: in four intermediate cases, the residual cluster overtook the intended main. All grids could look lawful while `n_markers=7` or `8` became `6` or `7`. The final acceptance guard now compares the selected main with the intended main and checks the observed residual count. The old inputs, public Racket outputs, five red regressions, and guard-only green result are retained. The guard was checked against the old version's seed stream before changing the version, preventing seed churn from masquerading as a fix.

## D3: Mix canonical profiles with broader lawful shapes

Keep canonical size/palette profiles in every difficulty band, while drawing new connected patterns and broader dimensions. The final profile-floor check hits exact profiles in 44/60 draws: easy 15/20, medium 12/20, hard 17/20; 49/60 also lie inside the observed profile envelope. There are no canonical rejections or zero-support bands. These are small, fixed gate samples, not estimates of all possible support.

The strict hook denotes the declared lawful generation envelope: rectangular integer grids, zero background, a uniquely largest component of at least four cells, 3–8 residual cells, one residual corner, and an in-bounds triangle. It does not assert that all generated pictures are visually identical to canonical examples. The final semantic gate finds 600/600 draws in that envelope, 200 per band. Deliberately exclude equal-largest components, zero residuals, absent/multiple residual corners, and clipped triangles; their broader Racket behavior is not needed to teach this task and is not claimed by the generator.

## D4 / R3: Make the lesson, not just each sample, counter a rival

The supported lesson is **six demonstrations plus one query**, using consecutively accepted samples at one seed. The period-three order is `corner_vote`, `tie_low`, `tie_high`; any of the seven labeled pairs may be held out once while the remaining order is preserved. Repetition leaves evidence after a single holdout. The independent episode context chooses mono/multicolor main objects and critical/neutral corner roles from the seed. Context bits are independent of the profile index.

Core profiles use counts 3, 5, 6, or 7. Odd cores carry an ordinary strict majority; six-cell cores have a unique 2/6 plurality. Tie profiles use 2/2/1/1 residual counts, with a singleton losing color at the corner and another at the first residual position. The winner is therefore the first **tied** color, and its numeric rank alternates between lower and higher. Tied scenes also carry residual contact and main/triangle overlap. Main colors and residual colors can overlap.

In critical contexts the corner changes the vote outcome. In neutral contexts it is a losing color. A corner-exclusion rival may agree with every label of a neutral episode, and the monochrome-object rival may agree with every label of a monochrome episode. These are answer-equivalent surviving hypotheses in those measured episodes; they are not evidence that the same rival can fit all demonstrations and disagree on that query. The lesson check tests exactly the latter defect. We do not claim arbitrary seed mixing, arbitrary reorderings beyond the measured holdouts, multiple-query rotations, or identifiable lessons under forced exact marker-count overrides.

Rejected alternatives include one canonical-shaped scene repeatedly recolored, a permanent winning corner, tie selection by minimum/maximum color, and independent rare witnesses without lesson-level assembly checks. All can yield correct individual labels while teaching a shortcut or failing to distinguish a query.

## D5 / R3 / F1: A green ambiguity report can still hide a distribution gap

The intermediate `4.0.0` source (`c441345c25d526fb529ec3510a0082f7368dc8a6866ba913f0f93049fcdad129`) passed its twelve-stage battery and 300-lesson/2,100-holdout census against its original five distinct rivals. Independent review then found a conditional shortcut: use the corner's color for a monochrome main, otherwise the first residual color. That rival fits only 2/10 canonical pair occurrences but matches every generated label in the retained intermediate census. A query-ambiguity checker still passes because it sees no differing query answer in that sampled distribution.

The revised context choices and singleton-loser positions break this association. The final same-sized census refutes the conditional rival in all 300 lessons and all 2,100 holdouts. These counts mean a demonstration refutes the rival; they do not mean 2,100 separate query predictions were wrong. The final receipt has sixteen namespace-qualified declaration rows covering six distinct hypotheses.

The included `workspace/audit_rival_coverage.py` compares canonical fit with generated survival from existing receipts. It exposes the exact retained intermediate gap and reports none in the final receipt. It joins rescore and canonical evidence only with matching current generator/rule/declaration identities. Keeping this prototype task-local avoids an unrequested shared-tool change; F1 identifies the shared integration proposal. The earlier green census and newly diagnosed gap are both preserved, not overwritten by the final pass.

## D6 / R4: Synchronize selected authority text without changing the rule

The canonical program is the authority. Copy its exact existing bytes only into the two assignment-listed `racket_target.target_code` strings. The training selected text had legacy syntax/comments; the augmented selected text differed in layout. Canonical execution parity on five examples does not prove all texts universally equivalent, so archival `raw_code` was preserved rather than promoted or rewritten. Verification proves every byte outside the selected JSON string tokens and the entire canonical ledger stayed unchanged. Four active authority entries now form one exact-text group, with permitted archival divergence still reported explicitly.

## D7: Evidence and scope of acceptance

The final larger census uses the shared production sampler: 100 requested starts per band, index 0–99, deterministic seeds from the documented `lesson-census:v1:TASK:BAND:INDEX` hash recipe. It materializes 300 lessons and 2,100 distinct inputs, then checks all 2,100 single-pair holdouts. It reports no materialization or scoring errors, hook warnings, or declared-rival ambiguities. The separate seed-zero schedule enumeration covers all three starting residues in all bands, nine lessons and 63 holdouts, but only 23 unique inputs because windows overlap. Neither run proves all-seed or all-hypothesis identifiability.

The independent boundary matrix covers 2,160 calls: seeds 0–9, indices 0–2, six counts, four corners, and three extremal dimension pairs per count. It checks graph facts and controls without executing Racket. The Racket-backed battery/censuses supply separate label evidence. The portable task stage reports 103 passed and one optional retained-census test skipped; direct tooling tests also exercise the actual historical receipt. Exact final-delta replay is recorded in `checks/final-replay/`.

The separate blind task was solved before the repair with no prior rule exposure. The post-repair solve is declared exposed at the supervising-reviewer level, while its delegated solver receives only public visible examples and checker feedback. Query correctness remains withheld. Work logs and revisions are evidence of the attempts, not token-level reasoning traces.

Both assigned audit targets remain unmodified. A1 independently confirms a previously recorded unresolved texture/validator inconsistency; A2 reproduces a supported `spans=None` route to a rotated-lesson ambiguity. Their source-bound counterexamples and actual reference outputs are in `AUDIT.md`. The broad repository test run was not wholly green: two supplied-source assertion/diagnostic mismatches and one relative-interpreter spelling issue reproduce on the original ZIP. Those shared defects are outside this scoped task repair; no catalog approval or shared-source alteration is included.
## Current reviewer considerations

Source SHA-256: `008f30c17748241bfc1bc3678dda6f34faba375edea6cc20a447a3823a9aa8ad`.

# Decisions for review-e119992824f89f40

## D1 — Reject malformed request scalars at one front door

**Decision.** Add `_validate_request(seed, sample_index, difficulty)` and call it from both `schedule_profile` and `generate`.

**Evidence.** The baseline strict defect stage accepted boolean/float/string/`None` seeds, boolean/negative/non-integer sample indices, and invalid difficulty values. The red regression run has 12 expected failures in `checks/tdd-request-validation-red.log`; the same tests pass in `checks/tdd-request-validation-green.log`.

**Why this design.** Validation at both public entry points prevents schedule and generation from disagreeing. `type(x) is int` intentionally rejects booleans. A nonnegative sample index matches the schedule's indexing contract. The accepted difficulty set is explicit and identical to the generator's existing bands.

**Rejected alternatives.** Relying on `gen_ctx` would leave `schedule_profile` unguarded and had already allowed malformed controls. Coercing values would make typos reproducible but semantically wrong. Bumping `VERSION` would churn every valid deterministic sample even though valid behavior is unchanged, so version `4.1.0` is retained.

## D2 — Synchronize selected authority text only after semantic review

**Decision.** Replace only the selected training and augmented `racket_target.target_code` strings with the exact canonical source. Preserve both `raw_code` fields and all unrelated JSON bytes/values.

**Evidence.** The supported authority-sync dry run refused the training target because it was token-different, so no automatic patch was forced. `checks/authority-sync/manual_equivalence_probe.json` compares canonical plus both selected legacy programs on 586 lawful inputs and records 1,758 live Racket evaluations with zero mismatches. `tests/test_authority_binding.py` failed before synchronization and passes afterward. Final authority sync reports selected synchronization with archival divergence explicitly retained.

**Limits.** Finite execution parity does not prove universal program equivalence. The canonical program was already authoritative, so the repair does not promote either legacy string; it copies the authority into the selected execution field and keeps the original text as archival evidence.

## D3 — Parameterize only triangle leg length

**Decision.** Build one proposed parameter, `triangle_leg_mode`, with values `residual_minus_one` (canonical `K-1`) and `residual_count` (proposed `K`). Choose the value once per episode and keep the prototype outside the production generator.

**Why this parameter.** It is a small, interpretable change to the original family's quantitative relation while preserving every object role and reasoning step. It produces visibly distinguishable outputs on ordinary lawful scenes and can be expressed by a one-site Racket source change. Color voting, component connectivity, and paint order were not parameterized because changing them would entangle several already-important teaching contrasts rather than form a clean original-family variant.

**Evidence.** `checks/parametric/triangle-leg-v1/report.json` binds exact rule sources, callable hashes, public/private episodes, and source snapshots. Both settings are exercised; each episode's three demonstrations refute the other setting; there are zero measured parameter-rival ambiguities; the canonical setting replays all ten labeled canonical occurrences.

**Limits.** Two seeds, four authored inputs, and the two declared parameter rivals are finite authoring evidence. The proposed `K` setting requires one additional row/column of fit. It is not approved, exported through `AXES`, or used by the selected generator.

## D4 — Keep the initially failed after battery and close it with an explicit schedule receipt

**Decision.** Retain the prescribed after run at `checks/after/` rather than hiding it. Run the exact fixed-seed period enumeration, then bind its receipt to a fresh `checks/after-final/` battery.

**Reason.** The first repaired battery had 11/12 green; semantic content itself passed, but strict after policy correctly rejected the unenumerated declared period. The follow-up source-bound receipt covers all three starts in all three bands and all 63 holdouts. Binding it gives a truthful 12/12 final result without downgrading the first warning or pretending sampled checks exhaust a schedule.

## D5 — Preserve the established six-demo curriculum claim

**Decision.** Keep six demonstrations plus one query, same-seed consecutive accepted samples, period-three profile order, and arbitrary single-query holdout of the seven labeled pairs.

**Evidence.** The larger final census materializes 300/300 lessons and all 2,100 rotations with no declared-rival ambiguity, hook warning, or scoring error. The seed-zero schedule census covers nine band/start lessons and 63 rotations. These checks use Racket labels and source/hash bindings.

**Limits.** The results cover six distinct hypotheses repeated across declaration namespaces; they do not establish universal induction, all-seed schedule coverage, arbitrary mixed-seed lessons, or exact-control curricula.

## D6 — Retain full large evidence in compressed form

**Decision.** Deterministically gzip the 20,967,404-byte full lesson census, retain its compact summary, and add `checks/COMPRESSION.json` with original/compressed hashes and a restoration command.

**Reason.** This preserves every exact lesson and rotation while staying within the return's 25 MiB expanded-member budget. No failed iteration or unique counterexample was deleted to create space.

## D7 — Audits are findings-only

The assigned audit targets `48fee61713bb` and `8387b52c80df` were not edited. Fresh current-source reproductions are recorded in `AUDIT.md` and `checks/audit/`; passing or failing their checks does not affect selected-task acceptance.

## D8 — Replay the exact patch in a fresh full packet

**Decision.** Build a provisional hash-bound return, replay its source patch against a new full extraction of the original ZIP, and rerun the selected portable task suite inside that checkout before producing the final return.

**Evidence.** `checks/final-replay/replay.json` records all 88,765 original files extracted, nine changed files applied, patch SHA-256 `53fb98068a7bc3f7a14041ca7a298c555319803cf01852f715a8be5cb6d5a080`, and final generator SHA-256 `008f30c17748241bfc1bc3678dda6f34faba375edea6cc20a447a3823a9aa8ad`. `checks/final-replay/fresh-task-tests/result.json` reports 135 passed and one inherited-receipt skip in that fresh runtime. The combined binding is `checks/final-replay/summary.json`.

**Limit.** The replay validates the exact source delta and selected task tests, not a second full 300-lesson census; the final source-bound battery and census remain the evidence for those broader properties.
