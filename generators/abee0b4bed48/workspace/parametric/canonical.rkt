(rule! (lambda (g)
         (let* ((h (rows g))
                (w (cols g)))
           (cellmap g
                    (r c v)
                    (let* ((z (/ c 3))
                           (zc (* z 3))
                           (cnt (+ (+ (for/sum ((cc (range zc (+ zc 3))))
                                        (if (= (at g 0 cc) 5) 1 0))
                                      (for/sum ((cc (range zc (+ zc 3))))
                                        (if (= (at g 1 cc) 5) 1 0)))
                                   (for/sum ((cc (range zc (+ zc 3))))
                                     (if (= (at g 2 cc) 5) 1 0)))))
                      (cond
                        ((= cnt 1) 4)
                        ((= cnt 8) 3)
                        ((= cnt 3) (cond
                            ((and
                               (= (at g 0 zc) 5)
                               (= (at g 0 (+ zc 1)) 5)
                               (= (at g 0 (+ zc 2)) 5)) 6)
                            ((and
                               (= (at g 2 zc) 5)
                               (= (at g 2 (+ zc 1)) 5)
                               (= (at g 2 (+ zc 2)) 5)) 1)
                            (else 9)))
                        (else 0)))))))