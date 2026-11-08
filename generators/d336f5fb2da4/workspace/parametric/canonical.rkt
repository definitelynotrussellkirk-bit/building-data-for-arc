(rule!
  (let ((dummy 0))
    (define (cell<? a b)
      (or (< (first a) (first b))
          (and (= (first a) (first b)) (< (second a) (second b)))))
    (define (norm cells) (sort (normalize-cells cells) cell<?))
    (define (rot cells) (norm (rotate-cells-cw cells)))
    (define (flip-h cells)
      (let* ((n (norm cells))
             (rmax (apply max (map first n))))
        (norm (map (lambda (p) (list (- rmax (first p)) (second p))) n))))
    (define shape0 (norm (find-color g 1)))
    (define ctrl (cond [(not (empty? (find-color g 4))) 4]
                       [(not (empty? (find-color g 6))) 6]
                       [(not (empty? (find-color g 7))) 7]
                       [else 4]))
    (define cells (cond [(= ctrl 6) (rot shape0)]
                        [(= ctrl 7) (flip-h shape0)]
                        [else shape0]))
    (define start (first (find-color g 2)))
    (define nxt (first (find-color g 3)))
    (define dr (- (first nxt) (first start)))
    (define dc (- (second nxt) (second start)))
    (let loop ((ar (first start)) (ac (second start)) (out (empty-grid (rows g) (cols g) 0)))
      (let ((placed (map (lambda (p) (list (+ ar (first p)) (+ ac (second p)))) cells)))
        (if (all? (lambda (p) (pos-in-bounds? p (rows g) (cols g))) placed)
            (loop (+ ar dr) (+ ac dc) (paint-cells out placed 8))
            out)))))