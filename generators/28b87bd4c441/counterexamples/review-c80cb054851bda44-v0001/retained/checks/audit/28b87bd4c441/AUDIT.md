## 28b87bd4c441

**Finding — grid dimensions reveal a fixed-shape shortcut that survives the generated curriculum and fails the unchanged canonical test.** This is a teaching and canonical-coverage finding. No incorrect Racket labels or output failures within the checked generated profiles were found. The audit target and approval records were left unchanged.

### Audited identity

- Generator: `repo/generators/28b87bd4c441/generator.py`, version `2.0.0`, SHA-256 `29036f7470aca505bde6c0a0f047c9a131ab22a9a27abcd6b111d333ea6ebc2e`.
- Executed canonical rule ID: `0af5c7008ee7`; it matches the catalog.
- Executed callable text SHA-256, as returned by public `apply`: `de53f267bd26799af3ea4e32aa312f48e2ecedd51ea7819b0861e167bc3921df`.
- Canonical `program_solution` string SHA-256: `d488617f0f22d0115b860791a46ebdb0b32dd15c52cbbd12f0c2612c95addb7c`. This is a different hash convention from the executed callable text.
- Source snapshot and both authority bindings are retained in `checks/audit/28b87bd4c441/source_snapshot.py`, `checks/audit/28b87bd4c441/canonical_rule.rkt`, and `checks/audit/28b87bd4c441/source_bindings.json`.

### Concrete witness

The generator has eight scene profiles. Each fixes a distinct grid size and a single gray shape; generation changes source and marker positions, but not that shape. A rival can therefore learn one output-shape template per grid size from eight demonstrations and stamp that template at the red marker. It never examines the gray cells in the query.

The retained rival is learned from demonstration outputs in `learn_dimension_templates` and executed by `template_rival` in `checks/audit/28b87bd4c441/probe.py`. It contains no special case for the counterexample. It fits all **27 checked generated pairs** and all **3 canonical training pairs**. It fails the original canonical labeled test input, a 12×13 grid. In that input the red marker is at `(2,1)` and the gray cells are `(6,8)`, `(6,10)`, `(7,8)`, `(7,9)`, and `(7,10)`, using zero-based coordinates.

The generator's 12×13 profile always uses its `p5` shape, while the canonical test contains a different five-cell shape. Public Racket execution preserves the latter. The learned template differs at exactly two cells:

| Zero-based cell | Racket output | Template rival |
| --- | ---: | ---: |
| `(2,2)` | 0 | 5 |
| `(2,3)` | 5 | 0 |

All three tested full-profile demo sets accept the canonical query with `lesson_identifiable(demos, query) == []`. The query also receives `self_check == []` and `strict_canonical_like == []`. Public `apply --check-generator-domain` records its accepted domain verdict independently of the Racket result.

The sampling boundary is explicit: `observe_overrides` rejects this canonical query because it does not match one of the eight exact generated profiles. This finding therefore does **not** claim that the rival fails on a sampled production query. It shows that the current generated support never requires reading the query's gray shape, and the lesson hook accepts an original canonical query for which this compact demo-fitting shortcut gives the wrong answer.

### Fresh checks and limits

One public Racket application covered **31 inputs**: the 3 canonical training inputs, the canonical labeled test input, and 27 generated inputs. Generated parameters were `(seed=0, difficulty=easy)`, `(seed=17, difficulty=medium)`, and `(seed=20261020, difficulty=hard)`, each at sample indices **0–8**, without overrides. These are three stated combinations, not a seed-by-difficulty cross-product.

- **31/31** Racket outputs matched the generator's Python `rule_mirror`; all 4 retained canonical labels also matched.
- **31/31** inputs passed the generator's `self_check`.
- All 8 observable generated profiles were exercised, with 3 ordered lessons of 8 demonstrations and 1 generated query; all 3 ordered lesson hooks returned `[]`.
- The template rival fit all 27 generated pairs. Each eight-demo set also fit the 3 canonical training pairs and produced the same 2-cell canonical-test failure.
- All 3 eight-demo sets accepted the canonical test as a query through `lesson_identifiable`, despite the surviving rival.

No full battery, exhaustive seed sweep, or retained legacy task-test suite was run. The checks here are the source-pinned reproducer assertions and the public reference application; older six-test or rotation-audit results were read as inherited context and are not claimed as freshly verified. The previously retained rotation limitation remains separate and is not resolved by this audit.

### Suggested follow-up, not implemented

Break the one-to-one relation between canvas dimensions and gray shape: include at least two different lawful shapes for the same dimensions, retain the canonical five-cell test shape, and require demonstrations that refute the dimension-template rival. The source-shape copying requirement then becomes observable in the generated curriculum. This suggestion is a proposed repair direction; its wider sampling and override effects have not been tested here.

### Reproduction and evidence

Commands were invoked from `/workspace/scratch/64d6d4b955d5/review_work/WORK`; `run_with_racket.py` set the payload working directory to its `repo/` subdirectory. Each command below exited **0**:

```bash
python3 run_with_racket.py /workspace/scratch/64d6d4b955d5/review_work/WORK/.venv-review/bin/python -B ../checks/audit/28b87bd4c441/probe.py prepare
python3 run_with_racket.py /workspace/scratch/64d6d4b955d5/review_work/WORK/.venv-review/bin/python -B -m arcpuzzles apply 28b87bd4c441 --input ../checks/audit/28b87bd4c441/input.json --out ../checks/audit/28b87bd4c441/racket.json --check-generator-domain
python3 run_with_racket.py /workspace/scratch/64d6d4b955d5/review_work/WORK/.venv-review/bin/python -B ../checks/audit/28b87bd4c441/probe.py verify
```

Use the review environment's absolute Python path when relocating. `probe.py --repo PATH` can explicitly select a relocated packet repository and refuses changed generator or canonical-program bytes. The initial scaffold preparation exited 1 because it incorrectly compared the canonical program string with the executed callable hash. The hash conventions were separated, then preparation and verification succeeded; no task source changed. That failed attempt remains in the command record and is not a generator failure.

Evidence paths, relative to `WORK/`:

- `checks/audit/28b87bd4c441/audit_summary.json` — source-bound counts, profiles, hook verdicts, and differences.
- `checks/audit/28b87bd4c441/counterexample.json` — complete eight-demo lesson, canonical query, Racket answer, learned templates, and rival answer.
- `checks/audit/28b87bd4c441/input.json`, `checks/audit/28b87bd4c441/input_index.json`, and `checks/audit/28b87bd4c441/racket.json` — all 31 public applications with input provenance and source/rule hashes.
- `checks/audit/28b87bd4c441/probe.py` — preparation and assertion-based verifier; no private runner calls.
- `checks/audit/28b87bd4c441/commands.json` — exact arguments, invocation and effective working directories, exit codes, timestamps, and stdout/stderr paths, including the corrected scaffold failure.
- `checks/audit/28b87bd4c441/source_snapshot.py`, `checks/audit/28b87bd4c441/canonical_rule.rkt`, `checks/audit/28b87bd4c441/canonical_record.json`, and `checks/audit/28b87bd4c441/source_bindings.json` — minimal audited source and authority.

No target repair, source approval, or training-admission change was made.
