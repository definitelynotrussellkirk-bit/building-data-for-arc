(rule!
 ;; The black rectangle is a count-chart template; each nonblack seed labels
 ;; one row. Ignore that rectangle while discovering same-color 8-connected
 ;; objects on the dominant-color canvas. Count objects of each legend color,
 ;; preserving legend order. Crop to the chart and repeat its seed every two
 ;; columns, starting at the original seed column. Other colors do not add rows.
 (lambda (g)
  (let ()
   (define count-scope 'all)
   (define zeros (find-color g 0))
   (define top (min-of first zeros))
   (define bottom (max-of first zeros))
   (define left (min-of second zeros))
   (define right (max-of second zeros))
   (define colors (grid-colors g))
   (define background (for/fold ((best (first colors))) ((c (in-list colors)))
     (if (> (count-color g c) (count-color g best)) c best)))
   (define (in-chart? r c) (and (<= top r bottom) (<= left c right)))
   (define seeds (for*/list ((r (in-range top (+ bottom 1))) (c (in-range left (+ right 1)))
                            #:when (not (= (at g r c) 0)))
     (list (- r top) (- c left) (at g r c))))
   (define field (grid-from-fn (rows g) (cols g)
     (lambda (r c) (if (in-chart? r c) background (at g r c)))))
   (define components (objects-8 field background))
   ;; Each component's measured occupied-cell count is consumed by selection.
   (define records (map (lambda (obj) (list (obj-color obj) (obj-size obj))) components))
   (define ph (+ 1 (- bottom top)))
   (define pw (+ 1 (- right left)))
   (for/fold ((out (grid-from-fn ph pw (lambda (r c) 0)))) ((seed (in-list seeds)))
    (let* ((color (third seed))
           (matching (filter (lambda (rec) (= (first rec) color)) records))
           (maximum (if (null? matching) 0 (apply max (map second matching))))
           (chosen (if (eq? count-scope 'all) matching
                    (filter (lambda (rec) (= (second rec) maximum)) matching)))
           (n (length chosen)))
     (for/fold ((acc out)) ((i (in-range n)))
      (let ((c (+ (second seed) (* 2 i))))
       (if (< c pw) (set-cell acc (first seed) c color) acc))))))))
