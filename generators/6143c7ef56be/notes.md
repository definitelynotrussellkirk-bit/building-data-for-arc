# Working notes: 6143c7ef56be

Imported associated notes retain original evidence/timestamps in `evidence/associated_notes.jsonl`.

## 2026-10-24 parametric admission candidate

The canonical generator and canonical Racket rule remain byte-for-byte unchanged. The task-local native adapter adds one episode-fixed parameter, `route_marker = none | nearest | farthest`; `none` materializes the exact canonical program. The two alternate settings first select the uniquely nearest/farthest quadrant marker by Manhattan distance to its collapsed-block destination, then paint that selected color along a vertical-then-horizontal route into the destination.

The retained audit showed that corner-only demonstrations could teach the shortcut “copy the four outer grid corners.” The lesson builder now uses shared paired inputs whose three demonstrations distinguish all three parameter settings and deliberately place markers off the outer corners. Its bounded self-audit also refutes a fixed-top-left-route rival. Four queries are stored per episode, the first query is invariant under one-query versus four-query requests, and query four is a substantive 30×30 scene.

Source-bound evidence is under `workspace/parametric/evidence/`. Native qualification at `checks/6143c7ef56be/qualification/qualification.json` passed six seed/setting jobs, with sibling execution evidence. The protected-Racket sequential witness at `checks/6143c7ef56be/sequential-witness.json` shows that substituting the opposite Step-A intermediate changes Step B's route and final grid.

Limits: the learnability audit covers two explicit shortcut families and finite seeds, not universal uniqueness. `ready` is reviewer-reported only; exact live-byte owner qualification/acceptance remains mandatory before variant approval or training admission.
