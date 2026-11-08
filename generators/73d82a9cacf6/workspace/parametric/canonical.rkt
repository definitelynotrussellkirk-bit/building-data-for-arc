(rule!
  (let ((dummy 0))
    (define (crop-object obj) (subgrid g (obj-r1 obj) (obj-c1 obj) (obj-r2 obj) (obj-c2 obj)))
    (define (hole-count obj)
      ;; Same shape, translated so its bbox starts at (0,0)
      (let* ((norm (normalize-cells (obj-cells obj)))
             ;; Bounding box enclosing the cells
             (bb (bbox-of-cells norm))
             (h (+ (third bb) 3))
             (w (+ (fourth bb) 3))
             (occ (map (lambda (p) (list (+ (first p) 1) (+ (second p) 1))) norm)))
        (define (free? r c) (not (member? (list r c) occ)))
        (let loop ([remaining (filter (lambda (p) (free? (first p) (second p)))
                                      (positions-in-rect 0 0 (- h 1) (- w 1)))]
                   [holes 0])
          (if (empty? remaining)
              holes
              (let* ((p (first remaining))
                     (region (connected-region (empty-grid h w 0) (first p) (second p)
                                (lambda (r c v) (free? r c)) 4))
                     (touch? (any? (lambda (q) (or (= (first q) 0) (= (second q) 0)
                                                    (= (first q) (- h 1)) (= (second q) (- w 1))))
                                   region)))
                (loop (filter (lambda (q) (not (member? q region))) remaining)
                      (if touch? holes (+ holes 1))))))))
    (define (paste out pat left)
      (for*/fold ([acc out])
                 ([r (in-range (rows pat))]
                  [c (in-range (cols pat))]
                  #:when (not (= (at pat r c) 0)))
        (set-cell acc r (+ left c) (at pat r c))))
    (let* ((items (sort (map (lambda (obj) (list (hole-count obj) (- (obj-size obj)) (obj-color obj) (crop-object obj)))
                             (objects g 0))
                        (lambda (a b)
                          (cond [(not (= (first a) (first b))) (< (first a) (first b))]
                                [(not (= (second a) (second b))) (< (second a) (second b))]
                                [else (< (third a) (third b))]))))
           (crops (map fourth items))
           (out-h (apply max (map rows crops)))
           (out-w (+ (apply + (map cols crops)) (max 0 (- (length crops) 1)))))
      (let loop ([out (empty-grid out-h out-w 0)] [remaining crops] [left 0])
        (if (empty? remaining)
            out
            (loop (paste out (first remaining) left)
                  (rest remaining)
                  (+ left (cols (first remaining)) 1)))))))