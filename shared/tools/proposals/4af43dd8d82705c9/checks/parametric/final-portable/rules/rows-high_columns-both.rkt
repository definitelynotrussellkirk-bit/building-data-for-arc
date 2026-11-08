(rule!
 ;; Two rectangles: a plain EMPTY one and a (widest) SOURCE stamped
 ;; with marker dots. Rebuild the empty rectangle with the markers
 ;; transferred edge-relative: each marker keeps its distance to its
 ;; NEAREST edge on each axis; an exact tie mirrors it to both sides.
 (lambda (g)
   (let ()
     (define bg (at g 0 0))
     (define objs (objects-multicolor g bg))
     (define (colors-of o)
       (unique (map (lambda (p) (at g (first p) (second p)))
                    (obj-cells o))))
     (define blank (find (lambda (o) (= 1 (length (colors-of o)))) objs))
     (define blank-color (first (colors-of blank)))
     (define eh (obj-h blank))
     (define ew (obj-w blank))
     (define source
       (pick-max (filter (lambda (o) (> (length (colors-of o)) 1)) objs)
                 obj-w))
     (define rect-color  ;; the source's majority (frame) color
       (pick-max (colors-of source)
                 (lambda (c) (count-if (lambda (p)
                                         (= (at g (first p) (second p))
                                            c))
                                       (obj-cells source)))))
     (define marker-color
       (find-first (lambda (c) (not (= c rect-color)))
                   (colors-of source)))
     (define markers  ;; marker positions relative to the source bbox
       (map (lambda (p) (list (- (first p) (obj-r1 source))
                              (- (second p) (obj-c1 source))))
            (filter (lambda (p) (= (at g (first p) (second p))
                                   marker-color))
                    (obj-cells source))))
     (define (anchors mr mc)  ;; landing spots in the empty rectangle
       (let* ((bot (- (obj-h source) 1 mr))
              (right (- (obj-w source) 1 mc))
              (rrs (cond ((< mr bot) (list mr))
                         ((> mr bot) (list (- eh 1 bot)))
                         (else (list (- eh 1 bot)))))
              (ccs (cond ((< mc right) (list mc))
                         ((> mc right) (list (- ew 1 right)))
                         (else (list mc (- ew 1 right))))))
         (filter (lambda (rc) (in-bounds? (first rc) (second rc) eh ew))
                 (for*/list ((r rrs) (c ccs)) (list r c)))))
     (paint-cells (empty-grid eh ew blank-color)
                  (flatmap (lambda (m) (anchors (first m) (second m)))
                           markers)
                  marker-color))))