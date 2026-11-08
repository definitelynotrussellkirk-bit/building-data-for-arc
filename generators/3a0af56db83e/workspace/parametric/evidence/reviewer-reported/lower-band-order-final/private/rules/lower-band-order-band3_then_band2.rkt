(rule! (lambda (g)
  (let* ((w (cols g))
         ;; Four monochrome 3-row masks are stacked vertically. Project them
         ;; onto one 3-row frame without letting color identity encode priority.
         (band (lambda (j r c) (at g (+ (* j 3) r) c))))
    (build-grid 3 w (r c)
      ;; First nonzero wins in priority order 0 > 1 > 3 > 2.
      (let ((v0 (band 0 r c))
            (v1 (band 1 r c))
            (v3 (band 3 r c))
            (v2 (band 2 r c)))
        (cond
          ((!= v0 0) v0)
          ((!= v1 0) v1)
          ((!= v3 0) v3)
          ((!= v2 0) v2)
          (else 0)))))))