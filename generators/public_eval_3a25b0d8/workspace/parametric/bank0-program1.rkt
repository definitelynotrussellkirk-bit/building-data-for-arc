(rule!
 ;; Two disconnected figures share an outline color. One is a colored guide;
 ;; the other is an uncolored target whose enclosed cavities may be deformed.
 ;; Isolate each 8-connected figure before cropping (their bounding boxes can
 ;; overlap). Extract its four-connected enclosed non-outline regions. Match
 ;; regions in spatial order: bounding-box center row, then center column.
 ;; Transfer each guide region's color to the corresponding target cavity;
 ;; preserve the target outline and exterior, returning its tight bounding box.
 (lambda (g)
  (let ()
   (define bg (mode g -1))
   (define figures (objects-multicolor g bg))
   (define (colors obj)
    (remove-duplicates (map (lambda (p) (at g (first p) (second p))) (obj-cells obj))))
   (define target-object (first (filter (lambda (o) (= (length (colors o)) 1)) figures)))
   (define guide-object (first (filter (lambda (o) (> (length (colors o)) 1)) figures)))
   (define wall (first (colors target-object)))
   (define (isolated-crop obj)
    (build-grid (obj-h obj) (obj-w obj) (r c)
     (let ((p (list (+ (obj-r1 obj) r) (+ (obj-c1 obj) c))))
      (if (member p (obj-cells obj)) (at g (first p) (second p)) bg))))
   (define guide (isolated-crop guide-object))
   (define target (isolated-crop target-object))
   (define (region<? a b)
    (let* ((aa (bbox-of-cells a)) (bb (bbox-of-cells b))
           (ay (+ (first aa) (third aa))) (by (+ (first bb) (third bb)))
           (ax (+ (second aa) (fourth aa))) (bx (+ (second bb) (fourth bb))))
     (if (= ay by) (< ax bx) (< ay by))))
   (define (cavities canvas)
    (sort
     (filter
      (lambda (cells)
       (andmap (lambda (p) (and (> (first p) 0) (> (second p) 0)
                                (< (first p) (- (rows canvas) 1))
                                (< (second p) (- (cols canvas) 1)))) cells))
      (find-0-regions (cellmap canvas (r c v) (if (= v wall) wall bg)) bg))
     region<?))
   (define guide-regions (cavities guide))
   (define target-regions (cavities target))
   ;; Parallel clauses deliberately zip the already matched region lists.
   (for/fold ((out target)) ((source-region guide-regions) (target-region target-regions))
    (let ()
     (define paint? (> (length target-region) (length source-region)))
     (define color (at guide (first (first source-region)) (second (first source-region))))
     (if paint? (recolor-cells out target-region color) out))))))
