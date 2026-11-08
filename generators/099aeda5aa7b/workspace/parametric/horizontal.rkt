(rule!
 ;; Overlay the LEFT-RIGHT mirror onto the grid: every non-zero cell also
 ;; lands at its horizontally mirrored position.
 (overlay g (flip-lr g)))