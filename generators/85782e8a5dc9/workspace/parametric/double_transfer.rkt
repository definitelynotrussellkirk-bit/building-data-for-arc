(rule!
  (let ((dummy 0))
    (define (split-blank-cols grid)
      (let loop ([c 0] [panels (list)])
        (cond [(>= c (cols grid)) (reverse panels)]
              [(all? (lambda (r) (= (at grid r c) 0)) (range 0 (rows grid)))
               (loop (+ c 1) panels)]
              [else
               (let scan ([stop c])
                 (if (or (>= stop (cols grid))
                         (all? (lambda (r) (= (at grid r stop) 0)) (range 0 (rows grid))))
                     (loop (+ stop 1)
                           (cons (subgrid grid 0 c (- (rows grid) 1) (- stop 1)) panels))
                     (scan (+ stop 1))))])))
    (define (inside-frame panel)
      (let ((h (rows panel)) (w (cols panel)))
        (if (and (>= h 3) (>= w 3)
                 (all? (lambda (c) (= (at panel 0 c) 5)) (range 0 w))
                 (all? (lambda (c) (= (at panel (- h 1) c) 5)) (range 0 w))
                 (all? (lambda (r) (= (at panel r 0) 5)) (range 0 h))
                 (all? (lambda (r) (= (at panel r (- w 1)) 5)) (range 0 h)))
            (subgrid panel 1 1 (- h 2) (- w 2))
            (crop-to-content panel))))
    (define (anti-transpose grid) (rotate-180 (transpose grid)))
    (define (transform-code grid code)
      (cond [(= code 1) grid]
            [(= code 2) (rotate-cw grid)]
            [(= code 3) (rotate-180 grid)]
            [(= code 4) (transpose grid)]
            [(= code 5) (flip-lr grid)]
            [(= code 6) (flip-ud grid)]
            [(= code 7) (transpose grid)]
            [else (anti-transpose grid)]))
    (let* ((panels (split-blank-cols g))
           (A (inside-frame (first panels)))
           (B (inside-frame (second panels)))
           (C (inside-frame (third panels)))
           (code (let ((hit (find-first (lambda (t) (equal? (transform-code A t) B))
                                        (list 1 2 3 4 5 6 7 8))))
                   (if hit hit 1))))
      (transform-code (transform-code C code) code))))