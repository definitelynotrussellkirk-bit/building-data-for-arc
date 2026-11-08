(rule! (lambda (g)
         (let* ((h (rows g))
                (w (cols g)))
           (let* ((zero-regions (objects g 5)))
             (paint-objects-by g
                               zero-regions
                               (lambda (obj)
                                 (with-bbox obj
                                            (r1 c1 r2 c2)
                                            (let* ((top-wall (and
                                                               (> r1 0)
                                                               (for/and ((c (range c1
                                                                                   (+ c2
                                                                                      1))))
                                                                        (= (at g
                                                                               (- r1 1)
                                                                               c)
                                                                           5))))
                                                   (bottom-wall (and
                                                                  (< r2 (- h 1))
                                                                  (for/and ((c (range c1
                                                                                      (+ c2
                                                                                         1))))
                                                                           (= (at g
                                                                                  (+ r2
                                                                                     1)
                                                                                  c)
                                                                              5))))
                                                   (left-wall (or
                                                                (zero? c1)
                                                                (for/and ((r (range r1
                                                                                    (+ r2
                                                                                       1))))
                                                                         (= (at g
                                                                                r
                                                                                (- c1 1))
                                                                            5))))
                                                   (right-wall (or
                                                                 (= c2 (- w 1))
                                                                 (for/and ((r (range r1
                                                                                     (+ r2
                                                                                        1))))
                                                                          (= (at g
                                                                                 r
                                                                                 (+ c2
                                                                                    1))
                                                                             5)))))
                                              (and
                                                (and
                                                  (zero? (obj-color obj))
                                                  top-wall
                                                  bottom-wall
                                                  left-wall
                                                  right-wall
                                                  (not (and
                                                         (zero? c1)
                                                         (zero? c2)
                                                         (> r2 r1))))
                                                4)))))))))