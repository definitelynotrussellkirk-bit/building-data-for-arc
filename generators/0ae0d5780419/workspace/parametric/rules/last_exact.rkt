(rule!
  (let ((dummy 0))
    (define (split-panels grid)
      (let ((seps (filter (lambda (c) (all? (lambda (r) (= (at grid r c) 5))
                                                   (range 0 (rows grid))))
                          (range 0 (cols grid)))))
        (let loop ([remaining (append seps (list (cols grid)))]
                   [start 0]
                   [panels (list)])
          (if (empty? remaining)
              (reverse panels)
              (let ((stop (first remaining)))
                (loop (rest remaining)
                      (+ stop 1)
                      (if (> stop start)
                          (cons (subgrid grid 0 start
                                         (- (rows grid) 1) (- stop 1))
                                panels)
                          panels)))))))
    (define (transform-code grid code)
      (cond [(= code 1) grid]
            [(= code 2) (rotate-cw grid)]
            [(= code 3) (rotate-180 grid)]
            [(= code 4) (transpose grid)]
            [(= code 5) (flip-lr grid)]
            [else (flip-ud grid)]))
    (let* ((panels (split-panels g))
           (a (crop-to-content (first panels)))
           (b (crop-to-content (second panels)))
           (c (crop-to-content (third panels)))
           (code (let ((hit (find-first
                              (lambda (t) (equal? (transform-code a t) b))
                              (list 6 5 4 3 2 1))))
                   (if hit hit 1))))
      (transform-code c code))))
