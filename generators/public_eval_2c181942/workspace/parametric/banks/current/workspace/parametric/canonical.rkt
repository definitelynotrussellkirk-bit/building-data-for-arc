(rule!
 ;; A four-color 4x4 hollow hub has one centered two-cell key on each side.
 ;; Keep that hub, erase source objects, and dock loose pieces of matching colors.
 ;; Rotations, not reflections, orient the centered contiguous two-cell neck
 ;; toward the destination key; rectangles with equivalent rotations are harmless.
 ;; Ignore colors absent from the hub. Preserve the original canvas and background.
 ;; Alternative: dock at the spatially opposite slot while retaining piece colors.
 (lambda (g)
  (let ()
   (define selection "matching")
   (define rival "")
   (define bg (mode g -1))
   (define groups (objects-multicolor g bg))
   (define (colors o)
    (remove-duplicates (map (lambda (p) (at g (first p) (second p))) (obj-cells o))))
   (define hub (first (filter (lambda (o) (> (length (colors o)) 1)) groups)))
   (define hr (obj-r1 hub))
   (define hc (obj-c1 hub))
   (define keys (list (at g hr (+ hc 1)) (at g (+ hr 1) (+ hc 3))
                      (at g (+ hr 3) (+ hc 1)) (at g (+ hr 1) hc)))
   (define parts (filter (lambda (o) (and (= (length (colors o)) 1)
                                        (member (first (colors o)) keys))) groups))
   (define selected (if (equal? rival "only_largest") (list (pick-max parts obj-size)) parts))
   (define base-shift (if (equal? selection "matching") 0 2))
   (define shift (cond [(equal? rival "other_setting") (- 2 base-shift)]
                       [(equal? rival "clockwise_slots") 1]
                       [(equal? rival "counterclockwise_slots") 3]
                       [else base-shift]))
   (define (color-index color ks)
    (for/first ([i (in-range 4)] #:when (= color (list-ref ks i))) i))
   (define (neck? shape side color)
    (let* ([cells (find-color shape color)]
           [edge (cond [(= side 0) (map second (filter (lambda (p) (= (first p) (- (rows shape) 1))) cells))]
                       [(= side 1) (map first (filter (lambda (p) (= (second p) 0)) cells))]
                       [(= side 2) (map second (filter (lambda (p) (= (first p) 0)) cells))]
                       [else (map first (filter (lambda (p) (= (second p) (- (cols shape) 1))) cells))])]
           [sorted-edge (sort edge <)]
           [span (if (even? side) (cols shape) (rows shape))])
     (and (= (length sorted-edge) 2) (= (second sorted-edge) (+ (first sorted-edge) 1))
          (= (+ (* 2 (first sorted-edge)) 2) span))))
   (define (placed o)
    (let* ([color (first (colors o))]
           [dx (- (+ (obj-c1 o) (obj-c2 o)) (+ (* 2 hc) 3))]
           [dy (- (+ (obj-r1 o) (obj-r2 o)) (+ (* 2 hr) 3))]
           [key-side (cond [(equal? rival "fixed_color_order") (color-index color (sort keys <))]
                           [(equal? rival "source_position")
                            (if (>= (abs dx) (abs dy)) (if (>= dx 0) 1 3) (if (>= dy 0) 2 0))]
                           [else (color-index color keys)])]
           [side (modulo (+ key-side shift) 4)]
           [source (subgrid g (obj-r1 o) (obj-c1 o) (obj-r2 o) (obj-c2 o))]
           [oriented (if (equal? rival "skip_rotation") source
             (first (filter (lambda (shape) (neck? shape side color))
                     (list source (rotate-cw source) (rotate-180 source) (rotate-ccw source)))))]
           [shape (if (equal? rival "mirror_piece")
                      (if (even? side) (flip-lr oriented) (flip-ud oriented)) oriented)]
           [gap (if (equal? rival "extra_gap") 1 0)]
           [dr (cond [(= side 0) (- hr (rows shape) gap)] [(= side 2) (+ hr 4 gap)]
                     [else (- (+ hr 2) (quotient (rows shape) 2))])]
           [dc (cond [(= side 1) (+ hc 4 gap)] [(= side 3) (- hc (cols shape) gap)]
                     [else (- (+ hc 2) (quotient (cols shape) 2))])])
     (map (lambda (p) (list (+ dr (first p)) (+ dc (second p)) color)) (find-color shape color))))
   ;; Stage A supplies an input-dependent list of oriented, translated cells.
   (define placements (map placed selected))
   (define base (if (equal? rival "keep_sources") g
      (paint-cells (empty-grid (rows g) (cols g) bg)
        (map (lambda (p) (list (first p) (second p) (at g (first p) (second p)))) (obj-cells hub)))))
   ;; Stage B consumes only those placements and the preserved hub.
   (define out (for/fold ([result base]) ([cells (in-list placements)]) (paint-cells result cells)))
   (define result (if (equal? rival "fill_hub")
      (paint-cells out (positions-in-rect (+ hr 1) (+ hc 1) (+ hr 2) (+ hc 2)) (first keys)) out))
   (if (equal? rival "crop_canvas") (crop-to-content result bg) result))))
