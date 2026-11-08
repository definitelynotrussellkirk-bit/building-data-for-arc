# Native leftmost-ranked band family

`all_bands` is the byte-exact canonical rule. `leftmost_ranked` finds the
leftmost singleton marker, converts it to its row-order rank, and gives only
that band the vertical side borders while retaining all marker rows and the
canonical top/bottom closures. Inputs are matched across settings.

The reusable bounded audit is `audit_lessons.py`; owner qualification remains
required after exact-byte integration.
