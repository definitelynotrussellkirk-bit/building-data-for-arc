(rule!
  (let ((dummy 0))
    (define (same-pos? a b)
      (and (= (fst a) (fst b)) (= (snd a) (snd b))))
    (define (pos-in? p cells)
      (any? (lambda (q) (same-pos? p q)) cells))
    (define proto
      (first
        (filter
          (lambda (obj) (and (= (obj-color obj) 9) (> (obj-size obj) 1)))
          (objects g 0))))
    (define shape (normalize-cells (obj-cells proto)))
    (define (transform code cells)
      (cond
        [(= code 1) (normalize-cells cells)]
        [(= code 2) (normalize-cells (rotate-cells-cw cells))]
        [(= code 3) (normalize-cells (flip-cells-lr cells))]
        [else (normalize-cells (rotate-cells-cw (flip-cells-lr cells)))]))
    (define anchors
      (filter
        (lambda (p)
          (and (> (first p) 0)
               (= (third p) 6)
               (member? (cell-at g (- (first p) 1) (second p)) (list 1 2 3 4))))
        (grid-cells g)))
    (define stamp-cells
      (flatmap
        (lambda (a)
          (let* ((ar (first a))
                 (ac (second a))
                 (code (cell-at g (- ar 1) ac))
                 (shp (transform code shape)))
            (map (lambda (p) (list (+ ar (fst p)) (+ ac (snd p)))) shp)))
        anchors))
    (grid-from-fn h w
      (lambda (r c)
        (if (and (in-bounds? r c h w) (pos-in? (list r c) stamp-cells))
            8
            (cell-at g r c))))))