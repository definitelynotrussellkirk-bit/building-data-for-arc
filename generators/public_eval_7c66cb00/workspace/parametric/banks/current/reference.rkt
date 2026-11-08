(rule!
 ;; Separate each monochrome source piece above the horizontal bands.
 ;; Match its original color to a band's interior color; preserve its columns,
 ;; bottom-align it to that band's floor, and paint in that band's rail color.
 ;; Components are independently aligned, not sequentially piled up.
 (lambda (g)
  (let ()
   (define output-policy "all_landings")
   (define bg (at g 0 0))
   (define band-rows
    (filter (lambda (r)
      (and (= (at g r 0) (at g r (- w 1)))
           (not (= (at g r 0) (at g r 1)))
           (not (= (at g r 1) bg))
           (for/and ((c (range 1 (- w 1)))) (= (at g r c) (at g r 1)))))
      (range h)))
   (define bands
    (for/list ((r band-rows)
       #:when (or (= r 0) (not (member (- r 1) band-rows))
                  (not (= (at g (- r 1) 1) (at g r 1)))))
     (list r
       (let loop ((end r))
        (if (and (member (+ end 1) band-rows)
                 (= (at g (+ end 1) 1) (at g r 1))) (loop (+ end 1)) end))
       (at g r 1) (at g r 0))))
   (define top (if (null? bands) h (first (first bands))))
   (define pieces (objects (subgrid g 0 0 (- top 1) (- w 1)) bg))
   (define deliveries
    (for/list ((o pieces))
     (let ((b (for/first ((b bands) #:when (= (third b) (obj-color o))) b)))
      (list o b
       (if b (map (lambda (p) (list (+ (first p) (- (second b) (obj-r2 o))) (second p)))
                  (obj-cells o)) '())))))
   (define cleared
    (for/fold ((out g)) ((d deliveries))
     (if (second d) (recolor-cells out (obj-cells (first d)) bg) out)))
   (define landed
    (for/fold ((out cleared)) ((d deliveries))
     (if (second d) (recolor-cells out (third d) (fourth (second d))) out)))
   (define mask
    (for/fold ((out (empty-grid h w -1))) ((d deliveries))
     (if (second d) (recolor-cells out (third d) (fourth (second d))) out)))
   (define groups (objects mask -1))
   (define selected
    (cond
     ((or (equal? output-policy "all_landings") (null? groups)) '())
     ((equal? output-policy "original_largest")
      (third (pick-max deliveries (lambda (d) (obj-size (first d))))))
     ((equal? output-policy "most_color")
      (let ((col (pick-max (grid-colors mask -1) (lambda (c) (count-color mask c)))))
       (find-color mask col)))
     ((equal? output-policy "most_pieces")
      (let* ((b (pick-max bands (lambda (b)
                   (length (filter (lambda (d) (equal? (second d) b)) deliveries)))))
             (parts (filter (lambda (o) (and (>= (obj-r1 o) (first b))
                                             (<= (obj-r2 o) (second b)))) groups)))
       (obj-cells (pick-max parts obj-size))))
     ((equal? output-policy "per_band")
      (apply append
       (for/list ((b bands))
        (let ((parts (filter (lambda (o) (and (>= (obj-r1 o) (first b))
                            (<= (obj-r2 o) (second b)))) groups)))
         (if (null? parts) '() (obj-cells (pick-max parts obj-size)))))))
     ((equal? output-policy "smallest") (obj-cells (pick-min groups obj-size)))
     ((equal? output-policy "first") (obj-cells (first groups)))
     ((equal? output-policy "last") (obj-cells (last groups)))
     ((equal? output-policy "exact_nine")
      (apply append (map obj-cells (filter (lambda (o) (= (obj-size o) 9)) groups))))
     (else (obj-cells (pick-max groups obj-size)))))
   (recolor-cells landed selected 9))))
