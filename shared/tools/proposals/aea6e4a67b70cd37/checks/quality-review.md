# Independent code review — 576426a573af

## Assessment and scope

No remaining critical or important code defect was found in the reviewed
canonical generator and separate axis/precedence prototype. Two concrete issues
were diagnosed and repaired: Q1 could report a source hash different from the
executed generator; Q2 selected the repository-shaped dependency mirror during
portable tests instead of the manifest-selected execution layout. Both Q1
regression scenarios and the Q2 dual-layout regression pass in the final
official portable result: **266 passed, zero failures/errors/skips**.

This is an independent source review, targeted execution, and inspection of the
final portable-test receipt. The 266-test run was executed by the implementation
owner and independently checked here for its result and current source hashes;
it was not redundantly rerun by this reviewer. This report does not claim the
main review's battery, production lesson census, schedule enumeration, solve,
or fresh return replay has completed. Those gates are recorded separately.

Final reviewed source identities (SHA-256), matched to
`checks/repair/final-portable-source-manifest.json`; all eight Python files also
match `checks/task-tests-portable-fixed/result.json`:

| Task-relative path | SHA-256 |
|---|---|
| `generator.py` | `d49ae2e612265752d5ce3cec5982071c6c6d96bb35183a47dff37719fd2eb0be` |
| `workspace/curriculum_probe.py` | `ee91d55a9a206aa6eb7b636b85229f1c3f2c33a6f0a297be6b162c433d7e04b5` |
| `tests/test_curriculum_probe.py` | `54c119f7200b8708b97d575313ac0f19c5bfacc46c9b5fca7aafc6e673162141` |
| `tests/test_generator_576426a573af.py` | `7443a6cf2f3ac688b0fc0611fade5a6ab4c003f689b78b1031f9a10c2aec172f` |
| `tests/test_conflict_multiplicity.py` | `7c879aca32736c35dfac5809d1bc88e91ba2edefbe87ec17bfb973f27292eb07` |
| `tests/test_morphology_support.py` | `9cbd2386882b1a62a6aef83cd650f739b590e82dab34f071452ce517a416a11f` |
| `workspace/parametric/prototype.py` | `60ac958885fb26eebf654b92e2d6e5456185afac87aa5e80cc53fe255ea3c35e` |
| `workspace/parametric/README.md` | `6f803c799e1c1faa2db89bf69cdbd33d2e7dd07f131a5dd37b25cecdb9354c08` |
| `tests/test_parametric_overlay.py` | `45ee101f32ab5f5a589fed264fe8cfb261a6a668800fdc57f5888c2aed52b406` |

## Q1 — source identity could differ from executed generator (resolved)

**Affected behavior:** the pre-fix `workspace/curriculum_probe.py` imported
`generator.py` through `SourceFileLoader.exec_module` at lines 34–37, then
computed its reported hash from the live file at line 202. CPython permits reuse
of timestamp-based bytecode when source size and timestamp match. A subsequent
source edit also left the imported module unchanged while changing the reported
hash. Either path could label an earlier execution with a newer source hash.

**Minimal reproduction performed:** copy the then-current intermediate
generator (`c36817d82d389ca28fb6398c5ef33995ce330874bcc07c7600aa4c9cb5895957`)
to a temporary directory; import it once; replace `VERSION = "2.1.0"` with
`VERSION = "2.1.9"`; restore its original timestamp; import again through the
same loader strategy under a new module name. The second module still reported
version `2.1.0`, while the current file hash was
`e4af406e6d640a25a0f05fbcc6f2c3689a62e1fb656c62e22cbeaaf6af4e55a4`.
Only temporary copies were modified. This reproduces the defect; it does not
establish that any retained review receipt was stale.

**Fix inspected:** the probe now calls
`reviewer_support.load_selected_generator(..., root=find_root(PROBE_PATH))`,
which compiles the exact hashed source bytes, respects staged-runtime selection,
and returns the selected source path and hash. The report retains that returned
hash instead of rereading the source after execution.

**Earlier regression verification actually run from `WORK/`, before Q2:**

```bash
.venv/bin/python run_with_racket.py ../.venv/bin/python -m pytest generators/576426a573af/tests/test_curriculum_probe.py -q -k hash
```

Exit status 0: **2 passed, 1 deselected**. These cases exercise a source edit
after probe import and stale same-size/same-timestamp bytecode in an independent
temporary tree. That earlier run used probe SHA
`3aa997ce1582e3dee9a2e86146fa155dffd5c34ecc8803192aedf2df039b6c10` and test SHA
`fdc55be77e2bf5f7ba033a9981c9800a033c428dab865e4a96ae370cfddc0115`.
Those two identities are **superseded by the Q2 portable fix**, not presented
as final-source results. Both cases are included in the final 266-test portable
pass at the final hashes above.

## Q2 — portable tests selected the dependency mirror (resolved)

**Observed failure:** `checks/task-tests-final/result.json` retains an actual
collection error from `test_curriculum_probe.py`, exit status 2:
`puzzle_generators.base belongs to another source tree`. This was a collection
failure, not a canonical-rule or generated-label disagreement.

**Root cause:** the shared task-test snapshot intentionally contains both
`<runtime>/puzzle_generators/` execution dependencies and identical
`<runtime>/shared/runtime/puzzle_generators/` repository-shaped mirrors. The
task-local bootstraps preferred the latter. Earlier test imports cached that
mirror, while `load_selected_generator` correctly followed `RUNTIME_MANIFEST.json`
and required the execution dependency tree. The helper's identity check exposed
the mismatch rather than silently accepting mixed layouts.

**Independent minimal reproduction:** two fresh subprocesses used the same
temporary staged layout. Importing `base` from the `shared/runtime` mirror
reproduced the exact error; importing it from the execution root succeeded and
selected generator SHA `d49ae2e612265752d5ce3cec5982071c6c6d96bb35183a47dff37719fd2eb0be`.
No helper changes, cache deletion, or guard bypass were used.

**Final delta inspected:** the three generator test modules and
`workspace/curriculum_probe.py` now prefer a local execution-layout package,
with the repository `shared/runtime` fallback. The new
`test_task_bootstraps_share_the_selected_runtime_layout` creates both layouts
and the selected-source manifest, imports the three actual test modules and
the probe in a fresh process, and asserts the concrete `base`,
`reviewer_support`, and generator source paths plus the generator hash. This
exercises the import interaction that the earlier repository-only run missed.
The shared helper and its source-tree guard are unchanged.

**Retained regression and final portable result:**

- `checks/repair/red-portable-runtime-layout.log`: the new regression failed
  before the bootstrap fix (1 failed, 3 deselected).
- `checks/task-tests-portable-fixed/result.json`: official isolated test run,
  exit status 0, **266 passed**, **0 failed**, **0 errors**, **0 skipped**.
- `checks/repair/commands.json`, entry `portable-task-tests-fixed`: exact public
  command, workspace/payload directories, exit code, and log location.
- `checks/repair/final-portable-source-manifest.json` and
  `final-portable-summary.json`: final current-file identities and the explicit
  supersession of the earlier portable failure.

The recorded public command uses `arcpuzzles check 576426a573af --stage task_tests
--timeout 600 --phase after --out ../checks/task-tests-portable-fixed` through
`run_with_racket.py`. Its selected runtime was
`/tmp/arcpuzzles-check-cezb_1w9`, where pytest ran with
`--import-mode=importlib`. This reviewer checked the result counts and matched
the final local Python bytes to that receipt. The main review's later fresh
return replay remains separate.

## Canonical delta review

The complete `generator.py` delta was compared with
`.review/baseline/repo/generators/576426a573af/generator.py`.

- `RULE_HASH` remains `892d64eecd2e`; canonical transformation and authority are
  unchanged. The source changes concern sampling, scalar validation, executable
  rivals, witnesses, and declared schedule period.
- Both conflict-bearing profiles draw 2 through `min(4, occupied - 1)` conflicts,
  leaving at least one singleton. Color assignment keeps every requested color;
  replacing an equal conflict partner cannot remove a color because its paired
  endpoint remains unchanged.
- The top source's anchored cells are connected, including sparse wide shapes.
  The conflict subset grows within that connected set; its reflected endpoints
  are consequently connected as well. Frontier selection cannot become empty
  while an unselected cell remains in that connected source.
- Reflection orbits exclude the center row of odd heights. Exact shape and
  palette overrides still control construction and bypass incompatible authentic
  anchors rather than changing requested dimensions or color counts.
- One of eight default index positions uses a canonical training geometry under
  an injective nonzero palette map; the alternate canonical role remains
  stochastic. The declared eight-index period includes this subcycle. The
  palette partition tests compare actual canonical training examples rather
  than accepting only the generator's own literal templates.
- All three declared canonical shortcuts were checked against every usable
  canonical pair, including the new count-limited rival. These are finite rival
  claims, not exhaustive identifiability claims.

### Targeted protected-Racket execution

The following exact command was run from `WORK/`, exit status 0. It checked
**32 generated inputs** at seed 47: default/easy/medium/hard, all four roles,
heights 4 and 5, width 3, and exactly six foreground colors. It also executed all
**3 canonical pairs**, for **35 rule executions** in total. The generator hash
was unchanged before and after the run. All assertions passed. The two
conflict-bearing roles produced conflict counts 2 or 4 in this small sample;
this sample does not claim to exercise count 3.

```bash
.venv/bin/python run_with_racket.py ../.venv/bin/python - <<'PY'
import hashlib, json, types
from pathlib import Path
from reviewer_support import canonical_pairs, find_root, load_selected_generator
from arc_repl.racket_bridge import RacketBridge
root = find_root(Path('generators/576426a573af/generator.py'))
gen, source_path, digest = load_selected_generator('576426a573af', root=root)
path = root/'generators/576426a573af/workspace/parametric/prototype.py'
proto = types.ModuleType('quality_review_parametric')
proto.__file__ = str(path)
exec(compile(path.read_bytes(), str(path), 'exec'), proto.__dict__)
rows = []
with RacketBridge() as bridge:
    for band in (None, 'easy', 'medium', 'hard'):
        for height in (4, 5):
            for index in range(4):
                grid = gen.generate(47, index, difficulty=band, grid_h=height, grid_w=3, fg_palette_size=6)
                assert gen.observe_overrides(grid) == {'grid_h':height,'grid_w':3,'fg_palette_size':6}
                assert gen.self_check(grid) == []
                if height % 2:
                    assert all(v == 0 for v in grid[height//2])
                conflicts = sum(grid[r][c] and grid[height-1-r][c] and grid[r][c] != grid[height-1-r][c] for r in range(height//2) for c in range(3))
                singletons = sum(bool(grid[r][c]) != bool(grid[height-1-r][c]) for r in range(height//2) for c in range(3))
                assert singletons >= 1
                if index in (1, 3):
                    assert 2 <= conflicts <= 4
                assert proto.execute_rule(proto.materialize_rule(), grid, bridge=bridge) == gen.rule_mirror(grid)
                rows.append({'band':band,'height':height,'role':gen.schedule_profile(47,index),'conflicts':conflicts,'singletons':singletons})
    canonical = canonical_pairs(gen.TASK_ID, root=root, labeled_only=True)
    for pair in canonical:
        assert proto.execute_rule(proto.materialize_rule(), pair['input'], bridge=bridge) == pair['output']
        for name, rival in gen.CANONICAL_SHORTCUTS.items():
            assert rival(pair['input']) == pair['output'], name
assert hashlib.sha256(source_path.read_bytes()).hexdigest() == digest
print(json.dumps({'generator_sha256':digest,'boundary_cases':len(rows),'seed':47,'bands':[None,'easy','medium','hard'],'indices':[0,1,2,3],'heights':[4,5],'width':3,'palette_size':6,'canonical_pairs':len(canonical),'rivals':list(gen.CANONICAL_SHORTCUTS),'racket_executions':len(rows)+len(canonical),'passed':True,'conflict_counts':sorted({r['conflicts'] for r in rows if r['role'] in ('top_only','conflict')})},sort_keys=True))
PY
```

## Prototype review

The default materialized Racket text is checked against the canonical ledger.
All four programs use the included protected `RacketBridge`; the Python mirror
is only an additional check. Settings are selected once, then reused for every
demonstration and query. The exact expression inside `rule!` is executed with
the lexical `g` binding, as documented.

The protected three-color/one-zero quartet separates both axes and both
precedences. Its positions are never overwritten by extra occupancy, so every
sampled demonstration distinguishes all four settings. The sampler key omits
the hidden setting, and query shapes cannot collide with demonstration shapes;
changing demonstration count therefore cannot trigger a query redraw through
cross-split duplicate rejection. All inputs in an episode are checked for
uniqueness, with explicit bounded failure rather than duplicate fallback.

`assess_lesson` accepts query inputs only and fits rules only to demonstration
outputs. It produces per-query refutations by demonstration index. Public files
contain only `train`/`test`, demonstration inputs/outputs, and query inputs.
Parameters, programs, output hashes, answers, and runtime evidence remain in
private files.

The retained `checks/parametric/all-settings` source hashes were compared with
the current prototype, README, and test bytes and all matched. Its four episodes
each contain two demonstrations, four queries, and six distinct inputs. All
four queries in every episode are reported identified from the demonstrations.
The retained runtime identity reports all seven security canaries passing, and
canonical parity covers three labeled examples. These artifact checks are
distinct from rerunning the already-recorded full prototype suite.

## Limits, not defects

The canonical sampler still bounds sides at 18 and conflicts at four. The
prototype deliberately forces a highly informative quartet and uses fixed
query shape slots through 30 by 30. These restrictions are explicitly disclosed;
neither finite rival rejection nor the targeted runs establish arbitrary-grid
sampling coverage, universal identifiability, or calibrated difficulty.

The documented prototype CLI executes source directly. Its importable API's
`prototype_sha256` still reads the live file at episode creation; callers who
edit the source after importing the module should not treat that value as an
independent execution attestation. This is outside the retained CLI evidence
and does not invalidate the reviewed source-matching exported episodes.
