# Count-scope parametric prototype

This is a **proposed, unapproved authoring prototype** for task
`4ca8a7b38652`. Its canonical default uses the exact registered Racket text;
the selected production generator and rule authority are unchanged.

## Fixed rule for a complete episode

The hidden episode parameter is `count_scope`, with exactly two allowed values:

| Setting | Executed scale factor | Status |
| --- | --- | --- |
| `nonzero` | Number of distinct nonzero colors | Canonical default |
| `all` | Number of all distinct colors, including zero | Proposed variant |

Both settings preserve the reasoning structure: identify distinct colors,
derive an integer scale factor, and enlarge each input cell into a square
block of that factor. The choice is made once from the episode seed and is
used for every demonstration and query. The standalone API can also receive
an explicit setting; exports require seeds consistent with their settings.

Inputs retain the selected generator's lawful 3×3 domain with 2–4 nonzero
colors. The input profile cycle covers all three color counts and both
zero-present and zero-free cases, using easy, medium, and hard layout draws.
Input generation is independent of the hidden setting. In a zero-present
input, the `all` factor is exactly one larger than the canonical factor;
zero-free inputs deliberately show the invariant region.

## Run four-query episodes

From the packet root, after `python3 review.py setup`:

```sh
python3 review.py run python3 \
  generators/4ca8a7b38652/workspace/parametric/prototype.py \
  --train 4 --test 4 --seed 0 \
  --out ../checks/parametric-v2/run
```

`--train` and `--test` are independent; each defaults to 4. For example,
`--train 6 --test 4 --seed 42` retains four queries with six demonstrations.
`--seed` starts a pair of consecutive deterministic episode seeds, producing
one complete episode for each setting. Use a fresh output directory per run.

Each count must be a positive integer and their sum must be at most 64.
One demonstration is supported because the first draw is always a zero-present
witness; the four-demo default also covers zero-free inputs and multiple
color counts. Inputs are distinct across the entire episode, including all
queries versus demonstrations. A repeated candidate is retried with the same
profile and a new deterministic draw; after 64 attempts for one requested
input, generation raises an explicit sampling error. It never clones a query
or silently returns fewer pairs. The cap is an operational prototype bound,
not proof that the domain is exhausted.

## Label authority and identifiability

Every retained label is produced by executing the exact materialized Racket
program. Both settings are executed on every episode input, and their results
are additionally compared with a Python mirror. A 4-demo / 4-query episode
therefore uses 16 protected Racket evaluations: eight for each setting.
The canonical program is read with a pinned content hash and returned without
modification. Rule files contain exactly the executed bytes, and their SHA-256
hashes cover those bytes, including any whitespace already in the authority.

Settings are fitted **only to demonstration input/output pairs**. For each
query, the private audit records all rival settings, whether each fits the
demonstrations, whether its query prediction agrees with the selected rule,
and whether the query remains ambiguous. A query is admitted only when every
demo-fitting setting agrees on its answer. Another query's label never becomes
a demonstration. This is a complete check of the two declared parameter
settings, not a claim that every possible simpler rule has been excluded.

The direct `make_episode(..., verify_racket=False)` switch exists for fast
unit tests. `write_evidence` and the CLI always request Racket verification.

## Public/private boundary

The output is split as follows:

- `public/` contains only generic challenge schemas, demonstration inputs and
  outputs, and query inputs. Pair fields are explicitly projected to this
  visible subset.
- `private/rules/` contains the exact Racket programs.
- `private/episodes/` contains full labels, hidden settings, seeds, source
  hashes, sampling counters, and per-query rival checks.
- `evidence.json` is private provenance: requested and actual counts, source
  and file hashes, rule hashes, exact Racket evaluation counts, uniqueness,
  and private maps connecting settings to public files.

Only `public/` is model-visible. Public files use
`challenge-<64-hex-visible-content-hash>.json`. The name depends exclusively on
visible demonstration inputs/outputs and query inputs under the generic
schema. Changing private parameters, seeds, reference fields, or query answers
cannot change it. Public names and directories contain no setting or seed map.

## Verification and bounded evidence

Focused tests live in `tests/test_parametric_count_scope.py` and
`tests/test_parametric_public_names.py`. They cover independent counts, fixed
settings, strict count bounds, duplicate exhaustion, demonstration-only rival
fitting, public metadata projection, opaque naming, exact file hashes, and
real Racket exports. Run the selected task's complete tests with:

```sh
python3 review.py run python3 -m pytest generators/4ca8a7b38652/tests -q
```

The review's actual commands, expected pre-fix failures, final checks,
source hashes, and bounded episodes are retained in
`WORK/checks/parametric-v2/`; the compact `implementation-receipt.json`
records their exact paths and execution counts.

This work does not establish production parametric support, approval or
training admission. It makes no large-grid, all-seed, arbitrary-count,
universal-identifiability, or measured learning-benefit claim. In particular,
zero-free demonstrations cannot select between the two settings before a
zero-present query; the audit explicitly reports such a lesson as ambiguous.
