(rule!
 ;; First discover all complete yellow plus centers on the untouched input.
 ;; Join centers when their five-cell footprints overlap (Manhattan distance
 ;; at most two), then count centers in each connected overlap cluster.
 ;; Recolor every footprint in every maximum-size cluster; retain all ties.
 (lambda (g)
  (let ()
   (define offsets (cons (list 0 0) cardinal-deltas))
   (define centers
    (filter (lambda (p)
     (for/and ((d offsets))
      (= (safe-at g (+ (first p) (first d)) (+ (second p) (second d)) -1) 4)))
     (grid-positions g)))
   (define (near? a b)
    (<= (+ (abs (- (first a) (first b))) (abs (- (second a) (second b)))) 2))
   (define (reachable seed)
    (let loop ((seen (list seed)))
     (let ((more (filter (lambda (p) (for/or ((q seen)) (near? p q))) centers)))
      (if (= (length seen) (length more)) more (loop more)))))
   (define scores (map (lambda (p) (length (reachable p))) centers))
   (define biggest (if (null? scores) 0 (apply max scores)))
   (define selected (filter (lambda (p) (= (length (reachable p)) biggest)) centers))
   (for/fold ((out g)) ((p selected))
    (for/fold ((acc out)) ((d offsets))
     (set-cell acc (+ (first p) (first d)) (+ (second p) (second d)) 8))))))
