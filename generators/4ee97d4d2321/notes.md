# Working notes: 4ee97d4d2321

## 2026-10-04 review `review-36ef73706f62e68c`

The retained return `external-local-random:a00e1780c9a9` and audit `review-4cd35f21d087afc9:v0001` were used only as leads. The pinned baseline was remeasured at generator SHA-256 `79db02707e07db4033262cefe67b39c849b8fab2ebb431b3ea0e2f0292471677`; its full 12-stage battery passed, but an undeclared shortcut remained: default `axis_offset` deterministically identified `source_mode`. An independent probe matched the intended rule on 360/360 baseline draws while an explicit lawful `(source_mode="both", axis_offset=1)` scene refuted it.

Version `4.0.0` uses a 20-slot Latin schedule crossing all four source modes with all five offsets. It exports the full joint profile space and declares `infer_source_side_from_axis_offset` as a lesson competitor. Tests require all 20 legal pairs in every band and require every cyclic four-example window to refute the shortcut. The reusable probe in `workspace/axis_offset_shortcut_probe.py` independently checks joint support and shortcut survival.

Final generator SHA-256: `dff3f83cf2dba19b5135915f02eb058a685adb879a2703fe70398f0f11623573`. The selected Racket authority and rule hash `7546649ac4b7` were unchanged. The completed after battery is 12/12 green; the task-local suite is rerun separately because the general battery does not discover it.

## Retained domain boundary

The grammar still excludes preoccupied reflection targets even though the broader oracle can execute them. This remains a deliberate calibration boundary from the earlier review, not a claim about oracle undefinedness. Finite named-rival checks do not prove universal identifiability; future schedule edits should rerun both the shared lesson census and the exhaustive 20-start task-local probe.
## Current reviewer considerations

Source SHA-256: `dff3f83cf2dba19b5135915f02eb058a685adb879a2703fe70398f0f11623573`.

# Decisions — `4ee97d4d2321` / `review-36ef73706f62e68c`

## Intended result and authority

The intended transformation was already correct: find the unique full-height color-8 column, preserve every input cell, and reflect each nonzero non-axis source across that column when the destination remains in bounds. The canonical Racket implementation, five canonical pairs, and rule hash `7546649ac4b7` agree. I therefore changed the teaching distribution and semantic contract, not the reference rule.

The pinned v3 implementation had already repaired many earlier defects and passed the complete battery. Its remaining problem was subtler: ordinary examples made `axis_offset` a perfect proxy for `source_mode`. The original author's reason for that correlation is unknown. Retained review material was used as a lead only; `checks/axis-offset-shortcut-before.json` is the new baseline measurement.

## Distribution choices

| Choice | Reason | Rejected alternative | Evidence / failure mode |
|---|---|---|---|
| Use a 20-slot Latin cross over four source modes and five offsets | Preserve every four-example semantic curriculum while covering every legal joint pair | Draw mode and offset IID | IID sampling gives no deterministic lesson guarantee and can leave short windows shortcut-compatible |
| Make source mode the fast cycle and offset the Latin-shifted slow dimension | Any consecutive four samples contain all four mutually exclusive source modes | Randomly shuffle one 20-item block | A block shuffle does not guarantee every boundary-spanning four-window contains all modes |
| Export tuple-valued `SCHEDULE_PROFILES` | Let shared gates see the actual joint schedule rather than four opaque residue IDs | Keep integer profiles and test only task-locally | The framework would again miss the joint-axis defect |
| Declare `infer_source_side_from_axis_offset` as an executable competitor | Turn the exact observed shortcut into a permanent teaching invariant | Rely only on contingency-table support | Full support alone does not prove each complete lesson refutes an output-changing shortcut |
| Keep `EXAMPLES_NEEDED = 4` | Matches the current fixed-query lesson policy and canonical scale | Increase to seven demos so every one-of-eight holdout contains all modes | Nearly doubles lesson cost for a query-rotation policy not currently used |
| Keep the canonical rule and base data unchanged | The defect is distributional, not an authority mismatch | Rewrite Racket or canonical examples | Would change the task and invalidate the already passing parity evidence |
| Keep the preoccupied-target exclusion | It is a deliberate grammar/calibration boundary from the prior repair | Broaden the generator to every rule-executable grid | Broader coverage is unrelated to the identified shortcut and would require a new semantic design review |
| Add an independent reusable probe | Future reviewers need a cheap regression that does not trust the generator's own rival | Put all logic only in the production generator or its tests | Mirrored bugs could make a self-referential test pass |

## Exact schedule design

For sample index `i`, the source-mode slot is `i mod 4`, the four-sample block is `floor(i/4)`, and the offset index is `(block + slot) mod 5`. Across indices `0..19`, each source mode occurs with every offset once. Across every four consecutive indices, the four source modes each occur once. The cycle repeats every 20 indices.

This schedule removes the learned rule “axis position tells me which side matters.” It does not aim to make every observable feature statistically independent. The canonical-anchor choice repeats every three indices; because 3 and 20 are coprime, each joint mode/offset pair encounters every anchor phase over a 60-index super-cycle rather than being permanently tied to one shape regime.

## Why deterministic crossing instead of IID sampling

The training unit is a short lesson, not an infinite population. IID support can look healthy in aggregate while individual lessons remain ambiguous. The deterministic schedule provides three separately checkable guarantees:

1. one full 20-sample cycle has exact legal joint support;
2. every consecutive four-example window has every source mode;
3. every such window contains at least one disagreement with the axis-position rival.

The first guarantee is a distribution property, the second a branch-coverage property, and the third an answer-level teaching property. None substitutes for the others.

## Tests and probes chosen

The production test additions were written in three red/green increments:

1. require the full joint support and zero surviving four-example windows;
2. require `SCHEDULE_PROFILES` and `schedule_profile` to expose the 20 joint tuples;
3. require the shortcut to appear in the declared lesson competitors and match an independent test implementation.

The reusable workspace probe loads the selected generator by path, reimplements the shortcut, samples production defaults, checks every overlapping lesson window, and constructs the lawful explicit `(source_mode="both", axis_offset=1)` counterexample. Its test compares the probe rival against another independent implementation before trusting its aggregate. TDD red and green artifacts are retained under `checks/tdd-red-*` and `checks/tdd-green-*`.

The shared lesson census was run with 100 lessons per band and optional query rotation. The fixed-query production view is clean; the optional rotation view is not. I retained the nonzero exit and ambiguous report rather than converting it into a pass.

## Rotation decision

A five-pair lesson contains four demos and one fixed query. If an exporter may hold out any pair, every source mode must occur at least twice in the five-pair bundle so removing one example cannot erase a branch. Four modes therefore require at least eight pairs. The current bundle cannot satisfy that combinatorial requirement regardless of schedule ordering.

Three alternatives were considered:

- **Seven demonstrations plus one query.** Strongest simple guarantee, but nearly doubles tokens and changes the established lesson contract.
- **Choose the query first, then resample demos.** Efficient, but moves correctness into the exporter/materializer and needs source-bound replay evidence there.
- **Duplicate only rare branch witnesses.** Cheaper than eight fully broad pairs, but creates a more complicated profile contract and can introduce new surface correlations.

Because current production uses a fixed fifth query and 0/300 such lessons were ambiguous, I documented the limitation rather than changing lesson size. `Acceptance: routine` is explicitly scoped to that assembly policy.

## Self-review for new shortcuts or restrictions

The repair could have replaced one deterministic mapping with another. The independent final probe therefore checks the full mode/offset contingency table and answer-level rival survival, not only source code structure. It finds 20/20 pairs in each band, 50% single-example shortcut agreement rather than 100%, an explicit lawful disagreement, and 0/300 surviving lesson windows.

The schedule remains deterministic and assumes consecutive sample indices. An exporter that selects a constant stride instead of consecutive indices can undersample residues; a packed-dataset gate should validate the exported lessons rather than infer coverage from generator declarations. The finite seven-rival contract is not a proof against every unnamed shortcut.

## Evidence handling

Four exhaustive reports exceeded the return's expanded-size budget. They were compressed losslessly with deterministic gzip; no records were sampled or discarded. `checks/COMPRESSED-EVIDENCE.json` records each original path, byte size, SHA-256, compressed path, compressed SHA-256, and restoration command. Human-readable aggregate reports remain uncompressed.

## Stopping decision

The source repair, TDD regressions, full battery, selected task tests, independent probe, lesson census, both assigned audits, blind solve, post-repair solve, and fresh patch replay are complete. No Racket authority or training-admission state changed. The only remaining data-policy decision is whether a future exporter must support arbitrary query rotation; that is documented rather than falsely reported green.
