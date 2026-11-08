(rule!
  (let ((dummy 0))
    (define (apply-transform grid cmd)
      (cond [(= cmd 0) grid]
            [(= cmd 1) (rotate-cw grid)]
            [(= cmd 2) (rotate-180 grid)]
            [(= cmd 3) (transpose grid)]
            [(= cmd 4) (flip-lr grid)]
            [else (flip-ud grid)]))
    (define (marker-command grid)
      (let* ((h (rows grid))
             (w (cols grid))
             (marker
              (first
               (for*/list ([r (in-range h)]
                           [c (in-range w)]
                           #:when (= (at grid r c) 9))
                 (list r c))))
             (r (first marker))
             (c (second marker)))
        (cond [(and (= r 0) (= c 0)) 0]
              [(and (= r 0) (= c (- w 1))) 4]
              [(and (= r (- h 1)) (= c 0)) 5]
              [else 2])))
    (let* ((cmd1 (at g 0 0))
           (clean (set-cell (set-cell g 0 0 0) 0 1 0))
           (obj (crop-to-content clean))
           (first-pass (apply-transform obj cmd1))
           (cmd2 (marker-command first-pass)))
      (apply-transform first-pass cmd2))))