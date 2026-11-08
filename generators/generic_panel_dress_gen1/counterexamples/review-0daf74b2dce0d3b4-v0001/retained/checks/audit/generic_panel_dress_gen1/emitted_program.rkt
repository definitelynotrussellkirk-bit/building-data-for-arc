(rule!
 ;; PANEL DRESS-UP: solid color PANELS tile a block (they touch each
 ;; other), each pierced by field-colored dots; isolated SHAPES with
 ;; enclosed holes lie on the field. Each panel takes the shape whose
 ;; hole count equals its dot count: output the panel block with every
 ;; panel refilled solid, its shape pasted centered (color kept, holes
 ;; showing the panel color).
 (lambda (g)
   (let ()
     (define h (rows g))
     (define w (cols g))
     (define bg (mode g))
     (define objs (objects g bg))
     (define (touches? a b)
       (< 0 (count-if
             (lambda (p)
               (< 0 (count-if
                     (lambda (q)
                       (= 1 (+ (abs (- (first p) (first q)))
                               (abs (- (second p) (second q))))))
                     (obj-cells b))))
             (obj-cells a))))
     (define panels
       (filter (lambda (o)
                 (< 0 (count-if (lambda (u) (and (not (equal? u o))
                                                 (touches? o u)))
                                objs)))
               objs))
     (define shapes
       (filter (lambda (o)
                 (= 0 (count-if (lambda (p) (equal? p o)) panels)))
               objs))
     (define (holes o)
       ;; enclosed bg regions in o's padded bbox (count, cells kept)
       (let* ((bb (obj-bbox o))
              (r1 (first bb)) (c1 (second bb))
              (r2 (nth bb 2)) (c2 (nth bb 3))
              (mask (paint-cells
                     (empty-grid (+ (- r2 r1) 3) (+ (- c2 c1) 3) 1)
                     (map (lambda (p) (list (+ (- (first p) r1) 1)
                                            (+ (- (second p) c1) 1)))
                          (obj-cells o))
                     0)))
         (length (filter (lambda (q) (not (bordering? q mask)))
                         (objects mask 0)))))
     (define prs (flatmap (lambda (o) (map first (obj-cells o))) panels))
     (define pcs (flatmap (lambda (o) (map second (obj-cells o))) panels))
     (define br1 (reduce min (first prs) prs))
     (define bc1 (reduce min (first pcs) pcs))
     (define br2 (reduce max (first prs) prs))
     (define bc2 (reduce max (first pcs) pcs))
     (reduce
      (lambda (out pan)
        (let* ((pb (obj-bbox pan))
               (pr1 (first pb)) (pc1 (second pb))
               (pr2 (nth pb 2)) (pc2 (nth pb 3))
               (pcol (obj-color pan))
               (ndots (holes pan))
               (shp (find-first (lambda (s) (= (holes s) ndots)) shapes))
               (sb (obj-bbox shp))
               (mr (quotient (- (- pr2 pr1) (- (nth sb 2) (first sb))) 2))
               (mc (quotient (- (- pc2 pc1) (- (nth sb 3) (second sb))) 2))
               (filled
                (for*/fold ((o out)) ((r (in-range pr1 (+ pr2 1)))
                                      (c (in-range pc1 (+ pc2 1))))
                  (set-cell o (- r br1) (- c bc1) pcol))))
          (reduce (lambda (o p)
                    (set-cell o
                              (+ (- (+ pr1 mr) br1)
                                 (- (first p) (first sb)))
                              (+ (- (+ pc1 mc) bc1)
                                 (- (second p) (second sb)))
                              (at g (first p) (second p))))
                  filled (obj-cells shp))))
      (empty-grid (+ (- br2 br1) 1) (+ (- bc2 bc1) 1) 0)
      panels))))