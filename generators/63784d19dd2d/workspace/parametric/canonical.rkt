(rule!
  (let ((seps (filter (lambda (c) (all? (lambda (r) (= (at g r c) 5)) (range 0 (rows g)))) (range 0 (cols g)))))
    (define (panel start end) (subgrid g 0 start (- (rows g) 1) (- end 1)))
    (define A (panel 0 (first seps)))
    (define B (panel (+ (first seps) 1) (second seps)))
    (define C (panel (+ (second seps) 1) (cols g)))
    (define (xform grid code)
      (cond [(= code 1) grid]
            [(= code 2) (rotate-cw grid)]
            [(= code 3) (rotate-180 grid)]
            [(= code 4) (flip-ud grid)]
            [else (flip-lr grid)]))
    (define code (first (filter (lambda (k) (equal? (xform A k) B)) (list 1 2 3 4 5))))
    (xform C code)))