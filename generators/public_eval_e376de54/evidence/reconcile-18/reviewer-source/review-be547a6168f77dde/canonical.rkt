(rule!
 ;; Parallel monochrome segments share an aligned starting OR ending baseline.
 ;; Sort them across that baseline and read the spatially middle segment's length.
 ;; Normalize every segment to that length from its aligned endpoint, clipping at
 ;; the canvas and preserving colors. The optional policy highlights the segment
 ;; with most actually changed cells, counting added AND erased cells after clipping.
 ;; The admitted grammar has odd segment count, a unique modal background and a
 ;; unique edit winner. Ties in general inputs use perpendicular spatial order.
 (lambda (g)
  (let ()
   (define output-policy "all_lines")
   (define bg (mode g -1))
   (define objects-list (objects-8 g bg))
   (define (ordered o) (sort (obj-cells o) cell<))
   (define example (ordered (first (filter (lambda (o) (> (obj-size o) 1)) objects-list))))
   (define dr (- (first (second example)) (first (first example))))
   (define dc (- (second (second example)) (second (first example))))
   (define (along p) (+ (* dr (first p)) (* dc (second p))))
   (define (across o) (- (* dr (second (first (ordered o)))) (* dc (first (first (ordered o))))))
   (define segments (sort objects-list < #:key across))
   (define start-level (along (first (ordered (first segments)))))
   (define from-start? (andmap (lambda (o) (= start-level (along (first (ordered o))))) segments))
   (define rr (if from-start? dr (- dr)))
   (define cc (if from-start? dc (- dc)))
   (define canonical-target (obj-size (list-ref segments (quotient (length segments) 2))))
   (define target
    (cond
     [(equal? output-policy "median_length") (list-ref (sort (map obj-size segments) <) (quotient (length segments) 2))]
     [(equal? output-policy "max_length") (apply max (map obj-size segments))]
     [else canonical-target]))
   (define (anchor o) (if from-start? (first (ordered o)) (last (ordered o))))
   (define (normalized o)
    (let ((p (anchor o)))
     (for/list ((i (range target))
       #:when (in-bounds? (+ (first p) (* i rr)) (+ (second p) (* i cc)) h w))
      (list (+ (first p) (* i rr)) (+ (second p) (* i cc))))))
   (define (score o)
    (let* ((old (obj-size o)) (new (length (normalized o))))
     (cond
      [(equal? output-policy "requested_edit") (abs (- target old))]
      [(equal? output-policy "longest_input") old]
      [(equal? output-policy "shortest_input") (- old)]
      [(equal? output-policy "growth_only") (max 0 (- new old))]
      [(equal? output-policy "shrink_only") (max 0 (- old new))]
      [(equal? output-policy "largest_rendered") new]
      [(equal? output-policy "ignore_singletons") (if (= old 1) -1 (abs (- new old)))]
      [else (abs (- new old))])))
   (define selected (cond [(equal? output-policy "first_line") (first segments)]
                          [(equal? output-policy "last_line") (last segments)]
                          [else (pick-max segments score)]))
   (define normalized-grid
    (for/fold ((out (empty-grid h w bg))) ((o segments))
     (recolor-cells out (normalized o) (obj-color o))))
   (if (equal? output-policy "all_lines") normalized-grid
    (recolor-cells normalized-grid (normalized selected) 8)))))
