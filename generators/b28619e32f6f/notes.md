# Working notes: b28619e32f6f

## Current native parametric family

`workspace/parametric/` supplies two private episode settings: `fixed` preserves
exact canonical Racket bytes; `relative_to_largest` first discovers enclosed
four-connected zero regions, derives the maximum area M across every frame,
then colors each area n with 8 when 4n <= M, 4 when 2n <= M, else 3.
This is input-dependent contextual gating, not iterative state simulation.

Constructive first-two demonstrations teach all fixed boundary values
7,8,9,23,24,25, relative equality/adjacent values at M32, and nonintegral
cutoffs at M51. The provisional M32/M48 curriculum admitted a ceiling shortcut;
M51 replaces the second teaching maximum and exposes that error. Multiple
frames, diagonal-only zero contact and area/bounding-box disagreement defeat
other declared shortcuts. The exact old-lesson counterexample and executed
programs are in `checks/b28619e32f6f/selfaudit-final/teaching-repair.private.json`.

Counts are 2–6 demonstrations (default 3) and independently 1–4 queries
(default 4), with matched input streams between settings. Queries include
7x7,17x20,24x30,30x30 with rotations; the largest scene contains two full-height
frames and substantial regions distributed across the canvas. The exporter
keeps four queries private and hashes only the currently visible one-query
projection. See the task-local README for exact commands.

The controlled area101 carve could leave an invalid solid red3x3 nested frame.
The sampler now rejects that carve; its regression was observed failing, then
passing. A separate small-room regression exposed and fixed an impossible
four-corner constraint for area3.

Verified on the final source: 35 focused tests; 8/8 bounded self-audit episodes
with 64 true-label occurrences checked through protected Racket (62 unique
executions including rivals); 14 fixed and 22 relative authored competitors
rejected by the first two demonstrations. Five named competing programs also
replayed in Racket. Native qualification passed both settings on seeds0 and17,
3 demos plus4 queries, using40 Racket evaluations. The source-bound causal
witness replaces M51 with32 and changes95 output cells; native construction
and independent replay both passed. Paths: `checks/b28619e32f6f/qualification/`
and `checks/b28619e32f6f/causal/`. These are finite checks, not universal uniqueness.

The approved canonical generator and reference authority remain unchanged.
Its inherited equality-boundary sampler audit remains open; this prototype's
new coverage does not resolve that production audit. The next owner action is
exact-source qualification and acceptance after intake. No training admission.
Imported historical notes remain in `evidence/associated_notes.jsonl`.

## Current owner parametric reconciliation

Three native-accepted rules: exact canonical fixed thresholds, the retained relative-to-largest thresholds, and singleton absorption before region measurement. Both original sampler modules remain; seed selects their extra-demo/query branch independently of settings and counts, after two common teaching witnesses. Owner protected causal replay and fresh native acceptance passed on the exact installed binding. Current evidence: `evidence/owner-sampler-reconciliation/current.json`. Prior canonical sampling audits remain open; finite qualification is not universal identifiability or training admission.

<!-- arcpuzzles-trainer-ambiguity:start -->
## Current trainer ambiguity follow-up

Claude supplied 1 exact canonical lesson(s) with a proposed alternative rule. Retained privately with source hashes and all stored queries: `evidence/trainer-ambiguity-current/current.json`. These are **open describer flags**, not confirmed wrong labels or failed current parametric qualifications. Check whether the proposed rival fits every demonstration and changes any stored query; distinguish source revisions before repairing. Approval and training state are unchanged.
<!-- arcpuzzles-trainer-ambiguity:end -->
