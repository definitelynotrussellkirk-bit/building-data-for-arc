# Read-only audit: generic_panel_dress_gen1

**Status: measured lesson ambiguity against a reading-order rival.** An
ordinary `generate_task(14, difficulty="easy")` episode has two demonstrations
that fit both hole-count matching and positional matching, followed by two
queries on which the rules disagree by **72 cells each**. All four stored
generator outputs match the unchanged emitted Racket program. This finding
concerns demonstration discrimination, not incorrect reference labels.

## Source identity

* Assigned/current generator SHA-256:
  `4d334d35eb30d0b798220259917fa2e082b8b6834152cd826b376640e4fbf64d`.
* Source: `repo/generators/generic_panel_dress_gen1/generator.py`, generic kind,
  version `1.0.0`.
* Exact unchanged emitted PROGRAM SHA-256:
  `a259e40d3dc9887618c3893272cda6f2af63ed2e89357eb6e3ba0b85cadca5a5`.
* Exact positional Racket rival SHA-256:
  `1ce8db1c527a63ec37341f4803b9a7832ca4c6d31e9215df56fd8e9b01f38142`.

The source hash was checked before and after the probe and remained unchanged.
No audited generator, shared runtime, catalog, or approval record was modified.

## Confirmed counterexample

The intended rule assigns each panel the loose shape whose enclosed hole count
matches that panel's enclosed dot count. The competing rule instead pairs the
first panel with the first loose shape in component reading order, the second
with the second, and so on. It keeps the same panel detection, filling,
centering, shape colors, and shape pasting. Its only changed selection is:

```racket
(shp (list-ref shapes (index-of panels pan)))
```

The rival was specified before screening. It is a fixed positional shortcut,
not a rule constructed from query answers. The Python screen examined seeds
0 through 14 and stopped at seed 14. Screening predictions were then replaced
by actual Racket results for the complete selected episode.

| Pair | Input dimensions | Output dimensions | Cells differing between actual Racket rules |
|---|---|---|---|
| Train 0 | 26×28 | 8×16 | 0 |
| Train 1 | 30×24 | 14×7 | 0 |
| Test 0 | 30×24 | 16×8 | 72 |
| Test 1 | 30×24 | 16×8 | 72 |

At zero-based coordinate `(1, 1)`, Test 0 has intended color 3 versus rival color
4; Test 1 has intended color 5 versus rival color 2. `probe.json` retains the
exact full episode, both actual output grids for every pair, executed Racket
expressions, and hashes. `query_differences.json` lists every differing cell.

## Execution and scope

The probe made **8 actual Racket calls**: both programs on each of two train and
two test pairs. All four stored outputs matched the emitted reference. Both
Racket programs agreed on both demonstrations and disagreed on both queries.
The selected complete task was deterministic on regeneration; the screen also
recorded unchanged process-global Python RNG state.

The command exited **0** because the audit completed. Its semantic verdict is
**`lesson_ambiguity`**, not a clean-generator result. Source/notes/API inspection
found no task tests in the generator home and no substantive current notes.

Reproduce from the outer extraction directory:

```bash
audit_python="$(pwd)/WORK/.venv-review/bin/python"
"$audit_python" review.py run "$audit_python" \
  ../checks/audit/generic_panel_dress_gen1/probe.py --max-seeds 64
```

`commands.json` retains fully expanded argv, `cwd: packet_root`, actual outer
and payload working directories, exit code, elapsed time, evidence paths, and
log/reproducer hashes. The script imports the selected task from this checkout
and refuses changed source bytes. It creates no copied runtime. The direct
bridge adapter removes only the emitted `(rule! ...)` marker and applies its
ordinary Racket lambda to the exact input; both programs use the same path.

## Follow-up and limitations

Add an episode-level teaching check requiring a demonstration that refutes
reading-order matching before a query depends on distinguishing that shortcut.
Retain the seed-14 episode as a focused regression. More demonstrations alone
do not prove that a particular lesson teaches the required distinction.

This is one confirmed ordinary easy-episode counterexample, found by screening
15 seeds. No full battery, large census, medium/hard parity batch, or public
export was run. No ambiguity frequency or general identifiability claim is
made. Public export train/test-count requests may filter or truncate generic
tasks; this finding identifies the actual complete two-demo/two-query task from
`generate_task`, not an independently checked default export invocation.

Execution was temporarily delayed twice by workspace inode exhaustion. No audit
runtime copies were created, and the Racket child exited before evidence writing
resumed. All files in this directory are private authoring evidence, not public
model challenges. No approval or training-admission label was changed.
