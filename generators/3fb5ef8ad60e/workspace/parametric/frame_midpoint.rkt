(rule!
  (lambda (g)
    (let* ((h (rows g))
           (w (cols g))
           (positions
             (flatmap
               (lambda (r) (map (lambda (c) (cons r c)) (range 0 w)))
               (range 0 h))))
      (define (block-color? v)
        (and (!= v 0) (!= v 8)))
      (define cells
        (filter (lambda (p) (block-color? (at g (fst p) (snd p)))) positions))
      (define frame-cells
        (filter (lambda (p) (= (at g (fst p) (snd p)) 8)) positions))
      (define colors
        (unique (map (lambda (p) (at g (fst p) (snd p))) cells)))
      (define (center color)
        (let* ((pts (filter (lambda (p) (= (at g (fst p) (snd p)) color)) cells))
               (n (length pts)))
          (list color
                (/ (for/sum ((p pts)) (fst p)) n)
                (/ (for/sum ((p pts)) (snd p)) n))))
      (define blocks (map center colors))
      (define mid-r
        (/ (+ (min-list (map fst frame-cells))
              (max-list (map fst frame-cells)))
           2))
      (define mid-c
        (/ (+ (min-list (map snd frame-cells))
              (max-list (map snd frame-cells)))
           2))
      (define (quadrant v mid) (if (<= v mid) 0 1))
      (reduce
        (lambda (out block)
          (set-cell out
                    (quadrant (second block) mid-r)
                    (quadrant (third block) mid-c)
                    (first block)))
        (list (list 0 0) (list 0 0))
        blocks))))
