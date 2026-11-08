(rule!
  (let* ((commands (filter (lambda (v) (not (= v 0))) (last g)))
         (base (subgrid g 0 0 (- (rows g) 2) (- (cols g) 1)))
         (motif (crop-to-content base))
         (mh (rows motif))
         (mw (cols motif))
         (out-w (+ (* (length commands) mw) (max 0 (- (length commands) 1)))))
    (grid-from-fn mh out-w
      (lambda (r c)
        (let* ((tile (quotient c (+ mw 1)))
               (offset (modulo c (+ mw 1))))
          (if (or (>= tile (length commands)) (>= offset mw) (= (at motif r offset) 0))
              0
              (list-ref commands tile)))))))