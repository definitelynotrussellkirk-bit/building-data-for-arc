(rule!
 ;; Decode colored anchors into four geometric 4x4 symbols.
 ;; A code immediately southeast of its exemplar is a legend, not a target.
 ;; Match only the exemplar's occupied cells: a real anchor can sit in a blank corner.
 ;; Ignore exemplar pixels, preserve canvas dimensions, and clip edge stamps.
 (lambda (g)
  (let ()
   (define (pixel code r c)
    (cond
     ((= code 2) (if (or (= r 0) (= r 3) (= c 0) (= c 3)) 4 0))
     ((= code 3) (if (or (and (or (= r 0) (= r 3)) (or (= c 1) (= c 2)))
                           (and (or (= c 0) (= c 3)) (or (= r 1) (= r 2)))) 1 0))
     ((= code 5) (if (or (and (< r 2) (< c 2)) (and (>= r 2) (>= c 2))) 6 0))
     ((= code 8) (if (or (= r c) (= (+ r c) 3)) 7 0))
     (else 0)))
   (define (legend? p)
    (let ((r (first p)) (c (second p)) (code (at g (first p) (second p))))
     (and (>= r 4) (>= c 4)
       (for*/and ((i (range 4)) (j (range 4)))
        (or (= (pixel code i j) 0)
            (= (at g (+ (- r 4) i) (+ (- c 4) j)) (pixel code i j)))))))
   (define targets
    (filter (lambda (p) (and (member (at g (first p) (second p)) '(2 3 5 8))
                             (not (legend? p)))) (grid-positions g)))
   (define decoded
    (for*/fold ((out (empty-grid (rows g) (cols g))))
      ((p targets) (i (range 4)) (j (range 4)))
     (let ((v (pixel (at g (first p) (second p)) i j))
           (r (+ (first p) i)) (c (+ (second p) j)))
      (if (and (> v 0) (in-bounds? r c (rows g) (cols g)))
          (set-cell out r c v) out))))
   ;; FINISH
   decoded)))
