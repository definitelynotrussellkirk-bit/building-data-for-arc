# `b9ada70e7181` chamber-gravity parameter

The hidden episode setting is `gravity_policy`:

- `all_down` is the exact canonical Racket program, byte-for-byte.
- `chamber_parity` first counts all pebbles in each full-height-wall-delimited
  chamber, then stable-packs every column upward for an even chamber or downward
  for an odd chamber.

The sampler is setting-neutral. Every scene contains both chamber parities,
non-palindromic stacks, and crossed controls. Its first two chambers have
opposite intended directions while sharing stack rows, width, occupied-row set,
top and bottom rows, first color, exact color sum, unique-color set, maximum color,
and the same nonempty-column profile. The minimum lesson crosses both parity and
magnitude with 6-up, 7-down, 8-up, and 9-down control chambers.
Across the minimum two demonstrations, some fixed chamber ranks change direction
while another keeps its direction, so neither a static rank table nor a rule that
counts only chamber 0 and extrapolates relative directions can fit. The retained
rival bank also probes fixed direction, reversed order, per-column parity,
nonempty/first-column counts, chamber rank, width/boundary parity, occupied-row
parity, and color-summary parity shortcuts.

The family supports 2-6 demonstrations and exactly four distinct queries. The
last query is a substantive 30×30 case. `certify()` recomputes labels and teaching
claims, enforces the promised counts, and rejects duplicate inputs, malformed ARC
numeric types, stale programs, surviving named rivals, and simple count or
color-sum threshold rules.

`prototype.py` exposes the constructive sampler, Python claim mirror, scene
analysis, shortcut rivals, and protected-Racket execution helper.
`adversarial_probe.py` is a reusable task-local audit for minimum lessons,
boundary dimensions, certificate negatives, setting-neutral inputs, and
protected-Racket agreement. The native adapter remains deliberately thin.
Owner qualification and acceptance are still required; this workspace does not
change catalog approval or training admission.
