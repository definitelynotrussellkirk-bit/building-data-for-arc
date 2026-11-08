# Optional, unapplied callable-authority calibration

The selected canonical program is `(rule! rotate-ccw)`. The unchanged checker
returns `None` for that spelling, although its existing applied/lambda forms
recognize the same prelude operation. This can demand an impossible generated
counterexample to the authoritative rule itself.

`callable-authority.patch` adds only exact full-normalized-program matches for
the six existing `_AUTHORITY_SHORTCUT_HEADS` identifiers. It adds no new heads,
changes no generic shortcuts, and changes no declared-rival policy. The full
proposed source is retained as `generator_semantic_gate.proposed.py`; neither
it nor the patch has been applied to the shared source.

Seven tests run the actual selected source functions/constant AST nodes with
synthetic canonical lookup inputs. Original source: eight failed assertions
(six whitelist subcases, whitespace, generic authority exemption). Proposed
source: seven tests pass, including eight rejected compound/nonwhitelisted
programs, two legacy forms, original `None` behavior, and an explicit declared
`rot270` rival that remains unsatisfied. These focused tests do not represent
a rerun of the full task semantic gate or resolution of its other warnings.

A separate native Racket bridge call executes `(rule! rotate-ccw)` on
`[[1,2,3],[4,5,6]]`, producing `[[3,6],[2,5],[1,4]]`. The probe receipt records
one Racket call and the bridge/prelude source hashes. No new main gate census
or assignment selection was performed.

Commands from the session root:

```bash
AUTHORITY_SOURCE="$PWD/packet/WORK/repo/shared/tools/generator_semantic_gate.py" python -m unittest discover -s packet/WORK/checks/authority-calibration -p 'test_authority_shortcut.py' -v
python -m unittest discover -s packet/WORK/checks/authority-calibration -p 'test_authority_shortcut.py' -v
```

Native probe command from `packet/`:

```bash
python3 review.py run python3 ../checks/authority-calibration/probe.py
```

`calibration.json`, `red.log`, `green.log`, and `racket-probe.json` retain the
observed results. The shared checker hash was checked against the original
packet manifest after the work and remains unchanged.
