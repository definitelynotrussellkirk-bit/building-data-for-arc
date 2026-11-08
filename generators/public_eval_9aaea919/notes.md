# public_eval_9aaea919 — implemented rule and handoff

Canonical rule: identify bottom command bars (red=donor, green=receiver),
count isolated objects in aligned stacks, gray every donor object, erase bars,
and add sum(donor counts) receiver-shaped copies above the receiver's stack.
Infer background, stack locations, receiver geometry and vertical pitch from
input. Preserve neutral stacks and color roles even when body colors are 2/3.
Alternative `aggregation=maximum` adds only the largest donor count; otherwise
uses the identical parse and render stages. Both settings share generated inputs.

Implementation order: tests RED; self-contained generator and exact Racket
reference; adapter with a byte-identical task-local generator copy; independent
Python/Racket parity and shortcut attacks; privacy exporter; official authoring
preflight and protected wrong-count witness. No owner approval or training claim.
Two demonstrations deliberately contain unequal donors; four queries are stored
privately and shuffled before single-query presentation. Counts support 2–6 demos
and 1–4 queries with prefix stability. Source index is not presentation order.

Limits: a single green receiver, at least one red donor, upright uniform-pitch
stacks of congruent connected masks, common baseline and one-row bars. Generated
scenes vary masks, widths, colors, positions, counts, background and margins.
No source lookup or original-answer cache is used by either generator or rule.


## Executed checks and current handoff

The final source is bound by `checks/public_eval_9aaea919/preflight-final/preflight.json` and
its sibling execution/original-pair records. Reusable `audit.py` checks the
binding before running protected labels, named shortcut rules and private-field
invariance. `checks/verify_final_witnesses.py` invokes the official schema
validator and replay engine; the invocation is explicitly reviewer-only.

Both settings have matched inputs, independently selected 2–6 demos and 1–4
queries, and a retained four-query controller bank. Public presentation shuffles
that bank with a separate presentation seed and returns one query per view. Never
expose the view list, its length, source indices or private presentation sidecar
to a solver. Saved filenames and emission order derive only from visible content.

The standalone generator declares literal `RULE_public_eval_9aaea919_ID = 'ee_9aaea919'`. Its source is
copied byte-for-byte into the native resource-local `family.py`; a test enforces
this equality. This intentionally small duplication avoids hidden deployment
imports. Ordinary generator calls support `generate(seed, sample_index)` and
strict keyword difficulty/override validation. Difficulty currently does not
change the generated domain; no effect is claimed for it.

The owner should integrate the task-local delta, preserve/reconcile any parallel
branches, verify originals, register the `ee_` reference, approve source, refresh
the native manifest, and run qualification plus acceptance. The disposable-copy
smoke tool rehearsed unapproved registration, ordinary protected generation and
the official staged tests without changing the actual catalogs. No approvals,
acceptance records or training data are produced by this return.

Final checks: 46/46 staged tests; 4/4 original protected labels; 36 audit episodes,
276 label claims, 61 protected executions, 432 rival checks, 16 saved public
views, zero findings. Separate census: 1,010 unique valid deterministic inputs,
all 1,010 setting-separated. Wrong transfer count changes 21 cells on the 30×30
query. Larger donors deliberately switch left/right order between minimal demos;
receiver pitch differs, refuting first/last-donor and fixed-pitch shortcuts.

Review limits: self-review by the author, no independent reviewer available.
Finite named rivals and sampled seeds do not prove universal uniqueness or
correctness outside the documented grammar. The complete family test directories
pass together using pytest `--import-mode=importlib`, as the official staged
runner does; default combined collection collides on the shared test basename.

## Current private repeated-parent reconciliation

Retain exact sum/maximum current programs and both constructors; add exact incoming balanced and broadcast programs. Two matched demonstrations bridge one- and multi-receiver domains to distinguish balanced from sum. Query bank uses one constructor per seed, alternating banks. Generalized Python mirror follows retained Racket first-receiver semantics on multi-receiver inputs. No single-receiver intersection imposed. Candidate native qualification and fresh acceptance were exercised in this isolated library; root publication remains separate. See evidence/repeat-next-union and the current private qualification receipt.
