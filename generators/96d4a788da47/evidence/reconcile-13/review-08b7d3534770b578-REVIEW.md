# Review — `review-08b7d3534770b578`

- **Scope:** two full native parametric builds, `93b39d8c4da4` and `96d4a788da47`; no peer tickets were assigned.
- **93 source:** family `d2e5fe0eb19da2970f58fbd5e56cae82fba55628c2a31f783af9f66e2fd31c0b`; exact canonical rule `d20fb64e7b014794b1e36c0f5b98545b0043a1398faa1bb12bce3bdb3840414d` unchanged.
- **93 repair:** added matched identity/mirror/clockwise-template settings, four-query 30×30 stress, public projection, bounded shortcut audit, and replayable transformed-template causal witness.
- **96 source:** family `c1c46aa49d27fc6d2ecb758929a4327121c2feec4854de07555cce2012d0dc84`; exact canonical rule `da14dfe7467eb27b48e9064cdd2a94cb7af91dbed6045b9260887290c8d57131` unchanged.
- **96 repair:** added matched left/right/per-object-nearest settings, irregular row-separated geometry, four-query 30×30 stress, public projection, bounded shortcut audit, and replayable displacement causal witness.
- **Checks:** focused tests 26/26 for each family; self-audit 12/12 jobs for each; qualification 6/6 jobs and 60 protected-Racket labels for each.
- **Changed-target tests:** `93…` 37/37; `96…` 75/75.
- **Export checks:** 48 public views, 12 first turns, 72 private-field invariance mutations, and 12 positive controls passed; all 48 saved files passed canonical-byte/schema checks.
- **Reference-rule changes:** none; each default program is byte-identical to its selected canonical authority.
- **Needs attention:** reviewer work is ready, but owner integration, fresh exact-source qualification, native acceptance, and training admission remain separate mandatory steps.

## `93b39d8c4da4`

The new private parameter is `template_transform = identity | mirror_lr | rotate_cw`. Step A extracts and tight-normalizes the full color-2 template, producing transformed occupied-cell geometry. Step B stamps that geometry at every color-3 marker in color 8. The fixed-L counterfactual changes a qualified mirror output under protected Racket. Evidence: `checks/93b39d8c4da4/qualification/`, `checks/93b39d8c4da4/causal/`, `checks/93b39d8c4da4/self-audit.json`, and `checks/93b39d8c4da4-tests/result.json`.

## `96d4a788da47`

The new private parameter is `destination_edge = left | right | nearest`. Step A measures each object’s left and right bounding-box margins, producing one signed displacement per object. Step B translates the exact original cells by those displacements. A constant `+1` wrong-intermediate changes a qualified nearest output under protected Racket. Evidence: `checks/96d4a788da47/qualification/`, `checks/96d4a788da47/causal/`, `checks/96d4a788da47/self-audit.json`, and `checks/96d4a788da47-tests/result.json`.

## Limits

The audits cover finite named rivals and finite seeds/counts; they do not prove universal identifiability or measured training benefit. Qualification and witness receipts are source-bound reviewer evidence, not owner acceptance or training admission.
