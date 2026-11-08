(rule! (lambda (g)
  ;; Crop to the non-background bounding box
  (let ((sub (crop-to-content g 0)))
    (crop sub 0 0 (- (quotient (rows sub) 2) 1) (- (quotient (cols sub) 2) 1)))))
