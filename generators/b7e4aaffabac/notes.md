# Working notes: b7e4aaffabac

Record design decisions, hypotheses, review findings, and unresolved questions here.
Imported associated notes retain original evidence/timestamps in `evidence/associated_notes.jsonl`.

## Current parametric admission candidate: overlap policy

The task-local native family exposes one private episode parameter,
`overlap_policy=trimmed|full`. `trimmed` returns the exact canonical Racket
program (SHA-256
`a94b19efa0d96fb0cb5bf93f301417c5fb3719cf89e5e11f765584a9a4d43fa5`).
`full` preserves the same rectangle discovery, separation-axis ordering and gap
reasoning, but paints the entire input-derived shared facing span instead of its
one-cell-inset interior. The production generator remains byte-for-byte unchanged
at its approved SHA-256
`523f2401aa66ade4f0abbdd3fec1d01b88f37f37bcb91a9ee2a1c568237dd920`;
an attempted production lesson edit was reverted because changing that source
invalidates its frozen approval, and packet policy does not permit manufacturing a
replacement approval hash.

Inputs are matched across settings, demonstrations are prefix-stable for counts
2 through 6, and every episode has exactly four distinct queries independent of
the demonstration count. The two-example prefix contains horizontal and vertical
separation, an offset and boundary contact. The fixed queries cover 14x19, 19x23,
24x28 and a substantive 30x30 case. Public projection exposes only demonstration
input/output pairs and the currently revealed query input; settings, programs,
intermediates and query answers remain private, and IDs hash exact visible bytes.

The retained task-local verifier executed 88 protected-Racket program applications
across both settings and 2/3/6-demo episodes. Demonstrations select the requested
setting uniquely among the two declared policies and reject hard-coded-horizontal
and hard-coded-vertical programs. Native qualification passed both settings at
seeds 0 and 17 with three demonstrations and four queries. The source-bound causal
witness uses a qualified `full` query: Step A derives horizontal gap bounds and raw
shared span `[6, 11]`; substituting the trimmed span `[7, 10]` in Step B changes the
cyan bridge from 18 to 12 cells, and protected Racket replays both outputs.

Current authorities are `workspace/parametric/evidence/manifest.json`,
`checks/b7e4aaffabac/qualification/qualification.json`, and
`checks/b7e4aaffabac/causal/witness.json`. The family is reviewer-reported `ready`,
not owner-accepted or training-admitted. The next action is owner integration and
fresh exact-source qualification/acceptance replay. Finite evidence covers only
the declared settings, seeds and rival programs; it does not establish universal
lesson uniqueness or measured training gain. Optional peer targets were not run.
