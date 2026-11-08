# Working notes: 96ebf3053dbe

Record design decisions, hypotheses, review findings, and unresolved questions here.
Imported associated notes retain original evidence/timestamps in `evidence/associated_notes.jsonl`.

## Current bounded robustness repair

The validator now rejects a color-2 marker shared by separate 6-components.
Previously, `used_anchors` was a set checked only for equality with all markers;
that proved every marker was used but lost evidence that one marker was used
twice. A 7x3 scene with two singleton bars above and below the same lower marker
was accepted as `singleton_cycle`. Reuse now emits the existing exactly-one
ownership error, and both `rule_mirror` and `observe_overrides` reject it.

Source-bound witness and red/green launcher receipts are retained in
`checks/96ebf3053dbe/before.json`, `before-command.json`, and `after-command.json`
in the review return. `tests/test_anchor_ownership.py` covers the rejection and
a valid scene with independent singleton anchors. The bounded control probe
in `workspace/probe_anchor_ownership.py` preserves all four canonical pairs and
one medium draw from each of the eight general profiles (seed 17, index 23);
its result is `checks/96ebf3053dbe/after.json`, with `controls-command.json`.
The sampler and rule are unchanged; the version remains unchanged to preserve
seeded generation. Reference execution and full batteries were not rerun for
this validation-only change. That earlier repair did not include parametric work;
the current admission candidate is recorded below.

## Current parametric admission candidate: endpoint policy

The task-local family now exposes one private episode parameter,
`destination_endpoint=opposite|adjacent`. `opposite` is the exact canonical
Racket program (SHA256
`839e4ae1c265d3f0e7fba6ab8a2348618baa0fc4456d5a235509329b93f3bb5e`);
`adjacent` changes only whether each moved 2/5 pair lands at the endpoint next
to its input-side color-2 marker. Inputs are matched across settings, demo counts
are independently supported from 2 through 6, and every episode has exactly four
distinct queries. The final query is a lawful 29x30 balanced stress scene with
top, bottom, left, and right anchors, long bars, and boundary contact.

Native qualification at seeds 0 and 17 passed all four setting/seed jobs with
three demonstrations and four queries under protected Racket. The retained
demonstrations reject the alternate setting, a skip-anchor rule, and an
erase-only shortcut. The source-bound causal witness names marker-side inspection
as Step A, the selected endpoint as its input-dependent intermediate, and
reflection/painting as Step B; a protected-Racket skip-A ablation changes the
29x30 output. Public files expose only demonstration input/output pairs and query
inputs, use exact visible-byte IDs, and reveal later queries without a total-count
hint.

Current authorities are `workspace/parametric/evidence/manifest.json`,
`checks/96ebf3053dbe/qualification/qualification.json`, and
`checks/96ebf3053dbe/sequential-dependency.json`. Production `generator.py` and
the canonical rule row remain unchanged. The family is reviewer-reported
`ready`, not accepted or training-admitted. The next action is owner integration,
fresh exact-source qualification/acceptance replay, and semantic review of the
causal claim. Finite evidence does not exhaust arbitrary rival programs or
measure training gain.
