(rule! (lambda (g)
  (let ((sub (crop-to-content g 0)))
    (crop sub
          (- (rows sub) (quotient (rows sub) 2))
          (- (cols sub) (quotient (cols sub) 2))
          (- (rows sub) 1)
          (- (cols sub) 1)))))
