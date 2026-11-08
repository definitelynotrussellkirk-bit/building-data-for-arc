(rule!
  (let ()
    (define markers (find-color g 1))
    (define cue (first (find-color g 2)))
    (define (distance p q)
      (+ (abs (- (first p) (first q)))
         (abs (- (second p) (second q)))))
    (define (row-key p)
      (+ (* 100 (first p)) (second p)))
    (define (satellite-count p)
      (length
        (filter
          (lambda (q)
            (and (in-bounds? (first q) (second q) (rows g) (cols g))
                 (= (at g (first q) (second q)) 3)))
          (list
            (list (- (first p) 1) (second p))
            (list (+ (first p) 1) (second p))
            (list (first p) (- (second p) 1))
            (list (first p) (+ (second p) 1))))))
    (define selected-marker
      (first
        (sort-by
          markers
          (lambda (p)
            (+ (* 10000 (distance p cue)) (row-key p))))))
    (define selected-radius (satellite-count selected-marker))
    (for/fold ((out (empty-grid (rows g) (cols g) 0)))
              ((p (in-list markers)))
      (paint-cells
        out
        (filter
          (lambda (q)
            (in-bounds? (first q) (second q) (rows g) (cols g)))
          (list
            p
            (list (+ (first p) selected-radius) (+ (second p) selected-radius))
            (list (+ (first p) selected-radius) (- (second p) selected-radius))
            (list (- (first p) selected-radius) (+ (second p) selected-radius))
            (list (- (first p) selected-radius) (- (second p) selected-radius))))
        7))))
