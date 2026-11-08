(rule!
 ;; Overlay the TRANSPOSE onto the grid: every non-zero cell also lands at
 ;; its mirrored (c, r) position.
 (overlay g (transpose g)))