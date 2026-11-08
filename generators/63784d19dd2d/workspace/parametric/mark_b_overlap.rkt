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
    (define transformed-c (xform C code))
    (define MARK-COLOR 2)
    (define (overlap-with-b? r c)
      (and (not (= (at transformed-c r c) 0))
           (not (= (at B r c) 0))))
    (define (paint-by-reference source reference overlap?)
      (build-list
       (rows source)
       (lambda (r)
         (build-list
          (cols source)
          (lambda (c)
            (let ((value (at source r c))
                  (occupied? (not (= (at reference r c) 0))))
              (if (and (not (= value 0)) (equal? occupied? overlap?))
                  MARK-COLOR
                  value)))))))
    (define (paint-all source)
      (build-list
       (rows source)
       (lambda (r)
         (build-list
          (cols source)
          (lambda (c)
            (if (= (at source r c) 0) 0 MARK-COLOR))))))
    (paint-by-reference transformed-c B #t)))