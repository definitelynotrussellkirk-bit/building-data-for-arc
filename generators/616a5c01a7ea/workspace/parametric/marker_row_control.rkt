(rule! (lambda (g)
  (let* ((n (rows g))
         (w (cols g))
         (sec-w (/ (- w 2) 3))
         (middle
          (grid-from-fn n sec-w
            (lambda (r c)
              (at g (- (- n 1) c) r))))
         (marker (first (find-color middle 8)))
         (lower-half? (>= (* 2 (first marker)) n)))
    (grid-from-fn n w
      (lambda (r c)
        (cond
          ((= c sec-w) 5)
          ((= c (+ (* 2 sec-w) 1)) 5)
          ((< c sec-w) (at g r c))
          ((< c (+ (* 2 sec-w) 1))
           (at middle r (- c (+ sec-w 1))))
          (else
           (let ((lc (- c (+ (* 2 sec-w) 2))))
             (if lower-half?
                 (at g lc (- (- n 1) r))
                 (at g (- (- n 1) r) (- (- sec-w 1) lc)))))))))))
