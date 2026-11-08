## e5ec1ac39df5

**Finding types:** existing canonical-coverage defect reproduced; newly retained
dimension-control/API defect. Findings only; the audited generator and rule were
not changed.

The audited version is `2.0.0`, generator SHA-256
`9e8fb059476e5ace3bca8092f92a395bca20c549c446e672599f63238a2f84d2`.
Public `Catalog.apply` executed canonical rule `ee68f3c23aa1`, matching the
catalog, with rule-text SHA-256
`9f6ebd92a9a73e37c3ec6744eeeb7e56c8b1d07cbed06823836d850892d3e843`.
All six retained applications completed without error; all three canonical
outputs exactly matched their supplied labels. These six applications contain
four unique inputs because the three control calls return identical grids.

### E5-F1 — Existing canonical-coverage defect, reproduced on unchanged source

The retained same-source audit `review-0109cbd0cb98d040:v0001` already reports
this issue; its current index resolution is `needs_triage`. This is fresh
confirmation of that finding, not a new discovery.

The current `self_check` rejects **2/3 authoritative canonical inputs**:

| Canonical pair | Input shape | Room geometry | Validator result | Racket output |
|---|---|---|---|---|
| Train 0 | 9 × 13 | 2 × 3 rooms; heights 3/3, widths 3/3/3 | Accepted | Exact canonical match |
| Train 1 | 7 × 17 | 1 × 3 rooms; height 5, widths 5/3/5 | Rejects the single-row lattice | Exact canonical match |
| Test 0 | 11 × 10 | 2 × 2 rooms; heights 3/5, widths 4/3; seed at (7, 2) off center | Rejects nonuniform rooms and off-center seed | Exact canonical match |

The source requires at least two room rows and columns, uniform rectangular
room dimensions, and exactly centered seeds. The second training input returns
early at the lattice-count check, so its nonuniform widths are an additional
observed geometry difference rather than a second reported validator message.

A deterministic structural census used seeds **1..100**, with
`sample_index = seed`, separately for easy, medium, and hard. Results:

| Difficulty | Draws | Unique inputs | Uniform room dimensions | All seeds centered | Self-check accepted |
|---|---:|---:|---:|---:|---:|
| Easy | 100 | 10 | 100 | 100 | 100 |
| Medium | 100 | 95 | 100 | 100 | 100 |
| Hard | 100 | 84 | 100 | 100 | 100 |
| Pooled | 300 | 183 | 300 | 300 | 300 |

Per-band unique counts overlap, so their sum is not the pooled unique count.
This is a finite structural and validator census. The 300 sampled grids were
not all passed through Racket, and this audit makes no universal-support or
lesson-identifiability claim. A solver restricted to uniform rooms with centered
seeds is a generated-distribution shortcut; it is **not a canonical-fitting
rival**, because that restriction excludes authoritative canonical inputs.

### E5-F2 — Advertised full-grid dimension overrides are silently ignored

This finding is new relative to the retained same-source audit above.
`AXES` advertises integer `grid_h` and `grid_w`, both with `valid: varied`.
The shared contract at
`docs/reference/PUZZLE_GENERATOR_SPEC.md`, section **Reserved full-grid dimension
axes**, explicitly assigns these names to the full returned height and width.

Three calls used the same identity: `seed=2`, `sample_index=2`,
`difficulty="medium"`:

| Overrides | Returned shape | Same grid as default | Consumed overrides |
|---|---|---|---|
| None | 11 × 16 | Baseline | None |
| `grid_h=30, grid_w=30` | 11 × 16 | Yes | None |
| `grid_h=13, grid_w=13` | 11 × 16 | Yes | None |

All three grids pass `self_check` and have input SHA-256
`3986ce848417dfd7f01a9ba54a2db7ea6ec9f4aabca974344a3f8ebb51a8b8a8`.
Their actual Racket outputs are identical, with SHA-256
`f86498049a8f2d08a1fa1bf4a0b6a53d9515979be3cd5db4cd775d8c4e6b447d`.
The public context provenance records only `rooms_r=2`, `rooms_c=3`,
`room_h=4`, and `room_w=4`; `overrides_used()` is empty for both override calls.
The source never reads/draws `grid_h` or `grid_w`: dimensions are derived from
room counts and sizes, yielding 2 × (4 + 1) + 1 = 11 rows and
3 × (4 + 1) + 1 = 16 columns.

The numeric validity range is unspecified, so the 30 × 30 witness alone does
not establish that this size must be realizable. The additional 13 × 13 request
removes that ambiguity: 13 × 13 occurs in **15/100 medium draws**, including
`seed=1, sample_index=1`, whose input hash is recorded in the evidence. The
advertised controls are nevertheless accepted and ignored at the same fixed
identity. This is an override/metadata contract defect, not a claim that the
returned 11 × 16 grid violates the Racket rule. A repair should make dimension
controls observable, explicitly reject incompatible settings, or stop advertising
them as controllable full-grid dimensions.

### Evidence and reproduction

- `checks/audit/e5ec1ac39df5/probe.py`: portable public-helper probe using
  `find_root`, `canonical_pairs`, and `load_selected_generator`; selected source
  hash is checked before and after execution.
- `checks/audit/e5ec1ac39df5/evidence.json`: canonical grids, exact validator
  messages, all 300 identities/hashes and structural measurements, control
  grids and draw provenance, contract hash, prior-audit identity, and actual
  Racket outputs/hashes.
- `checks/audit/e5ec1ac39df5/racket.json`: full public authority receipt for the
  three canonical inputs and three control-call inputs; generator-domain
  checks reproduce the same two canonical rejections.
- `checks/audit/e5ec1ac39df5/commands.json`, `probe.stdout.log`,
  `probe.stderr.log`, and `probe.exit`: exact wrapper command, runtime working
  directory, output, and exit status **0**. Exit 0 means the audit probe
  completed; it is not a generator gate pass.

From the outer packet directory, the recorded command was:

```sh
WORK/.venv/bin/python review.py run /workspace/scratch/496944bd91ed/arc_review/WORK/.venv/bin/python /workspace/scratch/496944bd91ed/arc_review/WORK/checks/audit/e5ec1ac39df5/probe.py
```

The wrapper's effective payload directory was `WORK/repo`. No full battery,
query-scoring operation, generator/rule modification, or training admission was
performed in this audit.
