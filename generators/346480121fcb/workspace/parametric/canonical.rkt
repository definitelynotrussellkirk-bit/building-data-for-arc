(rule!
  (let* ((sel (at g 0 0))
         (key (at g 0 (- (cols g) 1)))
         (body (subgrid g 1 0 (- (rows g) 1) (- (cols g) 1)))
         (chosen (first (filter (lambda (obj) (= (obj-color obj) sel)) (objects body 0))))
         (crop (subgrid body (obj-r1 chosen) (obj-c1 chosen) (obj-r2 chosen) (obj-c2 chosen)))
         (tf (cond [(= key 2) (rotate-cw crop)]
                   [(= key 3) (flip-lr crop)]
                   [(= key 4) (transpose crop)]
                   [(= key 5) (rotate-180 crop)]
                   [else crop])))
    (crop-to-content tf)))