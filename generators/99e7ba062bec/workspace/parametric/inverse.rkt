(rule!
  ;; Infer the same first A->B transform as the canonical rule, then apply its
  ;; inverse to panel C. Quarter-turns swap; all other supported transforms are
  ;; self-inverse.
  (let ((dummy 0))
    (define (apply-cmd grid code)
      (cond [(= code 1) grid]
            [(= code 2) (rotate-cw grid)]
            [(= code 3) (rotate-180 grid)]
            [(= code 4) (rotate-ccw grid)]
            [(= code 5) (flip-lr grid)]
            [(= code 6) (flip-ud grid)]
            [else (transpose grid)]))
    (define (inverse-cmd code)
      (cond [(= code 2) 4]
            [(= code 4) 2]
            [else code]))
    (define (zero-col? grid c)
      (all? (lambda (r) (= (at grid r c) 0)) (range 0 (rows grid))))
    (define (split-panels grid)
      (let loop ([c 0] [panels (list)])
        (cond [(>= c (cols grid)) (reverse panels)]
              [(zero-col? grid c) (loop (+ c 1) panels)]
              [else
               (let scan ([stop c])
                 (if (or (>= stop (cols grid)) (zero-col? grid stop))
                     (loop (+ stop 1)
                           (cons (subgrid grid 0 c (- (rows grid) 1) (- stop 1)) panels))
                     (scan (+ stop 1))))])))
    (let* ((panels (map crop-to-content (split-panels g)))
           (a (first panels))
           (b (second panels))
           (c (third panels))
           (code (first (filter (lambda (k) (equal? (crop-to-content (apply-cmd a k)) b))
                                (range 1 8)))))
      (crop-to-content (apply-cmd c (inverse-cmd code))))))
