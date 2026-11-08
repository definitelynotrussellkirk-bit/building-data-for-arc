(rule! (lambda (g)
         (let* ((h (rows g))
                (w (cols g)))
           (let* ((bg 9)
                  (new-color 8)
                  (regions (find-0-regions g bg))
                  (objs (objects g bg)))
             (paint-objects-by g
                               objs
                               (lambda (obj)
                                 (with-bbox obj
                                            (r1 c1 r2 c2)
                                            (let* ((has-hole? (for/or ((region regions))
                                                                      (for/and ((p region))
                                                                               (let ((r (fst p))
                                                                                     (c (snd p)))
                                                                                 (and
                                                                                   (> r
                                                                                      r1)
                                                                                   (< r
                                                                                      r2)
                                                                                   (> c
                                                                                      c1)
                                                                                   (< c
                                                                                      c2)))))))
                                              (and has-hole? new-color)))))))))