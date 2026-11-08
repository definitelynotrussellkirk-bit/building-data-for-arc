(rule! (lambda (g)
         (let* ((h (rows g))
                (w (cols g)))
           (build-grid h
                       (* w 3)
                       (r c)
                       (let ((i (quotient c w))
                             (lc (modulo c w)))
                         (if (zero? (modulo i 2)) (at g r lc) (at g r (- (- w 1) lc))))))))
