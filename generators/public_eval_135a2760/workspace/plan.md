# Periodic-strip reconstruction implementation plan

Goal: author the missing general parent rule and a native two-setting family.
Architecture: detect frame separators, infer each strip's least-error repeating
vector sequence (smallest period wins ties), then restore it or mark its errors
with the strip's ring color. All sampler resources stay inside parametric/.
Constraints: exact canonical copy, 2–6 demos, 1–4 stable query prefixes, four
private queries, matched inputs, substantive 30×30 query, no shared-source edits.

- [x] Write failing tests for original labels, a literal corruption fixture,
  count/type boundaries, private/public invariance and finite rivals.
- [x] Implement Python mirror/sampler, exact Racket reference and mark-errors
  alternative, thin native adapter and ordinary generator entrypoint.
- [x] Execute originals and generated labels through protected Racket; fix
  concrete sampler/teaching defects and retain regressions.
- [x] Run bounded audit, public export tests, source-bound causal witness,
  authoring preflight; self-review before moving to second target.

Review focus: incorrect orientation, short/aliased periods, errors within first
repeat, isolated boundary-corruptions, hidden-field leaks, bool-as-int inputs.
Decision: general rule is minimum Hamming reconstruction over periods up to
half the strip length, with ascending color tie-breaks and shortest period.
Generated examples require uniquely determined reconstructed labels, not merely
an arbitrarily chosen period; that restriction is tested and documented.
