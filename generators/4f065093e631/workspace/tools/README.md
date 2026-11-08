# Independent parametric bundle verification

`verify_parametric_bundle.py` checks an authoring bundle independently of the
generator that produced it. It is task-local to keep this review's patch scope
small, but has no hard-coded task, policy, seed, grid size, or expected answer.
Another one-parameter family can reuse it with the manifest contract below.

From the outer packet directory, using the environment created for this review:

```bash
WORK/.venv/bin/python review.py run \
  /absolute/path/to/WORK/.venv/bin/python \
  generators/4f065093e631/workspace/tools/verify_parametric_bundle.py \
  ../checks/parametric/final/evidence.json --root . \
  --execute --require-identified --require-rotations \
  --out ../checks/tooling/parametric-verification.json
```

Use a new output path for each run. Omitting `--execute` performs only structural
and content-hash checks and records execution/ambiguity as untested. Execution
uses the included protected Racket bridge, never the generator's Python mirror.
Supported programs are explicit, self-contained `(rule! (lambda (g) ...))`
expressions in ordinary Racket with the bridge prelude. DSL shorthand and free
implicit `h`/`w` bindings are outside this tool's declared contract; an unsupported
program fails rather than being silently translated through a different runtime.

## Manifest contract

- `task_id`: family identity; `parameter_name`: the one fixed episode parameter.
- `source_hashes`: source-root-relative POSIX paths mapped to SHA-256 of bytes.
- `programs`: setting names mapped to `{text, sha256}`. Program hash is exact
  UTF-8 text, not a whitespace-normalized semantic hash. At least two settings.
- `episodes`: each has unique `id`, `parameters` including the fixed setting, and
  `pairs` with unique `id`, `role` (`train` or `test`), `input`, `output`,
  `input_sha256`, `output_sha256`. At least one demonstration and one query.
- Grid hashes use `json.dumps(grid, sort_keys=True, separators=(",", ":"))`.
- `public_challenges`: exactly one `{episode_id, path, sha256}` per episode;
  paths are relative to the manifest's directory.

The manifest and executed query labels are **private authoring evidence**. Public
JSON must equal the exact projection `{train: [{input, output}, ...],
test: [{input}, ...]}`. Extra keys, including hidden parameter values, reference
code, private hints or query outputs, fail verification even if someone refreshes
the public file's hash afterward. Every source, program, input, output and public
file is content-bound. Structural failures prevent any program execution.

## What the receipt establishes

Every declared setting is run on every saved input. Labels are checked against
the episode's selected setting. Rival matches and ambiguities are recomputed;
claims in the input manifest's `rivals` field are not trusted. A production
ambiguity means a different setting fits all demonstrations and disagrees on at
least one query. A rotation ambiguity means it fits every other saved pair but
disagrees on the pair held out. A rival that agrees everywhere is distinguished
from an ambiguous prediction. `--require-identified` additionally requires every
alternative setting to be refuted by the demonstrations, even if it happens to
agree on that particular query.

Counts are setting/input executions, episode/rival production ambiguities, and
episode/rival/held-out-pair rotation ambiguities. They are finite evidence against
the declared parameter rivals. They do not establish unique induction against all
possible programs, canonical generator coverage, variant approval, or training
admission. Unit tests deliberately corrupt labels, hashes and public projections,
construct an unteaching episode, and run a small genuine Racket integration case.
