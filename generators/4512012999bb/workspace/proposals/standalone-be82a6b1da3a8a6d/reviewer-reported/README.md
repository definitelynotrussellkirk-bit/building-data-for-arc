# ARCpuzzles 4512012999bb: verified tie-policy proposal

This small return contains a five-file source patch, runnable prototype, focused
tests, actual Racket evidence, and a standalone checkpoint helper. It targets
the original supplied packet and preserves its production generator/rule.

**Packaging status:** independently verified proposal; normal controller intake
is blocked. The original assignment was observed as review-f41cf94e34ab02dd for
4512012999bb, but its private seed/journal was lost when the first temporary
execution session exited. No assignment was reconstructed or redrawn. There is
no INTAKE.json and no claimed completion of the two undrawn support tickets.
Do not submit this ZIP as a normal review_response_*.zip.

## Apply the source patch

Extract the original packet in a location with enough bytes and inodes. The
patch paths are relative to its WORK/repo directory. SOURCE_BINDINGS.json lists
original hashes and every expected after-hash. Check local changes before applying.

```sh
cd /path/to/original-packet/WORK/repo
git apply --check /path/to/proposal/patches/source.patch
git apply /path/to/proposal/patches/source.patch
cd ../..
python3 review.py setup
python3 review.py run python3 -B generators/4512012999bb/workspace/parametric/prototype.py --seed 17 --setting all --train 3 --test 4 --out ../checks/new-parametric
```

The patch was actually replayed on independent original files and all five
after-hashes were checked. It adds prototype.py, evidence.py, README.md and
a task-local test module, plus current notes. Full resulting source files are
also under source/ for inspection. It changes no shared runtime or canonical rule.

## What is built

The rule finds two guide columns, locates a detached pattern, compares the two
orientations by side-color matches, and places the pattern between the walls.
`direct` keeps the exact canonical behavior: equal scores keep orientation.
`mirror` mirrors on equal scores. The parameter is fixed for the whole episode.

Three default demonstrations cover a positive-score asymmetric tie and both
strict orientation directions. Four queries grow the active crop to 7x7, 8x8,
8x9 and 10x10, include odd widths, vary guide-wall colors and use narrow strict
score margins. Their active crop areas exceed all default demonstration crops.
The observed input grids range up to 16x28; no exact-30x30 coverage is claimed.

Every label and prediction is executed in Racket. Within the declared set
{direct, mirror, always-direct, always-mirror}, demonstrations uniquely select
the chosen policy, and all four query outputs are identified. This is a finite
rival claim, not uniqueness among all possible ARC programs.

Public challenges are in checks/parametric/final/public/, named by hashes of
their exact visible bytes. Only these files belong in a model-visible challenge
folder. The private sibling contains programs, settings, seed, query answers,
source hashes, predictions and certificates.

## Re-run scoped verification

From the original packet outer directory after applying the patch:

```sh
python3 review.py run python3 -B -m unittest discover -s generators/4512012999bb/tests -p test_parametric_4512012999bb.py -v
python3 review.py run python3 -B generators/4512012999bb/workspace/parametric/evidence.py --batch ../checks/new-parametric --out ../checks/new-parametric/private/replay.json
```

Both generation and replay refuse existing output paths. Replay rejects source
drift before executing labels. This needs the supplied Python3.12+/offline
Racket runtime; no labels fall back to a Python oracle. Test and replay receipts
from this work are in checks/. RESULTS.json records exact commands and exits.

## Reusable checkpoint helper

`tools/checkpoint_workspace.py` uses Python's standard library. It binds a
compact delta ZIP to the original source ZIP, retaining exact assignment/control
files, frozen baselines, source edits and evidence. Runtime/cache/temp files are
excluded explicitly. It never draws or reconstructs an assignment.

```sh
python3 tools/checkpoint_workspace.py run --workspace /ephemeral/WORK --source-zip /durable/original.zip --output /durable/checkpoint.zip -- python3 /ephemeral/review.py start
python3 tools/checkpoint_workspace.py verify --source-zip /durable/original.zip --checkpoint /durable/checkpoint.zip
python3 tools/checkpoint_workspace.py restore --source-zip /durable/original.zip --checkpoint /durable/checkpoint.zip --destination /new/WORK
python3 -B -m unittest discover -s tools -p test_checkpoint_workspace.py -v
```

Keep the wrapper alive until checkpoint success is reported. Later checkpoints
need explicit --replace. Restore writes WORK only into a new/empty directory;
copy the two outer controller files from the original ZIP and rerun setup for
the excluded Racket installation. The output must be on storage that survives
the temporary execution session; this tool does not choose or mount storage.

The helper passed 12 synthetic checks and a real 7,851-file checkpoint/verify/
restore, followed by Racket generation in the restored checkout. Regenerated
public bytes were identical. Terminating signals/host loss can prevent finally
from running; quiesce other writers. Full limits appear in the helper docstring.

## Evidence and remaining limits

- 8 prototype contract tests passed.
- 12 checkpoint contract tests passed.
- 10 independent rule cases passed (5 originals + 5 hand-built cases).
- Generation, retained-evidence replay, and restored generation each executed
  61 Racket evaluations for the same bounded two-episode seed17 batch.
- The five-file source patch passed Git application and after-hash verification.
- Production batteries were not rerun; production code is unchanged.
- Normal assignment intake and supplementary tickets remain blocked/unperformed
  because the first assignment journal could not be recovered.

No full checkout, installed environment, runtime snapshot, or original packet
is included. BUNDLE-MANIFEST.json binds every other delivered file by SHA-256.
