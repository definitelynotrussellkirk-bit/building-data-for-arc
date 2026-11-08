# Solve isolation incident

The helper `/root/final_visible_solve` prepared the current source episode successfully with `python3 review.py solve prepare` and read only the public solve help, `WORK/solve/README.md`, and `WORK/solve/challenge.json` as task evidence at that point. It also read the `using-superpowers` skill, which says dispatched subagents should ignore it.

Before authoring a solution, notes, or any check attempt, the helper called `collaboration.list_agents` to determine whether an independent reasoning slot was available. The tool unexpectedly included a completed historical agent's final answer, which contained a prior solver hypothesis. The helper stopped solving immediately, reported the exposure to `/root`, and did not transfer the hypothesis to a replacement solver.

The existing prepared episode was handed to `/root/final_visible_solve/isolated_evidence_solver`, created with `fork_turns="none"`. That solver received only interface instructions and current public evidence paths, plus a factual disclosure that the previous helper was replaced. It was explicitly prohibited from reading historical solves, reports, rule/generator/reference material, private labels, or this incident note, and from calling `collaboration.list_agents` or other context-bearing collaboration calls. It alone owns authoring and checking the current `WORK/solve` solution.

The coordinating parent has earlier rule exposure. The replacement is instructed to finish with `earlier_exposure=yes` and `reference_consulted=no` for its own solve, and to distinguish the coordinator's exposure from its isolated inference. The episode must not be called blind.

## Commands executed before replacement

All shell commands ran from `/workspace/scratch/f9e780997a95/review` unless otherwise specified.

| Command | Exit code |
| --- | --- |
| `python3 review.py solve --help` | 0 |
| `python3 review.py solve prepare --help` | 0 |
| `python3 review.py solve prepare` | 0 |
| `cat /root/.codex/plugins/cache/openai-curated-remote/superpowers/6.4.2/skills/using-superpowers/SKILL.md` | 0 |
| `cat WORK/solve/README.md WORK/solve/challenge.json` | 0 |
| `python3 review.py solve check --help` | 0 |
| `python3 review.py solve finish --help` | 0 |

At replacement, the public preparation summary reported `attempt_count=0`, `status=prepared`, `source_kind=reviewer_authored`, generator hash `4f4c3ac1c0f97f84cc2d2d598408982c5a16b708e7e5f285e300115008284eb7`, and challenge SHA-256 `f00c1e36fb0af90b41e0e6c2d4b4b18e2ab15a5061033ab160e7182010e9219c`.

No private query correctness was read, computed, or reported by the replaced helper. No visible solve tests were run by that helper. The replacement's actual test results must be obtained from its current episode artifacts and direct completion report, not inferred from this note or any historical summary.
