## 6b4b56166bfd

**Two reproducible findings; target left unchanged.** Audited generator SHA-256:
`f5199baa50a2c21157599f14b282471082818630273d028e420116e61353e84b`
(v2.0.0). The selected canonical Racket rule hash is `f2aaf100dc45`.
This is a findings-only audit, with no repair or approval-status change.

### 1. A canonical-fitting coordinate restriction survives production demonstrations

The rival `rotate_only_at_or_above_pivot` performs the same fourfold copying,
but only for original seed cells on or above the pivot row; other input cells
remain unchanged. It fits **all five labeled canonical pairs** because their
seed cells all lie on or above the pivot. Unlike the declared half-turn rival,
canonical examples cannot eliminate this restriction.

The actual production materializer, `runner.run_one`, reproduces an ambiguous
three-demonstration, one-query lesson with `seed=1`, `sample_index=3`, and no
difficulty argument or overrides. Its accepted demonstration indices are
`3, 4, 5`, and its query index is `6`; no input was rejected. The rival fits all
three demonstration outputs and disagrees with the Racket-executed query.
The query is 7 by 7, with pivot 5 at `(3,3)`, seed 7 at `(1,4)`, and seed 6 at
`(6,0)` (all coordinates zero-based). The reference paints color 6 at `(0,0)`,
`(0,6)`, and `(6,6)`; the rival leaves those three cells zero.

The same kind of production ambiguity was independently materialized at
`difficulty="easy", seed=1, sample_index=33` (accepted indices `33..36`, six
query-cell differences) and `difficulty="hard", seed=1, sample_index=3`
(accepted indices `3..6`, three query-cell differences). All three lessons
have four distinct inputs and zero rejection/skipping. Their existing
`lesson_identifiable` hook returns `[]`. Each four-pair lesson has exactly one
rival-disagreeing pair, so holding out that pair is ambiguous: **3 of the 12
checked query rotations** are ambiguous, including each original production
query. Rotations reuse these labels; they are not additional independent draws.

This establishes a concrete gap in the current half-turn-only teaching
contract, not a claim that all generated lessons are ambiguous. A targeted
repair should retain this canonical-fitting rival and arrange demonstrations
that expose below-pivot seeds before a query needs that behavior.

### 2. `CANONICAL_SHORTCUTS` contains a false canonical-fit declaration

The source aliases `CANONICAL_SHORTCUTS = dict(SEMANTIC_RIVALS)`, thereby
asserting that `half_turn_only` fits every labeled canonical pair. The current
contract in `docs/SEMANTIC_GATE_CONTRACT.md` requires exactly that universal
canonical fit; a nonmatching rival belongs in `LESSON_COMPETITORS` and/or
`SEMANTIC_RIVALS`, not this declaration.

The declared half-turn shortcut agrees with **0 of 5 canonical labels**.
All five stored canonical labels were separately confirmed by executing the
selected Racket rule. Calling the current shared
`check_canonical_ambiguity` component returns
`status="invalid_declaration", checked=5, mismatches=5, errors=0` for this
entry. This is a directly reproduced declaration failure under the current
semantic contract. No whole semantic-gate stage or new battery was run here.

### Execution and evidence

The probe loaded the exact selected source with
`reviewer_support.load_selected_generator(..., root=find_root(__file__))`,
read canonical pairs through the portable helper, and used the existing
`RacketBridge` plus `runner.run_one`. It executed **17 reference labels**:
five canonical pairs and twelve generated pairs. Every reference output
matched the generator's Python mirror; the findings concern the curriculum
and shortcut declaration, not incorrect labels. The target source hash was
unchanged at completion.

Retained files, relative to `WORK/`:

- `checks/audit/6b4b56166bfd/probe.py`: executable rival and exact replays.
- `checks/audit/6b4b56166bfd/probe.json`: complete inputs, Racket outputs,
  rival predictions, canonical comparison, accepted indices, rotations, and
  source/rule/helper hashes.
- `checks/audit/6b4b56166bfd/probe-command.log`,
  `checks/audit/6b4b56166bfd/probe-command.exit`, and
  `checks/audit/6b4b56166bfd/command.json`: command, working directories,
  stdout/stderr, and exit status (`0`, successful evidence collection).
- `checks/audit/6b4b56166bfd/input.json`: the exact decisive default query,
  suitable for the supported `arcpuzzles apply` command. Its existing Racket
  label and rival prediction are in `expected-output.json` and
  `rival-output.json`; `input-manifest.json` binds those file hashes to the
  replay and records the supported apply check as **pending**.
- `checks/audit/6b4b56166bfd/audit-evidence-manifest.json`: SHA-256 and byte
  length of each retained audit file.

Replay from the outer review directory:

```bash
PATH=/dev/shm/arcpuzzles_racket_4c463a4d2f73/bin:$PATH PYTHONDONTWRITEBYTECODE=1 \
  WORK/.venv/bin/python review.py run \
  /workspace/scratch/4c463a4d2f73/arc_review/WORK/.venv/bin/python \
  ../checks/audit/6b4b56166bfd/probe.py
```

The wrapper's effective working directory is `WORK/repo`. The run used the
existing protected Racket runtime and created no official check or runtime
snapshot. These bounded findings do not change training admission or approval.

The additional supported `arcpuzzles apply` replay of `input.json` is pending
execution by the root reviewer after the active census completes; it has not
been counted among the completed checks above.
