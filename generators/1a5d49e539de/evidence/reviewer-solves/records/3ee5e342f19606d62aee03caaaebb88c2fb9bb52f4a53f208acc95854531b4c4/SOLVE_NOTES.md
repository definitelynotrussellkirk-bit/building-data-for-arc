# Solve notes

From the three visible pairs, I treated equal-coloured nonzero cells as
8-connected objects. In every pair, exactly three object shapes were symmetric
under reflection across their own vertical axis and one was asymmetric. The
output was the tight bounding-box crop of that unique asymmetric object.

The implementation therefore enumerates same-colour 8-connected components,
normalizes each component to its bounding box, tests left-right reflection, and
returns the crop of the sole failing component. No reference source or masked
label was consulted during this solve episode. Earlier rule exposure is reported
separately in the episode metadata.
