# Review — assignment `review-384ba30ff2bc508b`

Both assigned public-evaluation homes now contain reviewer-ready, source-bound two-setting families.
`public_eval_981571dc`: retained the existing canonical closure family, repaired copied-runtime path discovery, and added portable self-audit/test entry points.
`public_eval_97d7923e`: authored the missing generator, general Racket rule, native adapter, finite-rival audit, public exporter, and causal witness.
Both authoring preflights passed; this is not owner registration, native qualification, acceptance, or training admission.
Final copied-runtime tests: 41/41 and 39/39; combined direct run: 80/80.
Bounded audits: 130 and 128 episodes, 64 protected-Racket label executions each, and 16 valid one-query public exports each.
Both deliberately answer-leaking exports were rejected by the standalone saved-file checker.
A clean extraction accepted the 14-path patch, matched every patched file byte-for-byte, and passed the combined 80-test suite.
Protected-Racket causal replays changed 1 and 5 cells, respectively.
Remaining limit: finite rival suites establish bounded separation only, not universal identifiability.

## `public_eval_981571dc` — transpose repair before suffix-mirror closure

The canonical `closure` program first repairs zeros whose transpose partner is visible, then closes remaining zeros under the row/column suffix mirrors that leave indices 0 and 1 fixed. The alternate `transpose_only` setting stops after the first stage.

The retained chain-mask witness removes a target and all of its original suffix-mirror donors while leaving transpose partners that Stage A can recover. Stage B therefore must consume the Stage-A grid; reading the original input leaves one cell incorrect. The protected replay is retained at `checks/public_eval_981571dc/causal/`.

The production generator, reference rule, adapter, engine, and canonical Racket bytes were preserved. The concrete repair was portability: the staged copied runtime did not satisfy the old ancestor-search heuristic. Test and audit roots are now derived from their stable task-relative locations. The second task uses a task-specific test basename, so it collects safely beside this frozen baseline test module in one pytest process.

Evidence:
- `checks/public_eval_981571dc/preflight/`
- `checks/public_eval_981571dc/audit/audit.json`
- `checks/public_eval_981571dc/causal/`
- `checks/public_eval_981571dc-tests-final/`
- `checks/public-exports/public_eval_981571dc.json`

## `public_eval_97d7923e` — ranked wire recoloring before relay selection

The authored parent rule reads each top-row monochromatic run as a one-based rank. For color `c`, a run of length `k` selects the `k`-th longest vertical wire whose endpoints are `c` and whose nonzero interior is a uniform different color; that interior is recolored to `c`. The rule reproduces all three supplied demonstrations and the private test gold through protected Racket.

The canonical `rank_only` setting performs that transformation. The alternate `selected_longest` setting then compares the lengths of the wires actually selected by Stage A and activates the matching horizontal `c,9...,9,c` relay. Generation constructively makes the color owning the longest raw candidate differ from the color owning the longest selected wire. The retained wrong-intermediate program uses raw candidates, picks color 8 instead of 4, and changes five cells.

The family supports 2–6 demonstrations and a private, prefix-stable bank of exactly four distinct queries. Inputs are matched across settings; the fourth query is 30×30. Eighteen declared rival policies are checked over 64 seeds. Its task-specific test basename prevents collision with the first task’s frozen `test_family.py` module.

Evidence:
- `checks/public_eval_97d7923e/preflight/`
- `checks/public_eval_97d7923e/audit/audit.json`
- `checks/public_eval_97d7923e/causal/`
- `checks/public_eval_97d7923e-tests-final/`
- `checks/public-exports/public_eval_97d7923e.json`

## Cross-task checks and limitations

The combined test run is retained in `checks/combined/`; it caught and motivated the test-module basename repair. A separate fresh-packet replay is retained in `checks/clean-replay.json` and `checks/clean-replay-pytest.*`. All ten task Python files parsed successfully. Saved public exports were independently checked without loading generators, private receipts, programs, or the Racket runtime. The source-bound inventories, preflight receipts, and causal witnesses all refer to the final renamed test paths.

Final review was an author self-review because no independent fresh-context reviewer was available. The owner still must register each public family, review exact source/provenance, run unchanged native qualification, and explicitly accept it before any training admission.
