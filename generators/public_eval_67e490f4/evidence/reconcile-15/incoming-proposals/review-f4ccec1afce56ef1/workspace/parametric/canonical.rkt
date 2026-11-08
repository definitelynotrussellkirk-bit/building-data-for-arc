(rule!
 ;; The unique largest monochrome connected object is a perforated panel.
 ;; Its background-colored holes match scattered objects up to rotation and
 ;; reflection. Each matching object casts one vote for its color, independently
 ;; for each shape class. Fill holes with their most frequent exemplar color and
 ;; return the cropped panel. Numeric color breaks ties; absent colors never vote.
 (lambda (g)
  (let ()
   (define most-frequent #t)
   (define bg (mode g -1))
   (define os (objects g bg))
   (define panel (pick-max os obj-size))
   (define box (obj-bbox panel))
   (define canvas (subgrid g (first box) (second box) (third box) (fourth box)))
   (define holes (objects canvas (obj-color panel)))
   (define (outside? p) (or (< (first p) (first box)) (> (first p) (third box)) (< (second p) (second box)) (> (second p) (fourth box))))
   (define clues (filter (lambda (o) (andmap outside? (obj-cells o))) os))
   (define (matches? x y)
     (member (sort (normalize-cells x) cell<) (all-transforms y)))
   (define winner-table
     (for/list ((hole holes))
       (let* ((matching (filter (lambda (o) (matches? (obj-cells hole) (obj-cells o))) clues))
              (colors (sort (remove-duplicates (map obj-color matching)) <))
              (counts (map (lambda (color) (list color (count-if (lambda (o) (= (obj-color o) color)) matching))) colors))
              (chosen (if most-frequent (pick-max counts second) (pick-min counts second))))
         (list (obj-cells hole) (first chosen)))))
   (for/fold ((out canvas)) ((entry winner-table))
     (recolor-cells out (first entry) (second entry))))))
