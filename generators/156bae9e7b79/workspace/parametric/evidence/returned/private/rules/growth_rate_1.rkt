(rule! (lambda (g)
         (let* ((h (rows g))
                (w (cols g)))
           (let* ((hh (rows g))
                  (ww (cols g))
                  (bg 5)
                  (key (for/list ((c (range 0 ww))) (at g 0 c)))
                  (line-col (let loop
                                 ((c 0))
                                 (if (for/or ((r (range 1 hh))) (= (at g r c) 8))
                                     c
                                     (loop (+ c 1)))))
                  (line-top (let loop
                                 ((r 0))
                                 (if (= (at g r line-col) 8) r (loop (+ r 1)))))
                  (line-bottom (let loop
                                    ((r (- hh 1)))
                                    (if (= (at g r line-col) 8) r (loop (- r 1)))))
                  (max-radius (quotient (- ww 1) 2)))
             (build-grid hh
                         ww
                         (r c)
                         (if (and (>= r line-top) (<= r line-bottom))
                             (let ((vis-r (min max-radius (- r line-top))))
                               (if (= c line-col)
                                   8
                                   (if (and
                                         (>= c (- line-col vis-r))
                                         (<= c (+ line-col vis-r)))
                                       (list-ref key c)
                                       bg)))
                             bg))))))
