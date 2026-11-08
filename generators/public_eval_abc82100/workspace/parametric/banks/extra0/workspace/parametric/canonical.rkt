(rule!
 ;; Each legend has an original-color cell, a replacement-color cell, then a
 ;; stencil origin. Cyan cells define relative offsets; the origin may be empty.
 ;; Split touching parallel masks by the nearest stem axis. Remove all legends,
 ;; then stamp each ORIGINAL marker once, clipped to the canvas. Unmapped colors
 ;; survive. Definition order is row-major; later stamps overwrite collisions.
 ;; The optional selector consumes connected components of the completed stamps.
 (lambda (g)
  (let ()
   (define output-policy "all_stamps")
   (define dirs '((-1 0) (0 1) (1 0) (0 -1)))
   (define (inside p) (and (<= 0 (first p)) (< (first p) h)
                           (<= 0 (second p)) (< (second p) w)))
   (define (shift p d n) (list (+ (first p) (* n (first d)))
                             (+ (second p) (* n (second d)))))
   (define (value p) (at g (first p) (second p)))
   (define gray (filter (lambda (o) (= (obj-color o) 8)) (objects-8 g 0)))
   ;; Record: original color, replacement color, original cell, near cell,
   ;; origin, direction, whole cyan component.
   (define defs
    (for*/list ((p (grid-positions g)) (d dirs)
     #:when (and (not (member (value p) '(0 8)))
                 (inside (shift p d 2))
                 (not (member (value (shift p d 1)) (list 0 8 (value p))))
                 (member (value (shift p d 2)) '(0 8)))
     (o gray)
     #:when (for/or ((q (obj-cells o)))
              (and (<= (abs (- (first q) (first (shift p d 2)))) 1)
                   (<= (abs (- (second q) (second (shift p d 2)))) 1))))
     (list (value p) (value (shift p d 1)) p (shift p d 1)
           (shift p d 2) d (obj-cells o))))
   (define (perp p d)
    (abs (- (* (- (first p) (first (list-ref d 4))) (second (list-ref d 5)))
            (* (- (second p) (second (list-ref d 4))) (first (list-ref d 5))))))
   (define (mask d)
    (filter
     (lambda (p)
      (= (perp p d)
         (apply min (map (lambda (v) (perp p v))
                      (filter (lambda (v) (equal? (list-ref d 6) (list-ref v 6))) defs)))))
     (list-ref d 6)))
   (define erased
    (append (find-color g 8) (apply append (map (lambda (d) (list (list-ref d 2) (list-ref d 3))) defs))))
   (define originals (map first defs))
   (define (seeds d)
    (filter (lambda (p) (not (member p erased))) (find-color g (first d))))
   (define blank
    (grid-from-fn h w (lambda (r c)
     (if (or (member (list r c) erased) (member (at g r c) originals)) 0 (at g r c)))))
   (define stamped
    (for*/fold ((out blank)) ((d defs) (p (seeds d)) (q (mask d)))
      (let ((r (+ (first p) (- (first q) (first (list-ref d 4)))))
            (c (+ (second p) (- (second q) (second (list-ref d 4))))))
       (if (inside (list r c)) (set-cell out r c (second d)) out))))
   (define parts (objects stamped 0))
   (define selected
    (cond
     ((or (equal? output-policy "all_stamps") (null? parts)) '())
     ((equal? output-policy "most_color")
      (find-color stamped
       (pick-max (grid-colors stamped)
        (lambda (v) (if (= v 0) -1 (length (find-color stamped v)))))))
     ((equal? output-policy "largest_template")
      (if (null? defs) '() (find-color stamped (second (pick-max defs (lambda (d) (length (mask d))))))))
     ((equal? output-policy "most_seeds")
      (if (null? defs) '() (find-color stamped (second (pick-max defs (lambda (d) (length (seeds d))))))))
     ((equal? output-policy "first_component") (obj-cells (first parts)))
     ((equal? output-policy "last_component") (obj-cells (last parts)))
     ((equal? output-policy "smallest_component") (obj-cells (pick-min parts obj-size)))
     (else (obj-cells (pick-max parts obj-size)))))
   (recolor-cells stamped selected 9))))
