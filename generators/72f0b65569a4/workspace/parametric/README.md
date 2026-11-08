# Mirror Inside the Frame: parametric prototype

**Status: proposed, unselected prototype.** This authoring tool explores two
small rule parameters for task `72f0b65569a4`. It does not change the selected
`generate(...)` interface, canonical rule, generator metadata, or approval.

## Parameters and default

| Parameter | Allowed values | Original/default | Executed effect |
|---|---|---|---|
| `axis` | `vertical`, `horizontal` | `vertical` | Reflect the column around the frame's vertical axis, or the row around its horizontal axis. |
| `output_color` | integer `7` (orange), integer `2` (red) | `7` | Paint that color at an empty reflected destination. |

The blue frame remains blue, yellow source marks remain yellow, and occupied
destinations remain unchanged. Both parameters affect the executed Racket
transformation. Colors `0`, `1`, and `4` are excluded to keep background, frame,
source marks, and newly painted cells distinct. Other output colors and other
reflection axes are unsupported rather than silently coerced.

The default emitted program is **byte-for-byte equal** to the unchanged
canonical `program_solution`, including its frame detector and iteration:

* Exact UTF-8 SHA-256: `3ca01023e0730d43844cac3ece57bfa2b777270780c3509e52b25eb23b0d7934`.
* Whitespace-normalized SHA-256: `64f526c954246fc4f1ff00ce2953d48d8d5a4f5bea10209d92db1d6103f61fcf`.

`canonical_rule.rkt` is the exact source snapshot and deliberately has no final
newline. The template performs checked, single-occurrence replacements only for
the row/column mirror coordinates and output color. `verify` checks the snapshot
against the current canonical ledger and executes every canonical pair. Every
variant is saved as exact Racket text with its own hash.

## Episode contract

Explicit/default parameter settings remain fixed for the entire episode.
`--sample-parameters` chooses the axis and color once from independent seeded
streams before any pair is generated. That option cannot be combined with
explicit parameter flags. The episode seed and final settings are retained
privately. The public challenge never contains either.

The input sampler is independent of `generator.py` and of the chosen parameter
values. No selected-generator import or changing-generator hash is needed to
reproduce its inputs. It uses only a local seeded Python `random.Random`, with
SHA-256 stream separation, and leaves process-global randomness unchanged.
This sampler is deliberately narrower than the canonical Racket program:

* One isolated complete blue rectangular frame, with a one-to-three-cell black
  exterior margin; frame dimensions range from 5 to 10, with both odd and even
  possibilities. Grids are between 7 and 16 cells in each dimension.
* Three to seven yellow marks, all strictly inside the frame; input colors are
  exactly `0`, `1`, and `4`. The selected axis is a frame-local axis.
* One interior corner mark has empty reflected targets along both candidate
  axes and an empty diagonal partner. This teaching constraint depends on the
  declared axis alternatives, not on the chosen hidden setting. The two axis
  targets differ and remain productive, distinguishing both axis and paint
  color in demonstrations.
* Consecutive draws also add occupied mirror pairs and center-axis marks, so
  retaining yellow marks and respecting occupied destinations is visible.

The same inputs are used for different parameter settings at the same seed.
Input geometry therefore does not encode the hidden parameter. Every actual
chosen output and every competing parameter prediction is obtained by
`RacketBridge.eval_text`. A strict task-local application adapter accepts only
the four exact materialized programs, removes their outer `(rule! ...)` marker,
and binds the input as `g`. Their bodies are ordinary Racket and need no other
automatic bindings or syntax normalization. The Python code constructs inputs
and scores grid equality; it has no Python transformation oracle and no fallback
if Racket fails.

Before exporting an episode, all three competing settings must be refuted by
at least one demonstration. Rival predictions and their differing demonstration
and query indices are retained privately. A rival fitting demonstrations but
disagreeing on a query would be `ambiguous`; agreement everywhere would be
`survived_all`. Export requires actual demonstration refutation of all three,
and fails visibly if that teaching constraint does not hold.

## Run from the outer extraction directory

The following commands use the included offline Racket runtime and execute
payloads from `WORK/repo/`. Output directories must be new. Use the review's
isolated interpreter for the wrapper and payload alike; plain system Python may
not have pytest installed.

```bash
review_python="$(pwd)/WORK/.venv-review/bin/python"

"$review_python" review.py run "$review_python" generators/72f0b65569a4/workspace/parametric/prototype.py verify \
  --seed 0 --seed 17 --out ../checks/parametric/suite

"$review_python" review.py run "$review_python" generators/72f0b65569a4/workspace/parametric/prototype.py episode \
  --seed 20261019 --sample-parameters --out ../checks/parametric/seeded

"$review_python" review.py run "$review_python" -m pytest -q \
  generators/72f0b65569a4/tests/test_parametric_mirror.py
```

`verify` runs a complete three-demonstration/one-query episode for every allowed
setting at every seed. It also executes the original canonical labels and a
small lawful 7-by-9 witness that separates all six pairs of parameter settings.
The `episode` command defaults to the canonical setting. To choose an explicit
alternative, use `--axis horizontal --output-color 2`. `--train` and `--test`
allow 1–8 demonstrations and 1–4 queries respectively.

In an independent repository checkout with its own Racket installation, the
equivalent payload can run with `PYTHONPATH=shared/runtime` and `RACKET_PATH`
set to that executable. The repository requires Python 3.12+; the focused tests
also require pytest 8+. The prototype has no additional third-party Python
dependencies. Dependencies must come from this checkout, and the bridge rejects
cached imports from a different tree. No predecessor or sibling import is used.

## Artifacts and reproducibility

Only **individual `public/episode-NNN.json` files** are model-visible challenges.
They contain exactly demonstration inputs/outputs and query inputs. Filenames
contain no parameter names. Share these files alone.

All other outputs are private authoring evidence:

| File | Contents |
|---|---|
| `private/episodes.json` | Fixed settings, seeds, exact programs/hashes, full labels, deterministic draw indices, and executed parameter rivals. |
| `private/rules/*.rkt` | Exact program text for every bounded setting. |
| `private/executions.jsonl` | Every actual Racket expression, input, output, and hashes; content-addressed repeat uses are explicitly counted. |
| `private/canonical_check.json` | Current canonical source identity and executed default comparisons with all canonical labels. |
| `private/witness.json` | Lawful witness, all four executed outputs, and six pairwise cell comparisons. |
| `private/receipt.json` | Actual payload argv/cwd, process exit status, seeds, counts, source and runtime hashes, executable/version, and limitations. |
| `manifest.json` | Exact file hashes for the complete evidence directory; private metadata. |
| `private/failure.json` | Exception and completed execution evidence if generation or verification fails. |

The receipt binds the prototype, exact rule snapshot, README, focused test,
Racket bridge, reviewer helper, and all local Racket prelude source
files. It separately hashes the selected Racket executable. The outer wrapper
commands and subprocess exit statuses are recorded in the review's
`WORK/checks/parametric/commands.json` and command logs when producing the retained
review evidence. Exact episode outputs are reproducible from source, parameters,
seeds, Python/Racket versions, and the recorded runtime sources.

## Scope and limitations

The first direct-run test exposed the general shared wrapper's dependency on
`scripts.comment_solutions`, a namespace available in staged production runtimes
but absent from this direct repository payload. That failed command and traceback
are retained in `WORK/checks/parametric/focused-tests.log`. The final prototype
uses the bounded application adapter above; shared runtime code remains unchanged.

The focused tests in `tests/test_parametric_mirror.py` test this prototype's
default equivalence, domain validation, deterministic sampling, actual Racket
parameter effects, occupied destinations, public/private boundary, rival scoring,
and retained artifact hashes. They are **separate from canonical repair tests**.

The examples provide bounded evidence for the retained seeds and the four
declared parameter settings. They do not establish general rule identifiability,
cover all possible random seeds, or assess arbitrary rival rules. Requiring an
asymmetric productive corner restricts the input support. The unchanged
canonical program also executes some scenes outside this one-frame grammar;
this prototype makes no new claims about those cases. Accepting a canonical
generator repair does not approve these proposed rule variants, add a production
parametric API, or admit these examples to training.
