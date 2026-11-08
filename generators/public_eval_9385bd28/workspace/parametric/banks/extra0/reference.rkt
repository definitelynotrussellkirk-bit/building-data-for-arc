(rule!
 ;; Read the isolated two-column color legend, including background-valued fills.
 ;; Opposite same-colored L corners delimit a rectangle. Keep its own markers
 ;; while filling; solid blocks instead recolor entirely. Earlier legend rows
 ;; have higher priority and can overwrite lower rectangles and their markers.
 ;; Unmapped foreground is unchanged unless covered by a filled rectangle.
 (lambda (g)
  (let ()
   (define earlier-wins #t)
   (define bg (mode g -1))
   (define (inside? p b)
    (and (<= (first b) (first p) (third b)) (<= (second b) (second p) (fourth b))))
   (define (end-row rr col)
    (if (or (= rr h) (= (at g rr col) bg)) (- rr 1) (end-row (+ rr 1) col)))
   (define (table? r c)
    (let* ((rr (end-row r c)) (keys (for/list ((y (range r (+ rr 1)))) (at g y c)))
           (b (list r c rr (+ c 1))))
     (and (>= (length keys) 2) (= (length (unique keys)) (length keys))
      (for/or ((y (range r (+ rr 1)))) (not (= (at g y (+ c 1)) bg)))
      (for*/and ((y (range (max 0 (- r 1)) (min h (+ rr 2))))
                 (x (range (max 0 (- c 1)) (min w (+ c 3))))
                 #:when (not (inside? (list y x) b)))
       (= (at g y x) bg)))))
   (define tables
    (for*/list ((r (range h)) (c (range (- w 1)))
                #:when (and (not (= (at g r c) bg)) (or (= r 0) (= (at g (- r 1) c) bg)))
                #:when (table? r c))
     (list r c (end-row r c) (+ c 1))))
   (if (null? tables) g
    (let* ((legend (pick-max tables (lambda (b) (- (third b) (first b)))))
           (entries (for/list ((r (range (first legend) (+ 1 (third legend)))))
                     (list (at g r (second legend)) (at g r (fourth legend)))))
           (masked (grid-from-fn h w (lambda (r c) (if (inside? (list r c) legend) bg (at g r c)))))
           (objs (objects masked bg)))
     (define draw-order (if earlier-wins (reverse entries) entries))
     (define result
      (for/fold ((out g)) ((entry draw-order))
       (define key (first entry))
       (define fill-color (if (= (second entry) 0) bg (second entry)))
       (define matching (filter (lambda (obj) (= (obj-color obj) key)) objs))
       (define ls (filter (lambda (obj) (and (= (obj-size obj) 3) (= (obj-h obj) 2) (= (obj-w obj) 2))) matching))
       (define solids (filter (lambda (obj) (and (>= (obj-h obj) 2) (>= (obj-w obj) 2) (solid-rect? obj))) matching))
       (define solid-records (for/list ((obj solids)) (list (obj-bbox obj) '())))
       (define records
        (append solid-records
         (if (= (length ls) 2)
          (let ((ps (append (obj-cells (first ls)) (obj-cells (second ls)))))
           (list (list (bbox-of-cells ps) ps))) '())))
       (for/fold ((canvas out)) ((record records))
        (define b (first record))
        (define markers (second record))
        (for/fold ((painted canvas)) ((p (positions-in-rect (first b) (second b) (third b) (fourth b))))
         (set-cell painted (first p) (second p) (if (member p markers) key fill-color))))))
     result)))))
