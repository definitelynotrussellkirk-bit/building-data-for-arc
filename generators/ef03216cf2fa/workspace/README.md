# Workspace

`reference_probe.py` is a portable, independent oracle for `ef03216cf2fa`. It loads the selected generator only at the API boundary and independently implements component extraction, bounding-box crops, clockwise/counterclockwise rotation, perimeter ordering, packing, canonical-pair loading, and observable-axis recovery.

The focused tests import this probe so a shared defect in the generator's own mirror cannot make the suite self-confirming. Set `GENERATOR_UNDER_TEST=/path/to/generator.py` to replay the same tests against another source version; the retained counterexample regression fails against the immutable `2.0.0` baseline and passes against `3.0.0`.

The selected implementation remains `../generator.py`; workspace helpers are reviewer tools, not automatically selected production code.
