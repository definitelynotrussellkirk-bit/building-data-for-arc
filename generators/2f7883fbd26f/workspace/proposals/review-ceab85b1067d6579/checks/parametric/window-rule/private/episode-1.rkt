(rule! (lambda (g)
         (let* ((h (rows g))
                (w (cols g)))
           (let* ((n (for*/sum ((r (range 0 (- h 1))) (c (range 0 (- w 1))))
                               (if (and
                                     (= 2 (at g r c))
                                     (= 2 (at g r (+ c 1)))
                                     (= 2 (at g (+ r 1) c))
                                     (= 2 (at g (+ r 1) (+ c 1))))
                                   1
                                   0))))
             (encode-bar n 5 1)))))