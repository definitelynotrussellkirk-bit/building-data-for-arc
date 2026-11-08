(rule!
  (let ((selector (at g 0 0))
        (cmd (at g 0 1)))
    (define (rect-frame? obj)
      (and (>= (obj-h obj) 3)
           (>= (obj-w obj) 3)
           (= (obj-size obj) (- (* 2 (+ (obj-h obj) (obj-w obj))) 4))))
    (define (apply-cmd grid code)
      (cond [(= code 1) (rotate-cw grid)]
            [(= code 2) (rotate-180 grid)]
            [(= code 3) (flip-lr grid)]
            [(= code 4) (transpose grid)]
            [else grid]))
    (let* ((chosen (first (filter (lambda (obj) (and (rect-frame? obj)
                                                      (= (obj-color obj) selector)))
                                  (objects g 0))))
           (motif (subgrid g (+ (obj-r1 chosen) 1) (+ (obj-c1 chosen) 1)
                          (- (obj-r2 chosen) 1) (- (obj-c2 chosen) 1))))
      (apply-cmd (crop-to-content motif) cmd))))