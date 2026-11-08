## 52d56c2a0191

**Finding: confirmed unchallenged color-selection shortcut; moderate curriculum gap. Target sources were preserved.**

The audited generator is version `4.0.0`, SHA-256
`fb6ab5e45958a64fa7fad8ebe5ca2cfccc2601d135bd05893b7ead8ade96afee`.
The canonical and executed rule hash is `5c9566dd0981`.

### Finding and exact discriminator

A plausible wrong rule is: **select the most frequent nonzero color, then
return the sorted sizes of its 4-connected components**. This rival fits
all five canonical pairs and all 300 grids measured in this audit. Source
inspection explains why the current sampler cannot distinguish it: each
non-red distractor color occurs exactly once, while every generated red
scene contains at least four red cells. Therefore red is always the unique
most frequent foreground color, independently of seed, canvas, difficulty,
or selected scene profile.

An accepted-domain counterexample is reproducible from:

```python
grid = generate(
    16, 0, difficulty="easy",
    scene_profile="canonical", canvas_profile="h10_w12_p7",
)
for column in range(7):
    grid[1][column] = 1
```

All seven changed cells were zero; color 1 already existed in the input.
The 10×12 dimensions, seven-color palette, and red components remain
unchanged. Red has six cells in components of sizes 1, 2, and 3. Color 1
now has eight cells in components of sizes 1 and 7.

| Check | Measured result |
| --- | --- |
| `self_check` | `[]` |
| `strict_canonical_like` | `[]` |
| `observe_overrides` | `canonical`, `h10_w12_p7` |
| Public Racket output | `[[1, 2, 3]]` |
| Independent red-component oracle | `[[1, 2, 3]]` |
| Most-frequent-color rival | `[[1, 7]]` |

The exact input SHA-256 is
`60206cfa836ea3c31214a3abab69898059c5b36c96ced3fe68a44d29cebb4985`.
Public `arcpuzzles apply --reference canonical --check-generator-domain`
confirmed a valid reference output and accepted generator domain.

This is an authored mutation of an exact generated input. The generator
does not emit this dense-distractor pattern, and this audit found no
incorrect generated labels. The gap is that its examples never separate
the intended fixed-red selector from this plausible frequency selector.
The existing `all_nonzero_component_sizes` rival does not cover that
distinction. The documented limitation to named rivals is accurate;
the current semantic gate does not evaluate the newly tested rival.

**Suggested future repair:** vary the sizes and total counts of non-red
distractors while preserving the selected canvas/palette profile, include
a lesson where a non-red color is more frequent than red, and add this
frequency-selector rival to the curriculum checks. No repair was applied
in this audit.

### Checks and limits

The independent Python probe checked 180 forced-profile grids covering
all 4 scene × 5 canvas × 3 difficulty combinations at seeds 0, 123, and
20261020, plus 120 default grids covering sample indices 0–39 in each
difficulty band. All 300 passed both validators, matched the independent
component oracle, and matched the wrong selector rival. The five canonical
pairs also matched the oracle and rival.

Public Racket apply checked **27 inputs**: the five canonical pairs, 20
forced scene/canvas representatives, the exact generated base, and the
counterexample. All 27 reference outputs were valid, matched the
independent oracle, and had accepted generator domains.

The current-source audit preset completed **2/2 requested stages**:
**80 passed JUnit cases, 12 unique test functions, 0 failures/errors/skips**,
and **semantic gate green**, with no advisory or changed runtime source.
This was the audit preset, not a rerun of the complete 12-stage battery;
the native battery summary correctly leaves its 11 unrequested stages
pending. Older battery/census claims in the task notes remain inherited
evidence rather than new measurements from this audit.

The unresolved inherited `no_red` audit targets older generator
`2ffebf69fe62f090dbe467b8bf098e34559369c69961cb895ae5d606dcfabff0`.
On the current source, `generate(123, 0, texture="no_red")` raises
`ValueError: unknown override axes: ['texture']`, and `self_check` rejects
the retained no-red input. That historical defect did not reproduce on
the current source. Its repository status remains `needs_triage`; this
findings-only audit did not change that status.

Final verification confirmed that all **24 task files** hashed before
the custom probe and the selected canonical rule were unchanged.

### Reproducible evidence

All paths below are under the packet's `WORK/` directory:

- `checks/audit/52d56c2a0191/commands.json` — exact commands, working directory, exit codes, and elapsed times.
- `checks/audit/52d56c2a0191/probe.py` and `probe_summary.json` — independent oracle, rival, complete sample lattice, and measured counts.
- `checks/audit/52d56c2a0191/input.json` and `counterexample.json` — exact input, base seed/overrides, mutation, validator results, and reference/rival outputs.
- `checks/audit/52d56c2a0191/racket_apply.json` — public Racket receipt; counterexample is result index 26.
- `checks/audit/52d56c2a0191/identity.json` and `reference_verification.json` — source/rule hashes, reference comparisons, and unchanged-source checks.
- `checks/audit/52d56c2a0191/combined/result.json` and `combined/checks/task_tests.xml` — current-source audit preset and test counts.
- `checks/audit/52d56c2a0191/inherited_recheck.json` — bounded current-source recheck of the historical no-red finding.
