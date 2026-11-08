## 5d1263287a4f

**Classification: Reproduced known production teaching shortcut — return the rightmost third.** The current `needs_triage` finding from `review-d3192d76dc7ddbba:v0001` remains reproducible on the same selected source. This audit supplies fresh production and Racket evidence; it does not resolve or close that finding.

Selected generator SHA-256: `e88a731c55edf29fc56e15aaf9c56d0f379c262f63d569caeab9af498822339d`. Selected/executed canonical rule hash: `92f6a0f9f7b3`. The rule splits the input into three equal-width panels and returns the leftmost. The public canonical source is retained in `checks/audit/5d1263287a4f/selected_authority.json` and `checks/audit/5d1263287a4f/rule_snapshot.rkt`; the exact generator is retained in `checks/audit/5d1263287a4f/generator_snapshot.py`.

The rival that returns the rightmost panel fits all **4/4 canonical pairs**. A fresh public production run generated only three episodes at base seed `20261006`, difficulty `medium`, three demonstrations and one query, with no overrides. Episode index `2` reproduces the retained ambiguity. Its actual generator seed is **`20261008`**, and its accepted sample indices are **`[0, 1, 2, 3]`**, with four attempts and no rejected pairs.

| Role | Sample index | Observed panel layout | Rightmost rival matches selected Racket output |
| --- | ---: | --- | --- |
| Demonstration 1 | 0 | `all_same` | Yes |
| Demonstration 2 | 1 | `middle_mirror` | Yes |
| Demonstration 3 | 2 | `middle_mirror` | Yes |
| Query | 3 | `both_mirror` | No |

**Sampler and validator scope.** All four inputs were emitted by ordinary production sampling without overrides. The bounded reproducer independently regenerates each exact input using `generate(20261008, index, difficulty="medium")`, and `self_check` returns `[]` on all four. The evidence therefore establishes a reachable production lesson, rather than relying solely on a hand-authored input accepted by the validator.

**Authority check.** Fresh public `arcpuzzles apply` execution returned four valid outputs with zero errors, matching the production labels. On the query, the authoritative left panel is `[[0,9,9],[8,3,0],[0,3,0]]`, while the rightmost rival returns `[[9,9,0],[0,3,8],[0,3,0]]`. The source identity and normalized rule identity match between the public lookup, generation and apply receipts. `finding.json` keeps the raw canonical source SHA-256 and the bridge-ready callable SHA-256 separate because those fields hash different text representations.

**Cause and suggested follow-up.** Weighted independent layout sampling can place every position-disambiguating example in the query. The materialized lesson records `lesson_check.status = "not_declared"`, with no executable rival declaration. A maintainer could declare the rightmost-panel competitor and guarantee that the demonstrations contain a `right_mirror` or `both_mirror` witness, through a lesson contract, sampling constraint or teaching schedule. The current individual outputs are correct; the reproduced issue is that both the intended rule and a canonical-fitting rival explain every demonstration and disagree on the query.

**Bounded checks and commands.** Outer working directory for every command below: `/workspace/scratch/362f05acc31b/packet`; payload working directory: `/workspace/scratch/362f05acc31b/packet/WORK/repo`. No full battery or unbounded seed sweep was run.

```bash
python3 review.py run python3 -m arcpuzzles show 5d1263287a4f --out ../checks/audit/5d1263287a4f/selected_authority.json
python3 review.py run python3 -m arcpuzzles generate 5d1263287a4f --count 3 --seed 20261006 --sample-index 0 --difficulty medium --train 3 --test 1 --allow-unapproved --out ../checks/audit/5d1263287a4f/production.jsonl
python3 review.py run python3 ../checks/audit/5d1263287a4f/audit_shortcut.py prepare
python3 review.py run python3 -m arcpuzzles apply 5d1263287a4f --input ../checks/audit/5d1263287a4f/input.json --out ../checks/audit/5d1263287a4f/racket.json
python3 review.py run python3 ../checks/audit/5d1263287a4f/audit_shortcut.py verify
```

All five commands completed with exit `0` using the corrected audit helper. An initial `verify` attempt exited `1` because the helper incorrectly equated the raw canonical source hash with the wrapped callable hash; only the audit helper was corrected, and the successful verification was rerun against the same Racket receipt. Both attempts are retained in `checks/audit/5d1263287a4f/commands.json`.

Evidence: `checks/audit/5d1263287a4f/finding.json` contains exact inputs, production/rival outputs, canonical-fit results, layouts, validator results and sampler provenance; `checks/audit/5d1263287a4f/racket.json` is the fresh public authority receipt; `checks/audit/5d1263287a4f/audit_shortcut.py` is the portable reproducer. Selected sources, tests, notes, catalog and shared code were left unchanged. No approval, closure or training admission action was taken.
