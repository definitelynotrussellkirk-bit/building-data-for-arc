# Reviewer solve loop and tracker

For generator improvements and these solve exercises, send
`var/review/SEND-THIS-ARCpuzzles-review.zip`. The separate
`var/review/SEND-THIS-ARC2-loop-review.zip` reviews the model/harness/training
process through random tickets; [ARC2train owns that workflow](https://github.com/definitelynotrussellkirk-bit/ARC2train/blob/main/docs/harness-review.md).
New packets first require a separate approved-task solve **before** opening any
repair/reference material. Draw with `python3 assignment.py`, then follow the
blind task in `DUTIES.md`:

```sh
python3 solve_episode.py blind prepare
# Read solve-blind/challenge.json; edit its solution.py and SOLVE_NOTES.md.
python3 solve_episode.py blind check --intent solve --note 'Hypothesis and revision'
python3 solve_episode.py blind finish --earlier-exposure no --reference-consulted no --reason 'Why I stopped'
```

Use the truthful exposure value if the task is already familiar. A blocked blind
task stays untouched; retain its reason and continue the repair assignment.
References remain in the library, so this relies on honest nonconsultation.
The two solve kinds retain distinct records and exposure metadata in the feed.
Earlier packets with only the post-repair solve remain supported.

After improving the assigned generator, the reviewer prepares a fresh episode,
tries to infer its transformation from visible examples, and submits Python
`solve(grid)` revisions. During this solve they **must not consult the Racket
rule**, generator implementation, reference solutions, private labels, or prior
solution explanations. Earlier exposure during generator work is recorded; this
is a rule-informed exercise rather than evidence of a blind held-out solve.

From an extracted packet root:

```sh
python3 solve_episode.py prepare
# Read solve/challenge.json, edit solve/solution.py and solve/SOLVE_NOTES.md.
python3 solve_episode.py check --note 'Hypothesis, probe, and reason for this revision'
python3 solve_episode.py finish --earlier-exposure yes --reference-consulted no --reason 'Why I stopped'
python3 package_return.py
```

Preparation uses at least three demonstrations, honoring a generator's literal
`EXAMPLES_NEEDED` minimum (up to 32), and two masked queries, with a reproducible
32-bit seed derived from the assignment ID and revised generator hash. Generation
uses the actual Racket reference. Only the public challenge enters `solve/`;
labels remain in `.review/solve-private/`, which is omitted from the return.
The Python worker receives public inputs only. The controller reports visible
pass counts and execution feedback; masked-query scores stay private until
independent maintainer scoring after return. This preserves the information
available during test-time solving. Private local score receipts stay under
`.review/solve-private/` and are omitted from the return. This is a workflow
boundary, not a sandbox preventing a reviewer from reading other packet files.
The exact demonstration count is recorded in the hashed episode and preparation
configuration. This count alone does not certify lesson identifiability: the
preparation record explicitly says that the assembled lesson hook was not checked.

Every check retains the program, work-log snapshot, revision note, execution
output and visible-check receipt under `solve/attempts/NNNN/`. Wrong programs, timeouts,
and errors remain. Generation failures can be returned as blocked; rerunning
prepare after a generator repair preserves failure receipts. A finished solve
cannot be overwritten. Hashes bind both the generator source and the ordered
public episode; hidden-answer changes do not change the instance hash.

Each new revision records `attempt_intent`: `solve` (default),
`teaching_negative`, `diagnostic_probe`, or `unknown`. Set it with the check
command's `--intent` flag. Preserve actual attempts; do not manufacture a wrong
route to fill a preference pair. Older records without this declaration remain
`unknown`. The tracker and exported feed carry the declaration independently of
the correctness label. Reviewer programs and work logs are not captured Qwen
conversations; a successful replay does not establish eligibility for DPO.

## Maintainer intake

```sh
PYTHONPATH=src python3 -m arcpuzzles review collect /path/to/returns
# Inspect changed code, then construct/check the isolated candidate:
PYTHONPATH=src python3 -m arcpuzzles review check review-ASSIGNMENT --version 1
PYTHONPATH=src python3 -m arcpuzzles review solve-check review-ASSIGNMENT --version 1
```

`collect` and `inbox` rebuild **`var/review/solves/index.html`**. This tracker links
each generator/instance, Python revision and work log, with reference-consultation
declarations, visible feedback, and independent replay results. Private answers
are absent. All attempts initially have `label=unknown`; a visible failure is
also recorded as the reviewer's local `reported_label=bad`. `solve-check`
regenerates the hash-bound episode from the applied candidate and independently
scores each revision before assigning `good` or `bad`. Failed generator quality
checks remain separate from solution correctness and training admission.

The tracker also emits `questions.jsonl`, `attempts.jsonl`, `summary.json` and a
hashed `manifest.json`. A self-contained feed lives at
`var/review/solves/export/reviewer-solves.zip` for import into ARC2train's question
bank. It contains public questions, program revisions, notes, execution receipts,
and provenance; it contains no private answer grids. The `feedback_policy`
field distinguishes new visible-only attempts from older private-feedback
captures. It is a maintainer export,
not another reviewer packet. No record is automatically training-admitted.

Useful authored solves, revisions and source-bound evidence live with their
generator, so later packets can reuse them without the transport archive.
Current notes, actionable audits and minimal witnesses survive verified
compaction; processed return ZIPs and redundant history do not. Keep a source
packet while reviewers still need it. See [the retention gate](../../docs/placement.md#generator-notes-and-review-retention).

The solve CLI prints a fixed allowlist of public scalar status fields. Generation
provenance, rival names, private-label hashes and new nested fields stay in retained
records. This is a display boundary, not a filesystem sandbox; earlier exposure
declarations are preserved and passing visible examples does not erase exposure.
