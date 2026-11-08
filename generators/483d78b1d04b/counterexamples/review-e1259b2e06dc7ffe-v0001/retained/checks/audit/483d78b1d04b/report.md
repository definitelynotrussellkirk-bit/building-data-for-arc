# Audit: 483d78b1d04b

**Verdict: reproduced teaching and validator defects; no source edits.**
Generator SHA-256: `aea0257da4a10a3a32cebefb0674602a3631d4768922d6962058fd49baf043f5`.
Selected Racket authority: normalized hash `54c33da43b6c`; exact text SHA-256 `7cfeece8e5a39f8ccece8e460cd477c9a5188369bee8b94cd12f2a6e5d8ae4b6`.

## A483-1 — Reproduced production lesson ambiguity (P2)

Production generation at seed 6, easy, three demonstrations and one query, sample indices 0,1,2,3 with zero rejections, produces a lesson where **fill the entire inset rectangle** matches all three demonstrations but differs from the canonical outline on the query. The input dimensions are 6x10, 8x6, 9x7, and 8x9. The source intends an inset outline, so this is a meaningful nearby rival. The first three examples' size/center configurations fail to distinguish it.

The bounded direct-draw search inspected seeds 0 through 6 and stopped at the first counterexample. All four labels were then checked with the actual canonical Racket authority. A separate public `arcpuzzles generate` command reproduced the exact four inputs and labels, proving this is also an actual production episode under the stated demonstration policy. The verifier asserts demo matches `[true,true,true]`, query match `false`, source hashes, accepted indices, and zero rejections.

Evidence: `probe.py`, `probe.json`, `racket.json`, `production-seed6.jsonl`, and `verification.json`. This establishes one concrete counterexample, not a population ambiguity rate or a claim about other demonstration counts.

## A483-2 — Reproduced validator blind spot (P2)

`self_check` validates only counts of gray and non-gray nonzero cells. It accepts a 6x6 grid containing four gray cells on one row, despite the declared requirement that the four gray cells be rectangle corners. Exact input is in `probe.json` and `input.json`; `self_check` returns an empty error list. The canonical Racket runtime executes this input successfully; execution success does not establish the declared geometric precondition. This input was deliberately constructed, not claimed to be drawn by default generation.

## A483-3 — Exposed but inert overrides (P2)

`anchor_inset`, `asymmetry_force`, and `marker_offset_kind` each produced identical grids for both declared values on all 30 seed comparisons, seed 0..29 at sample index 0 and default difficulty. Static inspection explains the results: the latter two are unused, while `anchor_inset` writes an inset pixel and then clears all non-gray cells before restoring the original center pixel. Evidence is in `probe.json`; this is 90 paired comparisons, not an exhaustive distribution census.

## Strict combined check

The requested strict `--stage audit --phase audit` terminated without timeout and failed, overall exit 1. Both stages completed: task tests returned exit 5 / `no_tests`; semantic gate returned exit 2 because no semantic contract is declared. There are zero executed task tests, and lesson/rotation verdicts from that gate are unknown because it stopped at the missing-contract check. Preserve this failure: `combined/result.json`, the semantic report, and native logs/receipts. Exact commands are in `commands.json`.

## Scope and limitations

Read the assigned generator, summary/notes, canonical rule and task metadata. Ran the strict combined preset, the bounded authoring probes above, five real Racket applications (one validator counterexample plus four lesson pairs), and one production episode. No selected generator, shared code, authority, safety classification, or approval metadata was edited. No solve files were read. The task was already catalogued `unsafe` and unapproved; this audit does not change that status. No full battery, exhaustive seed sweep, or arbitrary-query-rotation census was performed.
