# Portable semantic probe

`probe_semantics.py` generates inputs with the current selected generator and obtains every new label through the public `arcpuzzles apply` command. Its independent flood-fill implementation is a diagnostic mirror checked against those Racket labels. The mirror is never passed off as a reference execution.

The probe dynamically reads the actual `CANONICAL_SHORTCUTS`, `SEMANTIC_RIVALS`, `LESSON_COMPETITORS`, `SEMANTIC_WITNESSES`, and `WITNESS_RIVALS` declarations. It also evaluates 29 independently written alternatives, including some outside the declared teaching bank. Names are diagnostics, not a frozen expected inventory. Each function receives copied inputs twice; mutations, nondeterminism, malformed outputs and false witness claims fail the run.

## Run from a packet

From the extracted packet root, substitute the absolute path of that packet's own Python environment:

```bash
python3 review.py run /ABSOLUTE/PACKET/WORK/.venv/bin/python3 generators/f48cc30d7943/workspace/probe_semantics.py --out ../checks/semantics/current-v1 --expect-source-sha256 CURRENT_GENERATOR_SHA256
```

The wrapper supplies Racket configuration. A normal independent checkout can instead run the script directly with NumPy, Pillow, the public CLI, and Racket available. It discovers its own library with `reviewer_support.find_root(__file__)`; it does not depend on the invocation directory, `checks/`, a previous packet, or an absolute source path. Its child process receives only this checkout's public Python source/runtime paths. A copied tests-only runtime can inspect the module, but public reference execution requires an independent library containing the catalog; the probe refuses to guess a sibling library.

The default is 58 grids: all five canonical pairs, 31 small semantic probes, four preserved design variants, and 18 production draws (seeds 0 and 17, each of the three schedule residues, across easy/medium/hard). Larger `--seeds` lists are allowed. Public reference batches never exceed 64 grids. This grid-level probe complements the separate lesson census; it does not substitute for lesson assembly or rotation checks.

Every output directory must be new. It retains exact materialized grids, original public Racket output files, command argument arrays, actual working directories, timings, exit codes, source bindings, current rival predictions and witness results. Predictions are deduplicated by full-grid SHA-256 in `predicted_outputs.json`; each case refers to its exact prediction, so every disagreement can be reconstructed without rerunning a rival. `results.json` records which cases were accepted by the teaching grammar. Small rule-lawful examples can intentionally fall outside that narrower grammar.

Bindings cover the selected generator, this probe, its support fixture, imported local helpers, public CLI/runtime entry points, the Racket prelude, and the selected canonical rows/rule. The generator hash returned by public apply must match the source loaded by this process. The task, rule hash, returned grid order, grid digests and canonical labels are checked. Files changing during a run cause failure, with earlier evidence preserved. `--expect-source-sha256` additionally binds a command to the caller's intended revision.

## Verify retained evidence

With unchanged source bytes, use a new output directory:

```bash
python3 review.py run /ABSOLUTE/PACKET/WORK/.venv/bin/python3 generators/f48cc30d7943/workspace/probe_semantics.py --verify-retained ../checks/semantics/current-v1/results.json --out ../checks/semantics/current-v1-reverified
```

This verifies retained artifact sizes/digests, checks the current source and actual declaration inventory, compares every rescored case with its exact original public Racket record, and rescores all retained Racket labels. It does **not** claim to rerun Racket. Supply the original reference-run result; chained verification receipts are rejected. A changed generator, probe, helper, canonical row, prelude or retained output is rejected; use a fresh reference run for a new revision. The command never rewrites the prior evidence.

## Preserved design comparisons

`design_variants.json` retains exact inputs, original Racket labels, geometry and source provenance from the pre-implementation independent design batch. It includes four honest comparisons:

| Variant | Observed distinction |
|---|---|
| `minimal_non8_only` | The original design had no input cyan and did not distinguish treating cyan as a wall/count/activation marker. Its nonred marker appeared only in a positive room, so marker activation also remained a correlation. |
| `minimal_positive8_only` | Adding cyan to a positive room distinguished cyan traversal/counting, but cyan and foreign-marker activation still fit. |
| `minimal_negative_markers` | Adding the same foreign marker and cyan to a visible four-red negative room distinguished both activation rivals. |
| `invalid_ah10_joins_D_E` | This was an **intentional negative geometry boundary test**, not a failed solve or an accidentally shipped sampler. At active height 10, the proposed two-red chamber and one-red chamber join into one three-red chamber. The constructive stencil therefore requires active height at least 11. |

The initial variants genuinely failed to distinguish these design rivals; they are retained as such. Their labels were correct. The negative boundary input is reference-lawful but fails the proposed five-chamber geometry. The full original design batch covered 55 grids, including 52 strengthened valid layouts, and is retained in the review evidence. This compact fixture keeps the decisive inputs and provenance with the reusable tool, without importing review-output files at runtime.

## Seed-separation lesson and the later six-chamber design

`probe_seed_separation.py` searches the selected generator for a concrete consecutive four-pair lesson that fits the alternative “fill only if the two red seeds are at most eight Manhattan steps apart” in its three demonstrations but not in its query. It then obtains Racket labels for that lesson, if found, and 46 independent constructions of the proposed six-chamber design. Those hand constructions are explicitly distinguished from production draws.

```bash
python3 review.py run /ABSOLUTE/PACKET/WORK/.venv/bin/python3 generators/f48cc30d7943/workspace/probe_seed_separation.py --out ../checks/separation-design-new --expect-source-sha256 CURRENT_GENERATOR_SHA256 --search-limit 5000
```

On the first repair candidate, source `18bd71cc3610ac4e5b34966295780d68fd89d75e36eebb6eda36a468a14fb29f`, the search found **easy, seed 31, sample indices 0–3**. Racket confirmed agreement on all three demonstrations and disagreement on 33 query cells. The old declared lesson hook returned no findings because that rival was absent from its bank. The complete lesson and alternative output are retained in `../counterexamples/seed_separation_before.json`. This was a genuine newly discovered teaching defect, not an invented failed solve. The selected generator has subsequently been strengthened; the saved lesson remains evidence about its explicitly named prior source.

`../counterexamples/seed_separation_after.json` closes that exact case on final source `b132d7379dbffedb658594771b419d949fd817319fc8b3687e5c1bc04585d595`. Public production generation accepted sample indices 0–3 without rejections. Demonstrations 1 and 2 now refute the rival, while the query input and Racket label are unchanged. The same saved four pairs have no ambiguity under any single-pair query rotation for this rival. `../counterexamples/seed_separation_minimal.json` supplies a separate Racket-checked one-row, ten-column witness with the two red seeds nine cells apart; it explicitly identifies the distinction between the reference domain and teaching grammar.

The independent design gives the open chamber red seeds at opposite ends of its top edge, at least nine Manhattan steps apart. It enumerates feasible active dimensions with `2 * active_height + active_width - 6 > max(canvas_height, canvas_width)`, which keeps a zero beyond a graph-distance cap at the larger canvas dimension. It also makes the five-red negative chamber nonrectangular and thick, and adds a three-red boundary-touching negative chamber behind a full gray separator. Those controls distinguish seed distance, graph reach, open-boundary activation and shape-label correlations together. The constructive six-chamber design has red counts 2, 4, 5, 2, 1 and 3, with original zeros in every chamber.

The targeted probe checks minimum/maximum feasible active dimensions, corner canvas shapes, all square symmetries and all six nonred/noncyan marker colors. Its source-bound result reports the selected declaration inventory dynamically. A successful hand-design check means the proposed inputs distinguish the tested rivals; a new selected-generator probe and lesson census are still needed to show the implementation emits and teaches them. A bounded search that finds no gap is reported as `not_found`, not a universal identifiability proof.

## Scope of a pass

A pass establishes successful reference execution, matching source bindings, agreement of the independent model with the retained Racket labels, valid/pure declared callables, canonical fit for the declared canonical shortcuts, truthful mapped witnesses, and at least one exercise of every declared witness. The detailed statistics report each rival's disagreements and smallest retained counterexample. An independent rival can remain indistinguishable on the finite generated sample without making this tool claim either universal coverage or a defect outside the generator's supported query domain. Check `canonical_fitting_and_sample_fitting` and the exact retained counterexamples when assessing those limits.
