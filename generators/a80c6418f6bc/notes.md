# Working notes: a80c6418f6bc

## Current reviewer decision — 2026-10-24

Built a task-local native parametric family with episode-fixed `orientation`:

- `direct` is the byte-exact canonical rule (`88309ffec80e727d6f8a027070bd733a8a85e6c76daea82a40a70bef2beb12b5`).
- `rotate_180` infers the A→B bbox-relative added-cell delta and edit-frame dimensions, rotates that input-derived intermediate 180 degrees, then stamps it at C's bbox origin.

The family supports 2–6 demonstrations and 1–4 independent, prefix-stable queries. Settings share identical visible inputs. The first two demonstrations include both a within-bbox edit and simultaneous two-axis expansion, so the legacy query-only `expand_both` teaching hole is not present in supported episodes. Query four is a genuine 30×30 case with 202 non-separator cells, 24 occupied rows, 25 occupied columns, and boundary contact.

Finite self-review covered 640 lessons and 5,120 declared-rival checks with no survivor beyond the selected setting; six representative jobs executed 68 protected-Racket labels. Native qualification passed both settings on seeds 0 and 17 (4 jobs, 40 protected-Racket evaluations). The standardized wrong-intermediate witness replays the exact qualified `rotate_180` query against the direct/unrotated-delta program and changes four final cells.

The inherited canonical-loader test was made portable with `reviewer_support.find_root` and `canonical_pairs`; the copied-runtime task suite now passes 32/32. Production `generator.py` and canonical authority remain unchanged, so existing approval bytes are preserved. Exact-source owner integration, fresh qualification, and acceptance remain pending; `training_admitted` is false. The finite rival inventory is not a universal identifiability proof.
