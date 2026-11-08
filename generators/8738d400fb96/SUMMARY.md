# Signed marker-vector translation

Select the largest same-color four-connected green component. Move it by the
signed vector from marker2 to marker1, recolor to8, and clip to a fresh same-size
zero canvas. Other components disappear; an all-zero output is valid.

Version2.0.0 expands signed movement, clipping and distractor support, replaces
inactive controls with exact dimensions/shape mass, and supplies an eight-demo
curriculum with explicit shortcut witnesses. Canonical rulefc4e32aa0363 is
unchanged. Current choices, evidence and limits are in notes.md; tests contain an
independent oracle and workspace/ contains the reusable output-profile checker.
