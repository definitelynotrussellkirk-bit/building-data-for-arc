# Native cap / vertical-bridge family

`cap_only` is the selected canonical Racket program byte-for-byte.
`cap_then_vertical_bridge` first creates exactly the canonical red right-cap
cells, records the coordinates that changed from input zero to output color 2,
then groups those derived coordinates by column and fills only zero cells between
each eligible column's first and last new cap.

Every scene has at least two separated cap columns and three cap rows. Six-column
spacing guarantees a visible zero gap between neighboring runs, so the wrong
horizontal continuation is observable even in the smallest lesson. Wrong-color
controls, full-height space, and multiple eligible columns distinguish color-
blind capping, wrong bridge color, endpoint, extent, and first/last-column
shortcuts. The fourth query is a substantive 30x30 boundary case.

`audit_native.py` executes both settings and eight semantic shortcut programs
through protected Racket over four seeds. `skip_cap.rkt` is the causal ablation:
the admitted raw input has no color-2 cap coordinates, so Stage B has no
intermediate to consume and the final output changes.
