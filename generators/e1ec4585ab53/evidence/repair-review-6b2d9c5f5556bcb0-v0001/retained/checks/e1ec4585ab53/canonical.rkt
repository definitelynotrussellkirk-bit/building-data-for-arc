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
    (define (hcat grids)
      (let* ((out-h (apply max (map rows grids)))
             (out-w (+ (apply + (map cols grids)) (max 0 (- (length grids) 1)))))
        (define (paste out pat left)
          (for*/fold ([acc out])
                     ([r (in-range (rows pat))]
                      [c (in-range (cols pat))]
                      #:when (not (= (at pat r c) 0)))
            (set-cell acc r (+ left c) (at pat r c))))
        (let loop ([out (empty-grid out-h out-w 0)] [remaining grids] [left 0])
          (if (empty? remaining)
              out
              (loop (paste out (first remaining) left)
                    (rest remaining)
                    (+ left (cols (first remaining)) 1))))))
    (define (vcat grids)
      (let* ((out-h (+ (apply + (map rows grids)) (max 0 (- (length grids) 1))))
             (out-w (apply max (map cols grids))))
        (define (paste out pat top)
          (for*/fold ([acc out])
                     ([r (in-range (rows pat))]
                      [c (in-range (cols pat))]
                      #:when (not (= (at pat r c) 0)))
            (set-cell acc (+ top r) c (at pat r c))))
        (let loop ([out (empty-grid out-h out-w 0)] [remaining grids] [top 0])
          (if (empty? remaining)
              out
              (loop (paste out (first remaining) top)
                    (rest remaining)
                    (+ top (rows (first remaining)) 1))))))
    (let* ((row-cmds (list (at g 3 0) (at g 5 0)))
           (col-cmds (list (at g 0 3) (at g 0 5)))
           (src (subgrid g 3 3 5 5))
           (rows-out
             (map (lambda (rcmd)
                    (hcat (map (lambda (ccmd) (transform-code (transform-code src rcmd) ccmd)) col-cmds)))
                  row-cmds)))
      (vcat rows-out))))