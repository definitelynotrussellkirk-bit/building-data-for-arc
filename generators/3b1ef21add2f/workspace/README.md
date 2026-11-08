# Reusable local-window authoring probe

`probe_local_windows.py` checks the local operator independently of the sampler.
It executes the selected public Racket authority on 529 inputs: all 512 binary
3×3 masks in a black 5×5 canvas, 14 targeted cases, and the three canonical
labelled inputs. Targeted cases cover boundaries, overlapping windows, attached
red cells, unequal window-bearing components, and nonred squares.

From the review packet's WORK directory, with its prepared Python/Racket runtime:

```sh
.venv/bin/python3 run_with_racket.py "$PWD/.venv/bin/python3" \
  generators/3b1ef21add2f/workspace/probe_local_windows.py \
  --out ../checks/local-windows/NEW_RUN \
  --expected-generator-sha FINAL_GENERATOR_SHA256 \
  --expected-rule-hash 200a2c36d86e
```

The wrapper changes the payload working directory to `repo`; the quoted `$PWD`
therefore resolves the interpreter to its absolute path before that change.
The exact successful command for this review is retained in
`checks/local-windows/commands.json`. The output path must be new. Optionally
pass `--counterexamples generators/3b1ef21add2f/counterexamples/local-window-witnesses.json`
to refresh the current compact witness inventory without overwriting run history.

The probe uses public `arcpuzzles apply` in batches of at most 64. It binds
results to generator and rule hashes, preserves raw responses, and aborts if
source identity changes. It scores the actual `CANONICAL_SHORTCUTS`,
`LESSON_COMPETITORS`, and `SEMANTIC_RIVALS` declarations with namespaces intact.
Claimed canonical shortcuts are checked against every labelled canonical pair.

The independent snapshot oracle is diagnostic, never a replacement source of
exported labels. Validator acceptance, unique inputs, oracle equality, and rival
disagreement are separate measurements. This finite local space cannot expose
every global-selection shortcut: all windows of a 3×3 mask share its center.
The unequal-component targeted case is therefore essential. A ring also
distinguishes a red-graph cycle heuristic from membership in a red 2×2 window.

Whole-lesson teaching claims require the public lesson census, including every
query rotation and all three schedule starts; individual input witnesses alone
do not establish those claims. The review return retains those separate results.
