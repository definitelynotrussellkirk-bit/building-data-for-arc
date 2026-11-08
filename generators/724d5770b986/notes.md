# Working notes: 724d5770b986

## Current decision

Keep production `generator.py` v3.0.0, `RULE_HASH=e39c8a4e2b02`, and the
canonical Racket program unchanged. Replace the inherited radius proposal with a
native two-setting family that satisfies this round's sequential-dependency and
2–6 demonstration contract:

- `post_action=expand_only`: byte-exact canonical blocker-preserving 3x3 expansion.
- `post_action=highlight_largest_post_component`: run the same expansion, compute
  four-connected blue components on that expanded intermediate, and recolor the
  unique largest component to 8.

The constructive sampler makes the largest original blue component differ from
the largest post-expansion component. Therefore the second step cannot be
correctly performed before the first. Settings use matched inputs, support 2–6
demonstrations and 1–4 queries independently, and retain four distinct queries,
including a substantive 30x30 case.

## Verification and limits

The source-bound staged suite passes 100/100 tests. The bounded audit passes all
12 jobs with 221 protected-Racket evaluations and no surviving named rivals.
Authoring preflight passes four qualification jobs with 32 protected-Racket label
evaluations. The replayable wrong-intermediate witness changes 11 final cells,
and public release checks pass 16/16 one-query views, four first turns, 24
private-field invariance mutations, and four visible-query positive controls.

This is reviewer-reported `ready`, not owner acceptance. Exact-source owner
review, native qualification, fresh acceptance, and any training admission remain
mandatory. The finite rival set is not a universal uniqueness or training-value
proof.
