(rule!
  (let* ((out-h (- (rows g) 1))
         (out-w (- (cols g) 1))
         (matches
           (grid-from-fn out-h out-w
             (lambda (r c)
               (let ((rv (at g (+ r 1) 0))
                     (cv (at g 0 (+ c 1))))
                 (if (= rv cv) rv 0)))))
         (positions
           (for*/list ((r (range 0 out-h))
                       (c (range 0 out-w))
                       #:when (!= (at matches r c) 0))
             (list r c)))
         (anchor (first positions))
         (ar (first anchor))
         (ac (second anchor)))
    (grid-from-fn out-h out-w
      (lambda (r c)
        (at matches
            (modulo (+ r ar) out-h)
            (modulo (+ c ac) out-w))))))
