# `beb87e1c1b19` transform-composition family

The exact canonical setting is `composition=union`.  Both settings first infer
the unique A→B dihedral transform and apply it to C.  `union` overlays the
transformed copy on C; `xor` retains cells occupied by exactly one of C and its
transformed copy.  Inputs are matched across settings, demo/query streams are
independent and prefix-stable, and the fourth query is a substantive 30×30
rectangular-panel case using a dimension-preserving transform.

`wrong_identity_intermediate.rkt` skips transform application by feeding C
itself into the XOR composition stage; protected replay must change the answer.

## Verification and handoff

The retained source inventory is `evidence/manifest.json`; focused receipts live
under `evidence/current/`. The final staged suite is 7/7, the bounded audit covers
16 seeds and 320 labeled pairs, and the protected authoring preflight covers four
jobs. Public projection produces 16 one-query files from four private episodes.
These receipts are source-bound reviewer evidence only; they do not grant owner
acceptance or training admission.
