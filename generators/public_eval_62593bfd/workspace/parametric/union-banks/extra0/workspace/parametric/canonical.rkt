(rule!
 ;; Find same-color eight-connected pieces against the modal background. Pieces
 ;; with another congruent shape (rotation/reflection allowed, color ignored)
 ;; rise to the top; unpaired shapes sink to the bottom. Columns stay fixed.
 ;; The optional policy measures four-connected foreground groups AFTER docking
 ;; and highlights the largest one in cyan. Sampled scenes have a unique winner;
 ;; otherwise row-major order breaks ties. Original row-major paint order wins.
 (lambda (g)
  (let ()
   (define output-policy "all_shapes")
   (define bg (mode g -1))
   (define pieces (objects-8 g bg))
   (define (shape o) (sort (normalize-cells (obj-cells o)) cell<))
   (define (rotations cells)
    (let* ((a (sort (normalize-cells cells) cell<))
           (b (sort (normalize-cells (rotate-cells-cw a)) cell<))
           (c (sort (normalize-cells (rotate-cells-cw b)) cell<))
           (d (sort (normalize-cells (rotate-cells-cw c)) cell<))) (list a b c d)))
   (define (same-shape? a b)
    (cond
     [(equal? output-policy "size_match") (= (obj-size a) (obj-size b))]
     [(equal? output-policy "bbox_match") (equal? (sort (list (obj-h a) (obj-w a)) <) (sort (list (obj-h b) (obj-w b)) <))]
     [(equal? output-policy "translation_only") (equal? (shape a) (shape b))]
     [(equal? output-policy "rotations_only") (member (shape a) (rotations (obj-cells b)))]
     [else (member (shape a) (all-transforms (obj-cells b)))]))
   (define (matched? o)
    (for/or ((q pieces)) (and (not (equal? (obj-cells o) (obj-cells q))) (same-shape? o q))))
   (define (destination o)
    (map (lambda (p) (list (+ (- (first p) (obj-r1 o)) (if (matched? o) 0 (- h (obj-h o)))) (second p))) (obj-cells o)))
   (define docked
    (for/fold ((out (empty-grid h w bg))) ((o pieces))
      (recolor-cells out (destination o) (obj-color o))))
   (define mask (cellmap docked (r c v) (if (= v bg) 0 1)))
   (define groups (objects mask 0))
   (define selected
    (cond
     [(null? groups) '()]
     [(equal? output-policy "largest_original") (destination (pick-max pieces obj-size))]
     [(equal? output-policy "largest_color") (find-color docked (pick-max (grid-colors docked bg) (lambda (color) (count-color docked color))))]
     [(equal? output-policy "largest_class")
      (let ((best (pick-max pieces (lambda (o) (for/sum ((q pieces) #:when (same-shape? o q)) (obj-size q))))))
       (append-map destination (filter (lambda (o) (same-shape? best o)) pieces)))]
     [(equal? output-policy "smallest_group") (obj-cells (pick-min groups obj-size))]
     [(equal? output-policy "first_group") (obj-cells (first groups))]
     [(equal? output-policy "last_group") (obj-cells (last groups))]
     [(equal? output-policy "skip_docking")
      (let* ((raw (cellmap g (r c v) (if (= v bg) 0 1))) (original (objects raw 0)))
       (if (null? original) '() (obj-cells (pick-max original obj-size))))]
     [else (obj-cells (pick-max groups obj-size))]))
   (if (equal? output-policy "all_shapes") docked
    (recolor-cells (if (equal? output-policy "skip_docking") g docked) selected 8)))))
