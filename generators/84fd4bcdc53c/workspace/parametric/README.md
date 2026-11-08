# 84fd4bcdc53c parametric family

`bend_order=horizontal_then_vertical` is the exact canonical program.
`bend_order=vertical_then_horizontal` changes the input-derived L-bend used for
each consecutive row-major endpoint pair. The per-color trace is the sequential
intermediate; the final renderer consumes those traces in ascending color order
and preserves the first color at crossings. Inputs are matched across settings.
