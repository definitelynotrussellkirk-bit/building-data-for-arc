(rule! (lambda (g)
         (let* ((h (rows g))
                (w (cols g)))
           (let* ((cr (/ h 2))
                  (cc (/ w 2))
                  (kc (at g cr cc))
                  (cells (find-color g kc))
                  (avg-r (/ (for/sum ((p cells)) (first p)) (length cells)))
                  (avg-c (/ (for/sum ((p cells)) (second p)) (length cells)))
                  (dr (if (< avg-r cr) -1 1))
                  (dc (if (< avg-c cc) -1 1)))
             (cellmap g
                      (r c v)
                      (if (and
                            (= (* (- r cr) dc) (* (- c cc) dr))
                            (>= (* (- r cr) dr) 0))
                          kc
                          7))))))