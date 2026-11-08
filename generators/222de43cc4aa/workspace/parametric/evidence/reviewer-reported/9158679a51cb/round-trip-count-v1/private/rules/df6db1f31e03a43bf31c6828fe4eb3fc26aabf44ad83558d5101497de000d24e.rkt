(rule! (lambda (g)
         (let* ((h (rows g))
                (w (cols g)))
           (let* ((period (- h 1))
                  (out-h (+ 1 (* 2 period))))
             (build-grid out-h
                         w
                         (r c)
                         (let* ((pos (remainder r (* 2 period)))
                                (ir (if (<= pos period) pos (- (* 2 period) pos))))
                           (at g ir c)))))))