(rule!
  (let ((dummy 0))
    (define (apply-transform grid cmd)
      (cond [(= cmd 0) grid]
            [(= cmd 1) (rotate-cw grid)]
            [(= cmd 2) (rotate-180 grid)]
            [(= cmd 3) (transpose grid)]
            [(= cmd 4) (flip-lr grid)]
            [else (flip-ud grid)]))
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
    (let* ((panels (map crop-to-content (split-blank-cols g)))
           (a (first panels))
           (b (second panels))
           (c (third panels))
           (cmd (find-first (lambda (t) (equal? (apply-transform a t) b)) (list 0 1 2 3 4 5))))
      (apply-transform c (if (eq? cmd #f) 0 cmd)))))