(rule! (lambda (g)
  (let ((sub (crop-to-content g 0)))
    (crop sub
          (- (rows sub) (quotient (rows sub) 2))
          0
          (- (rows sub) 1)
          (- (quotient (cols sub) 2) 1)))))
