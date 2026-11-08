# Teaching-data policy gate prototype

This is an optional, standalone Python standard-library prototype for a stricter training-data policy. It consumes an existing **trusted** `arcpuzzles-lesson-census-v1` report, an explicit `generator.py` path and the expected canonical rule hash. It accepts ordinary JSON or `.json.gz` and writes a fresh JSON result. It does not import or execute the generator, produce labels, run rivals, invoke Racket, modify selected source, or integrate with export.

## Policy

A passing report must have an explicit rival contract, a nonempty declared rival inventory, and at least one declared rival whose `canonical_rival_fit` says `fits_all` with nonzero, complete canonical-pair support and no errors. These canonical-compatible entries become the required rivals. There is no task-specific rival name list. Other declared rivals remain visible in the input inventory but are not newly promoted into the required canonical-compatible set.

The exact generator bytes must match the report and its runtime manifest. A static AST check requires a declared rival namespace and the expected literal RULE_HASH pin; it does not evaluate callability. The report declaration and catalog-provenance hash must match the supplied expected canonical rule hash. The retained manifest and instance hashes, execution result, requested/materialized population, per-band indices, pair counts and rotation structure must be complete and consistent. Error verdicts, scoring errors and hook warnings reject.

For every recorded production lesson, each required rival must have status **refuted**. In the actual census schema that status means the rival disagreed with at least one retained demonstration. Both `survived_all` and `ambiguous` fail this stricter policy. A missing rival score also fails. With `--require-rotations`, the report must record all query rotations and every required rival must be refuted by the corresponding rotated demonstration set. Precise lesson `{band,index}`, rival ID, rotation query index and recorded status are retained for every failed check; no failing-ID list is truncated. Result counts report how many lessons, rotations and individual rival checks were inspected.

Top-level informational warnings are preserved. For example, the final report warns that its short deterministic schedule was not explicitly enumerated. This prototype checks every *recorded* production lesson and rotation; it does not require a separate exhaustive schedule enumeration, so that advisory is not a completeness failure. Hook warnings are different: they indicate lesson-level contract concerns and reject.

Exit codes: **0** policy pass, **1** policy rejection, **2** bad input/CLI/output error. Existing output files are never overwritten.

## Actual source-bound results

| Retained result | Exit | Population | Outcome |
| --- | --- | --- | --- |
| `baseline-result-final.json` | 1 | 3 lessons, 12 rotations | Genuine rejection: untouched v1.1.1 lacks source/report rival contracts, a RULE_HASH pin and canonical-compatible rival entries. Source hash matches; this is not a stale-source failure. |
| `final-result-final.json` | 0 | 300 lessons, 1200 rotations | All required recorded rivals refuted in every production lesson and requested rotation. |

The final report records **18 required rival IDs**, representing six algorithms under three declaration namespaces. The prototype preserves those IDs rather than guessing whether implementations are aliases: 5,400 production rival checks and 21,600 rotation rival checks. These counts do not imply 18 independent semantic hypotheses.

Baseline input report SHA256: `d5b5bdbc430420de4b0512cd15786cc49cf90339b8d11f36fb194086f674589c`.

Baseline generator SHA256: `fefed50051fb506105704bf728ab02125a6ff4f7cd19302f3f2a75636cb101cf`.

Final compressed input report SHA256: `7edfb0714a8e848c618e6a49fdc7865169d0f697589652e6252cccc404830d08`.

Final generator SHA256: `96cbe5e3a78eb4ceed303e8cb6d73f2240024d473d3ab39aed6a8b353fc37f99`.

Expected canonical rule hash: `c3726fc6c507`.

Prototype source SHA256: `8f11f754cff25c11256f8176d09fc9aa050a080fa419a6c2a3a7ed42e89d0d47`.

Both result JSON files also retain the decoded report hash, resolved input/source paths, expected hash, command, working directory, actual CLI exit code, counts and all failure details. `run-receipts.json` binds the final executed commands and logs to this exact prototype hash. Earlier `baseline-result.json` and `final-result.json` and `first-policy-source.py` preserve the initial pass/fail run before the additional inventory/verdict consistency checks; they are not the final receipts.

## Exact commands executed

Launch directory for all commands: `/workspace/scratch/f5c082144427/review`.

```sh
python3 WORK/checks/teaching-gate-prototype/teaching_gate.py --census WORK/checks/teaching-gate-prototype/baseline-census.json --generator /workspace/scratch/f5c082144427/fresh-replay/WORK/repo/generators/6e068328f4ce/generator.py --expected-rule-hash c3726fc6c507 --require-rotations --out WORK/checks/teaching-gate-prototype/baseline-result-final.json

python3 WORK/checks/teaching-gate-prototype/teaching_gate.py --census WORK/checks/lesson-census-final.json.gz --generator WORK/repo/generators/6e068328f4ce/generator.py --expected-rule-hash c3726fc6c507 --require-rotations --out WORK/checks/teaching-gate-prototype/final-result-final.json

python3 -m unittest discover -s WORK/checks/teaching-gate-prototype -p test_teaching_gate.py
```

Actual exit codes were **1, 0, 0**. The baseline check occurred before the fresh replay generator was patched. Repeating that command after replay should reject its changed source hash; it does not recreate the original baseline experiment. For any rerun, select a new output filename because the retained outputs already exist.

The targeted suite has four test families: the real complete census; eleven deliberate report mutations (missing contract, missing canonical-compatible rivals, incomplete lessons, report errors, top-level error verdict, dropped rival inventory, production survivor, rotation survivor, missing rival score, missing rotation and wrong rule hash); precise survivor IDs; and changed source bytes. All tests passed. These mutations are **test fixtures**, not claimed failures in the real final census. The initial preimplementation test import failed because the prototype module did not yet exist; it was not a generator or census finding.

## Limits and concrete false-positive / false-negative risks

This is a policy over trusted census reports, not a new ground-truth engine, an induction proof, a sampler audit or export integration. It trusts that the census actually ran the declared rivals against correct canonical Racket labels and recorded truthful outcomes. Hashes detect source/report drift; they do not establish report authenticity. A forged `refuted` status could pass. A faithful report covering only one seed or a narrow layout family can pass while an undeclared shortcut survives elsewhere. The gate does not discover omitted rivals, distinguish function aliases, verify controller binaries against a trust store or rescore predictions. The expected canonical hash must come from an independently trusted authority.

Strict rejection can also reject useful data. A rival may fit the canonical pairs yet be equivalent to the intended rule throughout an intentionally narrower generator domain. Such a rival will `survive_all` every lesson, and this policy rejects even if its query output is correct. An already correct simple generator with no rival contract is rejected on policy grounds, not proved semantically broken. Hook warnings may require human interpretation instead of unconditional exclusion in a future production policy. A dynamically assigned RULE_HASH pin can be valid but fail this deliberately simple static literal check.

Missing clipping support, unusual valid geometry or unenumerated schedule starts are not inspected beyond the recorded census. Additional task review, canonical authority checks, runtime trust and admission decisions remain separate. No source.patch or selected shared-tool change includes this prototype.
