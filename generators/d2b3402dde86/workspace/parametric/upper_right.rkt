(rule! (lambda (g)
  (let ((sub (crop-to-content g 0)))
    (crop sub
          0
          (- (cols sub) (quotient (cols sub) 2))
          (- (quotient (rows sub) 2) 1)
          (- (cols sub) 1)))))
