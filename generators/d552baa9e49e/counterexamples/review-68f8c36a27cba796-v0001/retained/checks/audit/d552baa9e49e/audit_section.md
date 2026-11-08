## d552baa9e49e

**D552-F1 — Reproduced teaching defect: a supported production start queries an undemonstrated command. Findings only; unresolved.**

Audited version `2.0.0`, generator SHA-256
`78b013356c78b80565774363b6dd3eed029b9f825c4a343325f0822c32ccbc5a`.
The canonical authority is rule `21cd1730c540`; the public Racket receipt records
callable-text SHA-256 `3ed5fa70e9361bbc394123161fe5fa092ab926161b0cd503b81adea17a39f072`.
The current source was read but not modified.

The public production command accepts seed **104729**, `sample_index=1`, medium
difficulty, and no overrides. Its default **three demonstrations and one query**
use indices `[1,2,3,4]` and command values `[2,3,1,4]`, in unchanged production
order. It records zero rejections and `lesson_check.status="not_declared"`.
Command 4's meaning is never demonstrated. A rival that exchanges commands 4
and 5 (up/down versus left/right reflection) and preserves commands 1–3 matches
**3/3 demonstration outputs** but differs on **1/1 query**. This gives two
distinct command interpretations consistent with the visible lesson.

The query's exact input is retained in `checks/audit/d552baa9e49e/finding.json`
and `input.json`; its SHA-256 is
`a7bcc955bd4e5704663295ede8dd0bdaa85af190de7493976fbbbb23afa8920a`.
The selected Racket output is `[[6,9,9],[6,6,0],[0,0,6]]`; the rival output is
`[[6,0,0],[0,6,6],[9,9,6]]`. All **four unique inputs** are direct, unmodified
production outputs. Public `arcpuzzles apply --check-generator-domain` reports
valid Racket outputs and `self_check` valid with no errors for each input.
Thus this witness lies in the documented generator domain; it does not rely
on an out-of-domain mutation or palette permutation. The rival is a
lesson-level ambiguity, not a claim that it fits the complete canonical set.

**Cause and repair direction.** `_COMMAND_BLOCKS` only guarantees a demonstrated
query command for starts aligned to four. The existing focused lesson test
only exercises `start = block * 4`. Lesson assembly should ensure every query
command has a demonstration, or reject/rebuild unsupported starts; tests should
cover every cyclic start admitted by the public API. This finding requires no
change to the Racket transformation rule.

**Reproduction and evidence.** Exact argv, working directories, and exit codes
are in `checks/audit/d552baa9e49e/commands.json`. The generation and public
Racket-apply commands both exited **0**. `production.jsonl` retains the actual
production lesson and source provenance; `racket.json` retains the independent
public authority and domain receipts; `finding.json` retains all rival outputs
and comparisons. Run the checked verifier from `WORK/`:

```bash
/workspace/scratch/f19998bd6d01/review_env/bin/python run_with_racket.py /workspace/scratch/f19998bd6d01/review_env/bin/python ../checks/audit/d552baa9e49e/reproduce.py
```

It exited **0**, meaning that the defect was successfully asserted. An initial
audit-script assertion confused raw-rule and callable-text hashes; the failed
code snapshot and traceback are preserved in `reproduce_v1_failed.py` and
`commands.json`. That probe failure is separate from the teaching defect.

**Prior lead and limits.** The unresolved D552-F1 entry from return
`review-f9811448dcb983fe:v0001`, ZIP SHA-256
`d3dc18d32cb1c93ed42cf60223a01093825ba7241e94cbbd6543feff6c209604`, was the lead.
Its source hash matches this draw. The counts above are new measurements from
one medium-band episode at seed 104729/start 1; prior census counts are not
reused. No broad frequency estimate, query-rotation check, task-test stage, or
full battery was performed. No audited generator, test, rule, notes, shared
source, or approval record was changed.
