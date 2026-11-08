# Section-frequency review implementation plan

Goal: preserve the canonical zero-divider/section-mode rule, add a separate
frequency-selection prototype, and make generated lessons teach frequency.
Specification: packet DUTIES.md, PARAMETRIC-RULES.md and RETURN-GUIDE.md.
Implementation choices below are reviewer decisions under the requested build.

## Scope and interfaces

- Canonical `generate(seed, sample_index, *, difficulty=None, **overrides)` still
  returns only an input; canonical Racket hash stays `bd52339e94ff`.
- Prototype owns `workspace/parametric/` and its dedicated test module. Its
  episode-wide `selection` is most-frequent (default) or least-frequent.
- Production repair owns `generator.py` and task-local regression tests. It
  adds a three-position schedule: canonical anchor, mixed witness, mixed witness.
  The two mixed inputs make each three-demo/four-pair lesson withstand one query
  holdout against the explicitly declared first/last/min/max/rarest rivals.
- Selected alias synchronization is exact-text-only; canonical and archival raw
  rules stay unchanged. Audit targets are findings-only after repair.

## Steps

- [x] Verify packet, draw once, finish independent blind solve (3/3 visible).
- [x] Preserve baseline battery failures and reproduce first-cell ambiguity.
- [x] Build and Racket-check the separate parametric prototype.
- [x] Write failing regressions for malformed controls, lesson ambiguity and
  source portability; implement only the supported repairs.
- [x] Preserve canonical linked profiles, lawful 8..30 dimensions and exact
  override behavior; declare infeasible combinations precisely.
- [x] Run task tests, complete after battery, 100 production lessons per band,
  all single-query holdouts and every finite schedule start at fixed seed 0.
- [x] Freeze post-repair visible-only solve (3/3 visible; masked labels unknown).
- Final handoff is tracked outside this source patch in `WORK/REVIEW.md`,
  `WORK/AUDIT.md`, and `WORK/RESULTS.json`: two findings-only audits, exact
  commands, fresh delta replay, independent-environment tests and final package.

## Review focus

Invalid scalar coercion; rejecting feasible joint controls; failure to preserve
canonical profiles; one remaining witness disappearing under query rotation;
prototype labels or hidden parameters leaking into public challenges. Tests and
receipts must distinguish canonical repair, proposed variants and unknown scope.
