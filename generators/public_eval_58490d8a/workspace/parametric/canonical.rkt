(rule!
 ;; The black rectangle is a counting board. Each colored legend marker names
 ;; a color to count outside the board. Count eight-connected monochrome objects,
 ;; not pixels (diagonally touching cells are one object), ignoring unlisted colors.
 ;; Crop the board and repeat each marker every two columns, once per object.
 (lambda (g)
  (let ()
   (define output-policy "count_all")
   (define black-parts (filter (lambda (o) (= (obj-color o) 0)) (objects g -1)))
   (define board (pick-max black-parts obj-size))
   (define r0 (obj-r1 board))
   (define c0 (obj-c1 board))
   (define r9 (obj-r2 board))
   (define c9 (obj-c2 board))
   (define bh (+ 1 (- r9 r0)))
   (define bw (+ 1 (- c9 c0)))
   (define background
    (mode-list (for/list ((p (grid-positions g))
       #:unless (and (<= r0 (first p) r9) (<= c0 (second p) c9)))
          (at g (first p) (second p)))))
   (define outside (recolor-cells g (positions-in-rect r0 c0 r9 c9) background))
   (define objects-out
    (if (equal? output-policy "four_connected") (objects outside background)
        (objects-8 outside background)))
   (define (object-shape o)
    (map (lambda (p) (list (- (first p) (obj-r1 o)) (- (second p) (obj-c1 o))))
         (sort (obj-cells o) (lambda (a b) (or (< (first a) (first b))
                          (and (= (first a) (first b)) (< (second a) (second b))))))))
   (define entries
    (for/list ((r (range r0 (+ r9 1)))
       #:when (for/or ((c (range c0 (+ c9 1)))) (not (= (at g r c) 0))))
     (let* ((c (for/first ((c (range c0 (+ c9 1))) #:when (not (= (at g r c) 0))) c))
            (color (at g r c))
            (matches (filter (lambda (o) (= (obj-color o) color)) objects-out))
            (n (cond
                 ((equal? output-policy "pixels") (apply + (map obj-size matches)))
                 ((equal? output-policy "shape_classes") (length (remove-duplicates (map object-shape matches))))
                 ((equal? output-policy "include_legend") (+ 1 (length matches)))
                 (else (length matches)))))
      (list (- r r0) (- c c0) color n))))
   (define ordered
    (cond
     ((or (equal? output-policy "count_all") (equal? output-policy "cumulative_input_order")) entries)
     ((equal? output-policy "descending_cumulative") (sort entries (lambda (a b) (> (fourth a) (fourth b)))))
     (else (sort entries (lambda (a b) (< (fourth a) (fourth b)))))))
   (for/fold ((out (empty-grid bh bw 0))) ((index (range (length entries))))
    (let* ((slot (list-ref entries index))
           (item (list-ref ordered index))
           (n (if (or (equal? output-policy "count_all") (equal? output-policy "rank_only"))
                  (fourth item)
                  (for/sum ((k (range (+ index 1)))) (fourth (list-ref ordered k))))))
     (recolor-cells out
       (for/list ((k (range n)) #:when (< (+ (second slot) (* 2 k)) bw))
          (list (first slot) (+ (second slot) (* 2 k))))
       (third item)))))))
