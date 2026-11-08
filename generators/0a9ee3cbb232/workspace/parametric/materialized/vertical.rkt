(rule! (lambda (g)
         (let* ((h (rows g))
                (w (cols g)))
           (let* ((count-segments (lambda (color)
                                    (let loop-c
                                         ((c 0) (count 0))
                                         (cond
                                           ((>= c w) count)
                                           (else (let loop-r
                                                      ((r 0) (in-seg? #f) (cnt count))
                                                      (cond
                                                        ((>= r h) (loop-c (+ c 1) cnt))
                                                        ((= (at g r c) color) (cond
                                                            ((not in-seg?) (loop-r (+ r 1)
                                                                      #t
                                                                      (+ cnt 1)))
                                                            (else (loop-r (+ r 1)
                                                                          #t
                                                                          cnt))))
                                                        (else (loop-r (+ r 1) #f cnt)))))))))
                  (n3 (count-segments 3))
                  (n2 (count-segments 2)))
             (build-grid 2
                         3
                         (r c)
                         (let ((i (+ (* r 3) c)))
                           (cond ((< i n3) 3) ((< i (+ n3 n2)) 2) (else 0))))))))
