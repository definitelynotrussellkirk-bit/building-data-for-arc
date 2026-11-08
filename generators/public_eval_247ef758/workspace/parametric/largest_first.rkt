(rule!
 ;; A uniform nonzero separator divides a template palette from a marked frame.
 ;; Match BOTH opposite frame edges for a source color, on each coordinate axis.
 ;; Center the source's occupied bounding box on EVERY row/column intersection.
 ;; Remove only matched source templates. Preserve frame and nonzero overlap cells.
 ;; Measure matched template area before ordering placement records; larger areas win.
 (lambda (g)
  (let ()
   (define sep (for/first ((c (range 0 w)) #:when (and (> (at g 0 c) 0) (col-uniform? g c))) c))
   (define left (+ sep 1))
   (define colors (remove-duplicates
    (for*/list ((r (range 0 h)) (c (range 0 sep)) #:when (> (at g r c) 0)) (at g r c))))
   (define records
    (filter (lambda (part) (and (not (null? (list-ref part 4))) (not (null? (list-ref part 5)))))
     (for/list ((color colors))
      (let* ((cells (for*/list ((r (range 0 h)) (c (range 0 sep)) #:when (= (at g r c) color)) (list r c)))
             (box (bbox-of-cells cells))
             (rs (for/list ((r (range 1 (- h 1))) #:when (and (= (at g r left) color) (= (at g r (- w 1)) color))) r))
             (cs (for/list ((c (range (+ left 1) (- w 1))) #:when (and (= (at g 0 c) color) (= (at g (- h 1) c) color))) c)))
       (list color cells (quotient (+ (first box) (third box)) 2)
        (quotient (+ (second box) (fourth box)) 2) rs cs (length cells)
        (* (+ 1 (- (third box) (first box))) (+ 1 (- (fourth box) (second box)))))))))
   (define ordered (sort records (lambda (a b) (> (list-ref a 6) (list-ref b 6)))))
   (define cleared (for/fold ((out g)) ((part records)) (erase-cells out (second part) 0)))
   (for/fold ((out cleared)) ((part ordered))
    (for*/fold ((canvas out)) ((rr (list-ref part 4)) (cc (list-ref part 5)) (p (second part)))
     (let ((r (+ rr (- (first p) (third part)))) (c (+ cc (- (second p) (fourth part)))))
      (if (and (in-bounds? r c h w) (>= c left) (= (safe-at canvas r c -1) 0))
       (set-cell canvas r c (first part)) canvas)))))))
