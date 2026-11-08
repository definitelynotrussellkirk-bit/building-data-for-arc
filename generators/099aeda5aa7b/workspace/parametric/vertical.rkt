(rule!
 ;; Overlay the TOP-BOTTOM mirror onto the grid: every non-zero cell also
 ;; lands at its vertically mirrored position.
 (overlay g (flip-ud g)))
