(rule! (lambda (g)
  ;; Crop to content, then select one floor-sized corner.
  (let* ([sub (crop-to-content g 0)]
         [h (quotient (rows sub) 2)]
         [w (quotient (cols sub) 2)]
         [top 0]
         [left (- (cols sub) w)])
    (crop sub top left (- (+ top h) 1) (- (+ left w) 1)))))
