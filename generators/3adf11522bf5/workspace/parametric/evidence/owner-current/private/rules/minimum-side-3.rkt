(rule! (lambda (g)
         (let* ((h (rows g))
                (w (cols g)))
           (let* ((max-sq (cellmap g
                                   (r c v)
                                   (if (!= v 0)
                                       0
                                       (let loop
                                            ((n 1))
                                            (if (or (>= (+ r n) h) (>= (+ c n) w))
                                                n
                                                (if (for/and ((i (range 0 (+ n 1))))
                                                             (and
                                                               (zero? (at g
                                                                          (+ r n)
                                                                          (+ c i)))
                                                               (zero? (at g
                                                                          (+ r i)
                                                                          (+ c n)))))
                                                    (loop (+ n 1))
                                                    n))))))
                  (gmax (reduce (lambda (a b) (if (> a b) a b))
                                0
                                (flatmap (lambda (r)
                                           (map (lambda (c) (at max-sq r c))
                                                (range 0 w)))
                                         (range 0 h))))
                  (in-large (cellmap g
                                     (r c v)
                                     (for/or ((dr (range 0 gmax)))
                                             (for/or ((dc (range 0 gmax)))
                                                     (let ((sr (- r dr))
                                                           (sc (- c dc)))
                                                       (and
                                                         (>= sr 0)
                                                         (>= sc 0)
                                                         (< sr h)
                                                         (< sc w)
                                                         (>= (at max-sq sr sc) gmax))))))))
             (cellmap g
                      (r c v)
                      (cond
                        ((at in-large r c) 1)
                        ((!= v 0) v)
                        (else (if (for/or ((n (range 3 (+ gmax 1))))
                                          (for/or ((dr (range 0 n)))
                                                  (for/or ((dc (range 0 n)))
                                                          (let ((sr (- r dr))
                                                                (sc (- c dc)))
                                                            (and
                                                              (>= sr 0)
                                                              (>= sc 0)
                                                              (>= (at max-sq sr sc) n)
                                                              (for/and ((i (range 0 n)))
                                                                       (for/and ((j (range 0
                                                                                           n)))
                                                                                (not (at in-large
                                                                                         (+ sr
                                                                                            i)
                                                                                         (+ sc
                                                                                            j))))))))))
                                  1
                                  v))))))))