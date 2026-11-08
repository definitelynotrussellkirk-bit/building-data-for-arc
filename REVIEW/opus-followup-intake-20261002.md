# Claude follow-up intake — October 2, 2026

Received `var/review/external/opus-followup-20261002/Opus-ARC2-followup-return.zip`:
1,700,586 bytes, SHA-256
`482bd964ae02f541bdd329515c0dc02e6dacfedec0fa1c357e0d238d337f7610`.
All 33 manifest-bound files verified. Original archive bytes remain unchanged.
This is a new follow-up to the earlier Opus review and reviewer round a371;
those two older returns are separately retained.

## Applied packet changes

All five proposed packet patches applied to source `49f81f70` in an isolated
owner worktree, then were checked and applied to the owner. They add canonical application, retained/resumable generation,
clearer battery messages, a separate unexposed solve assignment, and bundled
check evidence. Review found additional corrections needed before publication:

- Check nested evidence budgets before decompression and during extraction.
- Preserve partial generations into new directories and reject invalid resume
  prefixes; retain completed work after a keyboard interruption.
- Carry both solve kinds, their programs, notes and exposure annotations through
  the portable reviewer feed, rather than only replaying blind solves locally.
- Reopen the Racket bridge after a failed application; archival execution never
  inherits canonical approval.
- Bind resumed batches to all selected mapped generation sources and controller
  bytes, retaining the partial prefix and rejecting helper/source drift.
- Independently reproduced two final-review defects, then fixed them: blind
  replay retains the original whole-canonical hash while proving only the main
  task's rows changed; evidence extraction creates directories only through
  anchored descriptors, rejecting symlink ancestors before creating children.

Independent isolated full suite: **228 passed, 3 Torch-dependent skips**.
Owner focused suite before the final adversarial fixes: **102 passed**.
The two final-review regressions first failed as predicted, then the focused
solve/evidence suite passed **45 tests**. Final owner suite and relocated packet
release receipt are recorded separately; a passing fixture is not a release.
The owner full suite subsequently passed **234 tests**. A separate timeout
regression confirmed that unfinished replay previously became a verified bad
label; the corrected final solve/evidence suite passed **47 tests**. Noncompleted
replays now retain execution status and raw claims but keep correctness unknown.
The relocated packet exposed a further bootstrap defect: documented
`solve_episode.py blind prepare` skipped the offline-Racket setup. The wrapper
regression first failed (the ordinary prepare case passed), then the corrected
final solve/evidence suite passed **49 tests**. Fresh-extraction verification
without a system Racket or predecessor access is required for the release.

The current send ZIP stays available until the candidate passes the release
checks. New solve instructions record exposure honestly: the full library still
contains references, so this is reviewer-reported nonconsultation, not enforced
isolation. Legacy post-repair returns remain readable and exposed as declared.

## Proposals and remaining work

The powered lesson census is a useful advisory proposal, separate from the
12-lesson smoke. Its timing and ambiguity counts are reviewer measurements,
not a new full-corpus maintainer measurement. More samples increase coverage
against declared rivals; they do not discover unspecified rival rules, prove
identifiability, or confer training admission. Independence assumptions are
needed before interpreting binomial bounds on scheduled generator samples.

Typed feedback, a new overlap/cache adversarial round, HMAC analysis and revised
intake state UI were not delivered in this follow-up. Keep the existing mechanisms;
the next reviewer brief should address these remaining items with fixtures.
Trainer changes and H1–H4/D1 dispositions are owned and recorded by ARC2train.
The corrected UTC Slurm attribution remains an interval-based hypothesis, not
a directly captured producer job ID.
