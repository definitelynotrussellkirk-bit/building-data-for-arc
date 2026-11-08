Task/version: `537b409b6744` repaired from selected v4.0.0 to v4.1.0; final generator SHA-256 `34b8e36ac6bc1da85db025e34c4d908930dc5ce548cf3872e655312bb2e902cd`.
Baseline defect: 11/12 battery stages were green; defect lint failed with 48 accepted-invalid-scalar warnings for `seed`, `sample_index`, and `difficulty`.
Repair: reject non-literal/negative call scalars, retain the exact override surface, and add direct regression coverage.
Semantic defect: the canonical-fitting `smallest_mover` shortcut matched all 8 labeled canonical pairs but was undeclared and not guaranteed to be taught.
Semantic repair: declare that shortcut, retain an exact Racket-checked counterexample, and schedule default depths so every four-pair lesson refutes it under every one-query rotation.
Reference authority: canonical Racket bytes and declared `RULE_HASH=7b81cecb3b71` are unchanged; no shared/catalog authority file was edited.
Final battery: 12/12 green, including 600/600 strict semantic draws, all 8 canonical inputs, 3 witnesses, and 31,230 override draws with 0 findings/warnings.
Focused task tests: 90 passed both in the working portable runtime and after applying the return patch to a fresh full-packet checkout; both receipts match the SHA above.
Lesson evidence: 300 ordered three-demo/one-query lessons (100/band), 1,200 unique pairs, production 0/300 ambiguous; all-query rotations 0/1,200 ambiguous.
Parametric assessment: proposed, unapproved `candidate_selection=nearest|farthest` prototype; 2 Racket-labeled episodes, 16 executions, 6 distinguishing demonstrations; nearest is byte-exact canonical.
Remaining blocker: none for the canonical repair; finite rival checks do not prove universal identifiability, and the parametric variant is not approved or on the production path.
Acceptance: routine.

## Finding table

| ID | Affected task/path | Finding or change | Reproducer/evidence | Patch status | Result |
| --- | --- | --- | --- | --- | --- |
| R1 | `generators/537b409b6744/generator.py` | Invalid `seed`, `sample_index`, and `difficulty` scalars were accepted. | `checks/before/checks/537b409b6744_before_defect_lint.log` | Fixed in v4.1.0 | Final defect lint green. |
| R2 | `generators/537b409b6744/generator.py` | `smallest_mover` fits all 8 canonical labels but can choose the farther object. | `checks/shortcut/smallest-mover-evidence.json`; task counterexample JSON | Fixed in declarations, schedule, tests, and lesson contract | 317/600 witness hits; 0/300 production and 0/1,200 rotation ambiguities. |
| P1 | `generators/537b409b6744/workspace/parametric/` | Nearby rule parameter chooses nearest or farthest qualifying pair once per episode. | `checks/parametric/candidate-selection/manifest.json` | Proposed prototype only | 2 episodes, 16 Racket runs, 6/6 demos distinguish settings. |
| A1 | Audit-only `f563fafba6ac` | Enclosed-hole-area ordering fits all canonical and sampled generated cases but disagrees on a lawful validator-accepted input. | `checks/audit/f563fafba6ac/hole-area-rival-evidence.json` | Not patched | Reproduced; selected audit source left unchanged. |
| A2 | Audit-only `64a8d13b4024` | Advertised exact override contract is broadly violated. | `checks/audit/64a8d13b4024/override-contract-evidence.json` | Not patched | Reproduced; official override stage failed with 4,586 findings. |

## Repair details

### R1 — strict call contract

The before battery showed 48 warnings because booleans, floats, strings, negative
sample indices, and invalid difficulty values reached generation. v4.1.0 now
requires a literal integer seed, a literal nonnegative integer sample index, and
`difficulty` in `{None, "easy", "medium", "hard"}`. This is deliberately separate
from public axis validation: valid explicit overrides and all default bands keep
their prior domains. The after defect-lint stage is green, and the portable task
suite includes direct rejection tests.

### R2 — canonical-fitting shortcut and lesson repair

The strongest observed shortcut selects the qualifying candidate with the
smallest mover area, breaking ties by the canonical ranking. It matches all 8
usable canonical labels. The retained counterexample uses seed 1, sample index
17, and explicit 10x10/down/solid settings: the intended candidate has area 4 at
gap 1, while the shortcut chooses area 2 at gap 3. The selected Racket output
matches the independent Python oracle and differs from the shortcut output.

The shortcut is now present in `SEMANTIC_RIVALS`, `CANONICAL_SHORTCUTS`,
`LESSON_COMPETITORS`, `SEMANTIC_WITNESSES`, and `WITNESS_RIVALS`. Default mover
depth alternates by sample-index parity while explicit overrides remain intact;
combined with the existing distractor schedule, every four accepted sequential
pairs contains a shortcut-refuting example. Task tests enumerate the four cyclic
starts and every possible held-out query. The final semantic gate observed the
shortcut witness on 317/600 generated scenes, and the source-bound census found
all three declared rivals refuted in every production lesson and rotation.

### P1 — proposed parametric extension

`workspace/parametric/prototype.py` implements one bounded parameter:
`candidate_selection` in `{nearest, farthest}`, chosen once per episode from a
deterministic SHA-256 seed. It leaves object recognition, candidate construction,
wall cutting, growth, and mover relocation unchanged; only the gap extremum in
the ranking changes. The nearest Racket source is byte-for-byte the selected
canonical source. The retained manifest binds both Racket programs, two public
challenge files, two private answer files, source hashes, and the exact runtime.
This is authoring evidence only: it is not selected, approved, or training-admitted.

## Final checks and limitations

- Full after battery: `checks/after/checks/537b409b6744_after_battery_summary.json`.
- Portable task tests: `checks/task-tests/result.json` (90 passed); fresh patch replay and rerun: `checks/final-replay-candidate/summary.json` (90 passed, exact final generator hash).
- Large lesson census: `checks/lesson-census.summary.json` and its bound full report.
- Parametric evidence: `checks/parametric/candidate-selection/manifest.json`.
- Blind-before-repair and exposed-after-repair solves each passed 3/3 visible examples;
  both retain their exposure declarations and frozen notes.

The generator still intentionally samples only a bounded helpful subdomain of the
broader canonical geometry. The census is finite and checks declared plus shared
generic rivals; it does not prove unique induction against every possible rule.
The new alternating depth schedule was self-reviewed for a new fixed-position or
parity shortcut: colors, directions, dimensions, gaps, layout, and palettes remain
independently varied, while tests establish only the intended four-pair teaching
property rather than claiming parity is semantically meaningful.

Self-review: the repair changes no Racket transformation and no explicit override
result; it changes only invalid-call rejection, default teaching coverage, and
semantic declarations. The retained larger-near/smaller-far witness directly
checks the new lesson distinction and is covered independently by the workspace
probe and portable task tests.
