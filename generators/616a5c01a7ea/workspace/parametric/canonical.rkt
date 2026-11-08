(rule! (lambda (g)
         (let ((n (rows g))
               (w (cols g)))
           (let ((sec-w (/ (- w 2) 3)))
             (grid-from-fn n
                           w
                           (lambda (r c)
                             (if (or (= c sec-w) (= c (+ (* 2 sec-w) 1)))
                                 5
                                 (let ((sec (if (< c sec-w)
                                                0
                                                (if (< c (+ (* 2 sec-w) 1)) 1 2)))
                                       (lc (mod c (+ sec-w 1))))
                                   (cond
                                     ((zero? sec) (at g r lc))
                                     ((= sec 1) (at g (- (- n 1) lc) r))
                                     (else (at g (- (- n 1) r) (- (- sec-w 1) lc))))))))))))