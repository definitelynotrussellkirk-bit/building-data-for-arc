(rule! (lambda (g)
         (let* ((h (rows g))
                (w (cols g)))
           (let* ((comps (objects-multicolor g 0))
                  (box-info (map (lambda (o)
                                   (with-bbox o
                                              (r1 c1 r2 c2)
                                              (let* ((marks (for*/sum ((r (range r1
                                                                                 (+ r2
                                                                                    1))) (c (range c1
                                                                                  (+ c2
                                                                                     1)))
                                                                        #:when
                                                                        (and
                                                                          (!= (at g r c)
                                                                              0)
                                                                          (!= (at g r c)
                                                                              1)))
                                                                      1)))
                                                (list marks r1 c1 r2 c2))))
                                 comps))
                  (sorted (sort box-info (lambda (a b) (> (first a) (first b)))))
                  (best (first sorted))
                  (br1 (second best))
                  (bc1 (third best))
                  (br2 (fourth best))
                  (bc2 (fifth best))
                  (bh (+ 1 (- br2 br1)))
                  (bw (+ 1 (- bc2 bc1))))
             (build-grid bh bw (r c) (at g (+ br1 r) (+ bc1 c)))))))
