# Current review notes: 6fde852adb54

## Decision and production scope

Assignment `review-2503c7c25983472c`, source version 4.0.0. The canonical
`training:963c33f8` rule remains `4a2e9b9f15bf` and production sampling is unchanged.
The only production edit is an early return when dimensions fall outside 14..24.
Without it, one- and two-row four-color inputs reached later row accesses and
raised `IndexError`. The intended API outcomes now hold: `self_check` reports
errors, `rule_mirror` raises `ValueError`, and `observe_overrides` returns `{}`.
Twelve frozen-baseline configurations and four actual Racket cases preserved
valid behavior; see returned `checks/parser/`.

## Teaching decision

A longest-contiguous-run landing rival fits all three canonical demonstrations,
the official query and the eight public geometries. A lawful gapped obstacle
component separates it from total-cell-count landing at six output cells.
Current production construction does not emit that distinction. Keep the
proposed witness sampler and query-aware finite-rival gate in
`workspace/questions/` until a distribution change is deliberately reviewed.
The gate rejects a surviving rival only when its query prediction differs;
query labels never participate. `QUESTION_ANSWER.md` in the return supplies the
exact grid, false-positive policy boundary and executable Racket evidence.
A finite-gate pass is not universal identifiability or measured model benefit.

## Public-evaluation focus decision

The random focus is `evaluation:d8e07eb2`, challenge SHA-256
`6dece13d6599eea896cbb0ebece1f8098a602b601f2030026d3674cc08b4155c`.
Its catalog lookup and alignment reasoning is unrelated to the selected falling
column family, so retain a separate proposed extension in
`workspace/parametric/`. Do not replace the canonical rule or infer verified
lineage, approval, training admission or measured difficulty.
The inferred default performs exact colored-glyph lookup, tests catalog row or
column completion, highlights selected tiles and sets header/footer feedback.
The parameter also supports row-only and column-only settings. Each episode
keeps one setting fixed and exposes independent demo/query counts. A default
lesson needs three demonstrations to eliminate the declared count-only rival.
The certificate executes seven explicit Racket models, with four distinct
queries in the retained exports. It identifies only that finite model family.

The proposed default agrees exactly with four of five public demonstrations.
In train[0], the supplied output substitutes the second header glyph at nine
cells while highlighting the input-selected complete row. Train[3] contradicts
a simple normalization explanation. Preserve this unresolved discrepancy;
no special case, source edit or noise verdict is warranted. Requiring a complete
line for partial aligned headers is an explicit extension assumption because
the public examples do not identify that boundary. The two public query outputs
are unscored predictions, not confirmed hidden-answer matches.

## Next useful action

Review the discrepant public header against authoritative source/context before
considering this focus extension for admission. If production sampling of the
canonical task is later expanded to gapped landing components, add a separating
demonstration and replay the query-aware gate; the current return intentionally
keeps that expansion proposed. Use the task-local CLI and source-bound receipts,
not the existence of a packaged return, as the scope of evidence.
<!-- review-f339646b581e5a8e:start -->
## 2026-10-24 — bounded robustness check for review-f339646b581e5a8e

Production source remains byte-for-byte unchanged at SHA-256 `f7a534e4c744da6f32b2576f5831721a01f71a7ec0df48694fd97c52bbd176db`, version `4.0.0`, canonical `RULE_HASH = "4a2e9b9f15bf"`. A reusable source-bound probe was added at `workspace/robustness_probe.py`. It checks invalid difficulty/override/family values, malformed short-grid public APIs, ten deterministic replays, hash-seed invariance in a fresh subprocess, all four labeled canonical Racket pairs, and five generalized Racket parity cases. The bounded run passed; fresh evidence is `checks/completion/6fde852adb54-robustness-report.json`. The matching wrapper failure is retained at `checks/completion/6fde852adb54-tests/result.json`.

The issued task-test file still blocks the fresh native task-test wrapper before collection because it resolves canonical data from the task home (`.../generators/6fde852adb54/data/canonical/...`) rather than the repository root. That test was frozen and was not edited. This is a portability defect in the issued test path, not evidence of a generator failure. The next useful repair is to make the test select its root with the public reviewer helper, then rerun the native task-test wrapper.
<!-- review-f339646b581e5a8e:end -->


## Current owner test portability

The source-bound migration now gets past the canonical-path preflight and runs
the frozen suite: 56 of 59 tests pass. Two inherited base-authority paths still
use the old fixed root, and one test expects nonempty canonical written prose
that the current row does not contain. Assertions were preserved. This is a
partial fixture repair, not a passing suite or a generator defect finding. See
`evidence/owner-test-portability/result.json` for the exact source binding.

<!-- review-6c84bc11b6ab2517:start -->
## 2026-10-24 — native landing-metric promotion work

The known count-versus-contiguous-run ambiguity is now a native two-setting
parametric family rather than an unresolved proposed question. `total_cells`
returns the exact canonical Racket bytes; `longest_vertical_run` changes only
the bottom-component column score. Inputs are matched across settings, support
2–6 demonstrations and exactly four queries, and include a substantive 30×30
surface. Three constructive demonstrations separate the settings and reject a
finite set of source-column, tie, shelf, tip and bottom-run shortcuts.

The real dependency is component discovery/metric scoring → score map and
winning landing column → body placement and optional shelf clearing. A protected
counterfactual that skips assignment and keeps body slices in their source
columns changes the retained witness output. `audit.py` also writes strict
one-query public projections whose first-turn bytes are invariant to settings,
programs, answers and future queries.

The inherited task suite had three portability-only failures: two tests reached
for repository-wide base files omitted from copied task runtimes, and one
required canonical prose stripped from the packet ledger. Those assertions now
bind the canonical program to the retained task-local source and check the
source-local rule description instead. The production generator and canonical
rule remain unchanged.

Reviewer qualification and causal witness paths are recorded in `RESULTS.json`.
They do not imply owner acceptance or training admission.
<!-- review-6c84bc11b6ab2517:end -->
