# Layer Histogram Strip: proposed parametric prototype

**Status: proposed prototype, not production approved.** This is an isolated
authoring experiment. It does not alter `generator.py`, the canonical rule,
approval hashes, catalogs, shared runtime interfaces, or training admission.

## Bounded rule

One hidden episode parameter, `output_order`, has exactly two allowed values:

| Value | Executed transformation | Authority |
| --- | --- | --- |
| `outer_to_inner` | Cardinally peel the mask excluding colors 0 and 9; output the exact counts of successive removed shells from outside inward. | Original/default: exact canonical Racket bytes. |
| `inner_to_outer` | Perform the same peeling and counting, then reverse the histogram strip. | Proposed alternative: only the final histogram expression changes. |

These are exact shell counts, rather than cumulative populations surviving
erosion. A radius-two solid Manhattan diamond has output `[[8, 4, 1]]` by
default and `[[1, 4, 8]]` under the alternative. Both outputs are executed with
the included Racket runtime; the Python authoring code has no histogram mirror.

The deterministic parameter draw is `random.Random(seed).choice(ORDERS)`, once
per episode. Seed **1** chooses the original; seed **0** chooses the alternative.
A separate seed-derived stream chooses dimensions, interior translation, and
one shape color in 1..8 for all input draws. No input constraint depends on
the selected parameter.

Each episode has two demonstrations (a five-cell plus and a filled 3x3 square)
and one query (a radius-two diamond). The two demonstration histograms are
non-palindromic, so each demonstration distinguishes both declared settings.
The retained rival checks execute both programs on every demo and query and
require exactly the selected setting to survive the demonstrations. This checks
the bounded two-setting family; it does not establish uniqueness among all
possible rules.

## Run and verify

From the extracted review directory
`/workspace/scratch/df43994906e4/arcpuzzles_review`, the exact command is:

```bash
/workspace/scratch/df43994906e4/arcpuzzles_review/WORK/.venv/bin/python review.py run /workspace/scratch/df43994906e4/arcpuzzles_review/WORK/.venv/bin/python generators/12ace26107fd/workspace/parametric/prototype.py --seeds 1 0 --out ../checks/parametric/episodes-final
```

Focused prototype tests:

```bash
/workspace/scratch/df43994906e4/arcpuzzles_review/WORK/.venv/bin/python review.py run /workspace/scratch/df43994906e4/arcpuzzles_review/WORK/.venv/bin/python -m pytest generators/12ace26107fd/tests/test_parametric.py -q
```

After relocation, replace the absolute interpreter paths with the new
extraction's absolute `WORK/.venv/bin/python` (or an equivalently provisioned
interpreter). `review.py run` always sets the payload cwd to `WORK/repo` and
selects the included Racket. Python 3.12+, NumPy, Pillow, and pytest for testing
are the packet's declared dependencies. No predecessor checkout or sibling
environment is imported.

`prototype.py` uses the supported `RacketBridge` and `wrap_rule`. The packet's
direct `shared/runtime` import path does not include the mapped `scripts`
package required by `wrap_rule`. If needed, the prototype uses public
`prepare_runtime(Catalog(ROOT), temporary_directory, TASK_ID)` to prepare the
ordinary portable runtime layout and resolve that dependency. This temporary
copy is a local execution dependency, not retained evidence or an alternative
rule authority.

Tree and canonical-data discovery use `reviewer_support.find_root` and
`canonical_path`; canonical example checks use `canonical_pairs`. Tests locate
the selected generator with `load_selected_generator`. In copied execution
trees, workspace and provenance paths resolve through `RUNTIME_MANIFEST.json`
entries (`library_path` to `runtime_path`), including `task_workspaces/` layouts.
No fixed ancestor count or assumed `shared/` source layout is used. The private
manifest records both stable source identities and actual copied source paths.

The official isolated task-test command is:

```bash
/workspace/scratch/df43994906e4/arcpuzzles_review/WORK/.venv/bin/python review.py check --stage task_tests --phase after --timeout 600 --out ../checks/task-tests-final
```

## Files and information boundary

The command writes:

- `public/episode-000.json` and `episode-001.json`: only demonstration pairs
  and query inputs. These are the only files intended for model-visible use.
  They contain no hidden parameter, seed, metadata, reference code, or query
  answer. Their filenames identify only episode sequence.
- `private/episode-*.json`: parameter seed/value, matching Racket program and
  hash, query answers, all declared rival predictions, and exact Racket
  application expressions with executed outputs.
- `rules/outer_to_inner.rkt` and `inner_to_outer.rkt`: exact program bytes,
  without an appended newline; hashes are in the private manifest.
- `private/shared-witness.json`: one common lawful input and both executed
  outputs, plus the exact expressions sent to Racket.
- `private/canonical-checks.json`: default-rule execution on all three
  canonical example pairs and exact expected/actual outputs.
- `private/manifest.json`: prototype status, source SHA-256 values, normalized
  canonical-record SHA-256, program hashes, runtime identity, invocation, seeds,
  and explicit limits.

All `private/`, `rules/`, manifests, source, and execution logs are evaluator
material. Never attach them to the public challenge directory.

## Evidence and limits

Retained authoring evidence is under `WORK/checks/parametric/`. Its
`commands.json` records the actual invocations, cwd, exit codes, and log paths.
The final source-bound materialization is `episodes-final/`; earlier `episodes/`
records retain their original source hashes and are not silently refreshed.
Tests cover exact default preservation, canonical examples, the contrasting
shared input, deterministic full episodes for both settings, rival rejection,
parameter validation, manifest-based source lookup, and challenge
privacy/materialization.

This input sampler intentionally has only three connected, hole-free shape
templates. Translation, size of the surrounding canvas, and color vary, but
there is no broad distribution or all-seed claim. All sampled shell counts are
ARC digits 0..9, all inputs have zero background and one non-0/non-9 shape,
and no output clipping or modulo encoding is performed. Larger or arbitrary
polyomino support is outside this prototype. Runtime evidence is limited to
the retained seeds and tests, separately from canonical repair coverage.
