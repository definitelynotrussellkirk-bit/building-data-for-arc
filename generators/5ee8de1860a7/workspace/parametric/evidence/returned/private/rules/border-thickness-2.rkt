(rule!
  ;; alt: (lambda (g) (let ((color (first (filter (lambda (v) (!= v 0)) (grid-colors g))))) (cellmap g (r c v) (if (or (zero? r) (= r (- (rows g) 1)) (zero? c) (= c (- (cols g) 1))) color 0))))
  (lambda (g)
    (define h (rows g))
    (define w (cols g))
    (define color
      (find-first (lambda (v) (!= v 0)) (grid-colors g)))
    (define (border? r c)
      (or (< r 2) (>= r (- h 2)) (< c 2) (>= c (- w 2))))
    (build-grid h w (r c)
      (if (border? r c) color 0))))