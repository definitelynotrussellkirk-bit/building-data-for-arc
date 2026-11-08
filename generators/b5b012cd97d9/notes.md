# Working notes: b5b012cd97d9

Imported associated notes retain original evidence/timestamps in
`evidence/associated_notes.jsonl`.

## 2026-10-24 review-31443b62a37074ce

- Preserved the selected canonical rule and generator unchanged. The default
  `secondary=next_repeated` program is byte-identical to canonical source hash
  `27f6a42c783057ca3e60a9601751d5ce788cfc0b273a3249efdea9fca5b5e6b4`.
- Added a task-local native parametric adapter with two episode-fixed settings:
  `next_repeated` and `big_side_relay`. The latter derives the largest mass's
  square side, then uses that input-dependent number to select the secondary
  color count before packing.
- Kept inputs matched across settings, deterministic and prefix-stable. The
  adapter supports 2–6 demonstrations and 1–4 queries; the four-query prefix
  includes a substantive 30×30 boundary case.
- Constructed the first two demonstrations to distinguish both lawful settings
  from a finite bank of count, color, position, component, bounding-box and
  density shortcuts. The retained 64-seed audit is bounded evidence, not a
  universal identifiability proof.
- Repaired the existing test harness to use public portable root/canonical APIs.
  Its prior fixed `__file__` depth failed in the staged runtime. Also separated
  archival base-solution Racket snapshots from the live selected canonical
  source instead of incorrectly asserting byte equality between them.
- Native qualification passed for both settings on seeds 0 and 17 with three
  demonstrations and four queries. A source-bound protected-Racket witness
  shows that replacing the true intermediate 9 with fixed 4 selects a different
  secondary color and changes the final grid.
- Public projection exposes demonstrations and only the current unlabeled query;
  settings, programs, query answers, future inputs and total-query hints remain
  private.

### Limits and next action

This is reviewer-reported native-ready work, not owner acceptance or training
admission. The owner should integrate the exact patch, replay
`checks/b5b012cd97d9/qualification/qualification.json` and
`checks/b5b012cd97d9/causal/witness.json`, assess the causal interpretation, and
then run the native acceptance step. The optional peer homes were not modified or
re-audited in this return.

<!-- arcpuzzles-owner-reconciliation:start -->
## Current parametric decision

Owner-native accepted `secondary=next_repeated|big_side_relay|preserve_vertical`. Both previously accepted programs and the incoming vertical program remain byte-exact. Three common query-blind demonstrations teach all policies. Even/odd seeds choose complete original relay/vertical query banks at source seed floor(seed/2); optional demonstrations retain every original profile across draws.

Native minimum is now **3 demonstrations**, maximum6; queries remain1–4 with matching inputs and stable prefixes. Exact relay no-match behavior packs the largest mass only; exact vertical tied-center behavior rotates. No compound relay-plus-orientation rule was invented. Fresh installed-source20tests passed; native qualification covered3settings ×2seeds,3demos/4queries,78protected evaluations, followed by acceptance. Two protected causal replays passed. Current hashes, provenance and bounded independent audit: `evidence/owner-sampler-reconciliation/current.json`. Earlier review claims apply to their original sources; the incoming raw delta is separately deferred. No training admission or unrestricted uniqueness is claimed.
<!-- arcpuzzles-owner-reconciliation:end -->
