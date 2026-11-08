(rule!
  (let ((dummy 0))
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
    (let* ((cmd (at g 0 0))
           (left (subgrid g 1 0 3 2))
           (right (subgrid g 1 4 3 6))
           (tr (transform-code right cmd))
           (overlap
             (grid-from-fn 3 3
               (lambda (r c)
                 (if (and (not (= (at left r c) 0))
                          (not (= (at tr r c) 0)))
                     7
                     0)))))
      (grid-from-fn 3 3
        (lambda (r c)
          (if (and (= (at overlap r c) 7)
                   (or (and (> r 0) (= (at overlap (- r 1) c) 7))
                       (and (< r 2) (= (at overlap (+ r 1) c) 7))
                       (and (> c 0) (= (at overlap r (- c 1)) 7))
                       (and (< c 2) (= (at overlap r (+ c 1)) 7))
                       (and (> r 0) (> c 0) (= (at overlap (- r 1) (- c 1)) 7))
                       (and (> r 0) (< c 2) (= (at overlap (- r 1) (+ c 1)) 7))
                       (and (< r 2) (> c 0) (= (at overlap (+ r 1) (- c 1)) 7))
                       (and (< r 2) (< c 2) (= (at overlap (+ r 1) (+ c 1)) 7))))
              7
              0))))))
