(rule! (lambda (g)
         (let* ((h (rows g))
                (w (cols g)))
           (let* ((counts (make-hash))
                  (dummy (for* ((r (range 0 h)) (c (range 0 w)))
                               (let ((v (at g r c)))
                                 (when
                                   (> v 0)
                                   (hash-set! counts v (+ 1 (hash-ref counts v 0))))))))
             (cellmap g
                      (r c v)
                      (let ((color (+ c 1))
                            (cnt (hash-ref counts (+ c 1) 0)))
                        (if (and (<= color 4) (>= r (- h cnt))) color 0)))))))