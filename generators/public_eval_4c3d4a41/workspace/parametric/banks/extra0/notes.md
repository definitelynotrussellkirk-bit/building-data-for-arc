# Current authoring state — public parent 4c3d4a41

This is unapproved public-parent creation. The authored reference reproduces both original training labels and both supplied test golds; these labels were read during development, not held out. Owner registration, source review, native qualification and acceptance remain pending. No training admission.

## General rule

Find the upright gray vessel and the separate narrower gray comb to its left. Align the comb baseline to the lowest opening in the vessel's left wall, with the first tooth aligned to the first interior lane. Each contiguous gray-cap/colored stack moves UP only by max(0, tooth height minus its empty space below). Clip cells crossing above the top aperture, erase the source comb, and copy its baseline and teeth into the vessel. A shorter tooth does not pull a stack down. Geometry and colors are read from each input; no parent examples or gold data are read at generation time.

`insert` is byte-identical to reference.rkt. `longest_survivor` first produces the inserted/clipped intermediate, then marks the longest remaining colored lane blue (1), breaking ties leftmost. The wrong-order witness ranks source colored counts instead. Source and final ranks differ in the retained witness. The canonical physical program also works on the two-lane hand-derived regression; the generated curriculum uses four to six lanes.

## Sampler and teaching repair

Independent 2–6 demonstrations and 1–4 prefix queries, with four stored distinct query inputs. Inputs match across settings. Keyed scene RNGs are distinct from the four-query presentation RNG. Capacities range from the original four-cell 8x20 apparatus to a 26-cell six-lane apparatus on an exact 30x30 grid. Source-comb baseline, frame offset, margins, palette, lane order, caps, gaps and extra lanes vary. A zero-height tooth and a fully clipped lane are explicit boundary branches. The 30x30 case has substantial structure across its height, not just a padded small scene.

Self-review found a fixed-rank shortcut in the initial sampler: the desired survivor was always the second-longest source column. A protected-Racket counterexample retains two fitting old demonstrations and a lawful edited query on which that rival fails. `regression-source-rank.json` contains both standalone programs and all labels. The repaired minimum curriculum uses original ranks two and three; another query allows rank one to win. The audit independently replays the old failure and shows the new two demos refute it. Five executable Racket rivals cover no push, pushing by full tooth height, and choosing the first/second/third source rank; the wider bounded Python rival set also covers reverse teeth, top packing, fill-to-capacity, retained keys, position/color selectors and mark-all.

## Public boundary and tools

`public_turn` requires a complete four-query private bank, shuffles it independently before projection, and whitelists exactly the visible demonstrations and one query input. No query count, setting, seed, future input or query answer is exposed. The entire export directory and private presentation mapping remain controller-only. `public_export.py` validates all visible payloads before writing, rejects duplicates and existing destinations, physically writes in sorted content-ID order, and checks exact canonical serialization and tampering. An I/O interruption is not an atomic batch guarantee; use a new destination after failure.

The ordinary generator returns inputs. `self_check` returns [] for a valid apparatus and descriptive findings for an invalid one, without mutation. Its scope is the explicit structural grammar, not exhaustive support membership. Native resources and imports are task-local; runtime helpers are supplied by the packet.

## Reproduce and limits

Use the three commands in workspace/parametric/README.md. Current retained receipts are checks/public_eval_4c3d4a41/preflight/ and audit/. Earlier preflight evidence predates the boundary/teaching/export repairs and is superseded. Tests include the official labels, an independent literal mechanical fixture, counts/prefixes, rank variation, protected rival execution, privacy, publication order, stale hashes and symlink rejection.

This grammar has one upright vessel, one left-side comb, alternating lane spacing, one source color per lane, and optional gray caps. It does not claim arbitrary rotations or unrelated overlapping apparatus. All uniqueness claims are limited to declared finite rivals and executed seeds. Final review is author self-review, not an independent reviewer.
