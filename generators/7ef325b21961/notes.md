# Working notes: 7ef325b21961

## Current decision

The base generator was repaired before family construction: frame statistics are now local per frame, distinct frames can have distinct winners, dot distractors cannot form pseudo-frames, `self_check` rejects malformed scenes, the canonical rule hash is pinned, and only four implemented axes remain. The canonical `fill_choice=majority` program remains byte-for-byte identical to catalog authority. The native nearby variant `fill_choice=minority` changes only the per-frame statistic selected by step A; step B consumes each locally selected color to fill that frame.

## Self-review result

The bounded audit rejects global-statistic, border-color, fixed-color, keep-dots, and skipped-selection shortcuts for both settings. Protected Racket agrees with all retained labels, including distinct local winners and a substantive 30×30 query. Public single-query projections pass private-field invariance, positive controls, first-turn consistency, duplicate checks, and masked-answer checks.

## Limits and next action

The audit is finite and the causal intermediate descriptions are reviewer-authored metadata, not a universal proof of depth. Authoring preflight and replay do not grant owner acceptance or training admission. Next: integrate the exact generator and family sources, verify the manifest/source binding, rerun native owner qualification and the protected causal witness, then perform fresh owner acceptance.
