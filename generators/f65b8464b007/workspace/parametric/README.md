# Parametric cyclic-shift family

This family keeps the source task's section parsing, fixed section colors, and
cyclic transfer of final-band shapes.

- `shift_rule=next` is the exact canonical Racket program byte-for-byte. Each
  output section receives the next section's final-band shape.
- `shift_rule=densest_index` first counts occupied cells in every first-band
  shape. The unique densest shape's zero-based section index is the cyclic shift
  applied to the final band. The sampler keeps that index at least two and varies
  it across the first two demonstrations, so the dependency is active and is not
  reducible to one fixed shift.

The adapter supports 2–6 demonstrations and exactly four distinct queries. The
four query roles are 9×11 ordinary transfer, 13×19 wider sections, 17×29
boundary-width transfer, and a substantive 29×29 stress scene. Exact 30×30 is
not lawful under this grammar: three-row bands separated by one blank row have
height `4*b+1`; the extended five-wide/five-section grammar reaches 29×29.

`evidence/current/audit.json` records a protected-Racket audit of eight finite
rules on matched inputs. It is bounded evidence, not a universal uniqueness or
learning claim. Query answers, settings, and programs remain private in native
qualification/export records.
