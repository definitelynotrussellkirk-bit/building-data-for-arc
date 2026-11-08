(rule!
  (let ((dummy 0))
    (define (cell<? a b)
      (or (< (first a) (first b))
          (and (= (first a) (first b)) (< (second a) (second b)))))
    (define (norm cells) (sort (normalize-cells cells) cell<?))
    (define (rot cells) (norm (rotate-cells-cw cells)))
    (define (flip-v cells)
      (let* ((n (norm cells)) (cmax (apply max (map second n))))
        (norm (map (lambda (p) (list (first p) (- cmax (second p)))) n))))
    (define ctrl (cond [(not (empty? (find-color g 2))) 2]
                       [(not (empty? (find-color g 3))) 3]
                       [(not (empty? (find-color g 4))) 4]
                       [else 2]))
    (define times (cond [(= ctrl 2) 0] [(= ctrl 3) 1] [else 2]))
    (define shape-rot
      (let loop ((k times) (cells (norm (find-color g 1))))
        (if (= k 0) cells (loop (- k 1) (rot cells)))))
    (define shape (if (empty? (find-color g 6)) shape-rot (flip-v shape-rot)))
    (define start (first (find-color g 7)))
    (define nxt (first (find-color g 8)))
    (define dr (- (first nxt) (first start)))
    (define dc (- (second nxt) (second start)))
    (let loop ((ar (first start)) (ac (second start)) (out (empty-grid (rows g) (cols g) 0)))
      (let ((placed (map (lambda (p) (list (+ ar (first p)) (+ ac (second p)))) shape)))
        (if (all? (lambda (p) (pos-in-bounds? p (rows g) (cols g))) placed)
            (loop (+ ar dr) (+ ac dc) (paint-cells out placed 9))
            out)))))