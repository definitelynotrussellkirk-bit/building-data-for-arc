(rule!
 ;; Slide each black 4-component right until it contacts the vertical gray wall.
 ;; Recover enclosed background holes, excluding the exterior and right strip.
 ;; Only hole cells two columns left of the wall project red through its right
 ;; strip. Open notches and holes behind a thicker black border do not project.
 ;; Largest mode selects the eligible cavity of greatest actual area; ties are
 ;; resolved top-to-bottom then left-to-right, never by bounding-box area.
 (lambda (g)
  (let ()
   (define largest? #t)
   (define bg (mode g -1))
   (define wall (for/first ((c (range w)) #:when (for/and ((r (range h))) (= (at g r c) 5))) c))
   (define shapes (filter (lambda (o) (= (obj-color o) 0)) (objects g bg)))
   (define blank (for*/fold ((out g)) ((o shapes) (p (obj-cells o)))
                   (set-cell out (first p) (second p) bg)))
   (define docked
     (for/fold ((out blank)) ((o shapes))
      (let ((delta (- wall 1 (obj-c2 o))))
       (for/fold ((acc out)) ((p (obj-cells o)))
        (set-cell acc (first p) (+ (second p) delta) 0)))))
   (define holes
    (filter (lambda (o)
      (and (= (obj-color o) bg) (> (obj-r1 o) 0) (< (obj-r2 o) (- h 1))
           (> (obj-c1 o) 0) (< (obj-c2 o) (- wall 1))))
      (objects docked -1)))
   (define eligible
    (filter (lambda (o) (ormap (lambda (p) (= (second p) (- wall 2))) (obj-cells o))) holes))
   (define ordered
    (sort eligible (lambda (a b)
     (or (> (obj-size a) (obj-size b))
         (and (= (obj-size a) (obj-size b))
              (or (< (obj-r1 a) (obj-r1 b))
                  (and (= (obj-r1 a) (obj-r1 b)) (< (obj-c1 a) (obj-c1 b)))))))))
   (define selected (if (and largest? (not (null? ordered))) (list (first ordered)) eligible))
   (define signal-rows
    (remove-duplicates
     (append-map (lambda (o) (map first (filter (lambda (p) (= (second p) (- wall 2))) (obj-cells o)))) selected)))
   (for*/fold ((out docked)) ((r signal-rows) (c (range (+ wall 1) w)))
    (set-cell out r c 2)))))
