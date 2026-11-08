(rule!
 ;; Rotate every horizontal three-cell orange gate into a vertical magenta
 ;; barrier, making cyan elbows on either side. On each resulting simple cyan
 ;; track, gather its original green endpoint tokens at the lower endpoint,
 ;; packed along the track without loss. Flat tracks keep their token positions.
 ;; Thus the new gate-derived topology, not the old horizontal rails, controls
 ;; both the destination and the number of tokens that settle there.
 (lambda (g)
  (let ()
   (define prefer-lower? #t)
   (define initial (recolor g 3 8))
   (define gates
    (filter (lambda (o) (and (= (obj-color o) 7) (= (obj-size o) 3)
                            (= (obj-h o) 1) (= (obj-w o) 3)
                            (> (obj-r1 o) 0) (< (obj-r1 o) (- h 1))))
            (objects g 0)))
   (define rotated
    (for/fold ((out initial)) ((o gates))
     (let* ((r (obj-r1 o)) (c (+ (obj-c1 o) 1))
            (sides (set-cell (set-cell out r (- c 1) 8) r (+ c 1) 8)))
      (for/fold ((z sides)) ((rr (range (- r 1) (+ r 2))))
       (set-cell z rr c 6)))))
   (define routing-grid rotated)
   (define cyan (filter (lambda (o) (= (obj-color o) 8)) (objects routing-grid 0)))
   (define (neighbors p cells)
    (filter (lambda (q) (member q cells))
     (map (lambda (d) (list (+ (first p) (first d)) (+ (second p) (second d)))) cardinal-deltas)))
   (define (walk p prev cells left)
    (if (<= left 0) '()
     (let ((next (filter (lambda (q) (not (equal? q prev))) (neighbors p cells))))
      (cons p (if (null? next) '() (walk (first next) p cells (- left 1)))))))
   (for/fold ((out rotated)) ((o cyan))
    (let* ((cells (obj-cells o))
           (tokens (filter (lambda (p) (= (at g (first p) (second p)) 3)) cells))
           (ends (sort (filter (lambda (p) (<= (length (neighbors p cells)) 1)) cells) cell<))
           (destinations
            (if (or (null? tokens) (not (= (length ends) 2))
                    (= (first (first ends)) (first (second ends))))
             tokens
             (take (walk (if prefer-lower? (second ends) (first ends)) '() cells (length cells))
                   (length tokens)))))
     (for/fold ((z out)) ((p destinations))
      (set-cell z (first p) (second p) 3)))))))
