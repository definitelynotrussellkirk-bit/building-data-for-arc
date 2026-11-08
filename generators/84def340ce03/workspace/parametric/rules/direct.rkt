(rule! (lambda (g)
         (let* ((h (rows g))
                (w (cols g)))
           (begin
             (define block-cols (quotient w 2))
             (define rings (quotient (* h w) 4))
             (define n (* 2 rings))
             (build-grid n
                         n
                         (r c)
                         (let* ((layer (min r c (- n 1 r) (- n 1 c)))
                                (idx (- rings 1 layer))
                                (br (quotient idx block-cols))
                                (bc (modulo idx block-cols))
                                (ir (+ (* 2 br) (if (< r (quotient n 2)) 0 1)))
                                (ic (+ (* 2 bc) (if (< c (quotient n 2)) 0 1))))
                           (at g ir ic)))))))