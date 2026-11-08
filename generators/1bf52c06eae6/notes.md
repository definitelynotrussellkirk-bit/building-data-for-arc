# Working notes: 1bf52c06eae6

## Review findings and repairs

- The inherited generator advertised 2–4 colors but always emitted two, ignored
  several controls, and had a near-empty self-check. It now validates every
  ordinary override strictly, makes exact dimensions/color count/palette/density
  and layout controls real, and constructs 2–4 sparse bboxes with distinct
  square areas and genuine expanded-square overlap.
- The canonical `smallest_first` program is preserved byte-for-byte at SHA-256
  `51585a1368ca51b2e7f9dbc7209a7fa3bf869b44e8c45e673a8c15523fc1327d`.
- Added `probe_demote`: ignore the unique color-9 instruction probe when building
  shape boxes; select the first canonical-priority square covering the probe;
  demote that input-derived color to last priority; then re-render the complete
  square mosaic without the probe.
- Episodes support 2–6 demonstrations and exactly four distinct queries. Query
  four is a substantive 30×30 case with four shapes, a single probe, at least
  100 nonzero input cells, and corner contact.

## Adversarial self-review and evidence

- An initial two-demo audit found that demoting the selected square could mimic
  deleting it when later squares covered it completely. Construction now requires
  visible selected-only area.
- A second audit found a full reverse-priority shortcut on one seed. Construction
  now requires a nonselected priority conflict that distinguishes selective
  demotion from globally reversing the order.
- Focused suite: 26/26 passed.
- Finite teaching audit: 36 jobs, 276 labeled pairs, 1,056 rival-demo checks,
  zero survivors among eight named shortcuts. Selected intermediates span all
  colors 1–8 and canonical ranks 0, 1, and 2.
- Protected authoring preflight: both settings at seeds 0 and 17, 40 Racket
  evaluations, original labels and ordinary draws included.
- Source-bound wrong-intermediate witness chooses the largest covering square
  instead of the first and changes 26 final cells in the selected case.
- Public projection: 16 single-query views; first-turn check: 24 invariance
  checks and four positive controls.

Owner source review, native qualification/acceptance, and training admission are
separate downstream gates and are not claimed here.
