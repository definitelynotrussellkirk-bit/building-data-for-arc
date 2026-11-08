(rule!
  (let ()
    (define (split-panels grid)
      (let ((seps (filter (lambda (c) (all? (lambda (r) (= (at grid r c) 9)) (range 0 (rows grid))))
                          (range 0 (cols grid)))))
        (let loop ([remaining (append seps (list (cols grid)))] [start 0] [panels (list)])
          (if (empty? remaining)
              (reverse panels)
              (let ((stop (first remaining)))
                (loop (rest remaining) (+ stop 1)
                      (if (> stop start) (cons (subgrid grid 0 start (- (rows grid) 1) (- stop 1)) panels) panels)))))))
    (define (anti-transpose grid) (rotate-180 (transpose grid)))
    (define (transform-code grid code)
      (cond [(= code 1) grid]
            [(= code 2) (rotate-cw grid)]
            [(= code 3) (rotate-180 grid)]
            [(= code 4) (rotate-ccw grid)]
            [(= code 5) (flip-lr grid)]
            [(= code 6) (flip-ud grid)]
            [(= code 7) (transpose grid)]
            [else (anti-transpose grid)]))
    (let* ((panels (split-panels g))
           (a (first panels))
           (b (second panels))
           (c (third panels))
           (code (let ((hit (find-first (lambda (t) (equal? (transform-code a t) b))
                                        (list 1 2 3 4 5 6 7 8))))
                   (if hit hit 1))))
      (transform-code c code))))