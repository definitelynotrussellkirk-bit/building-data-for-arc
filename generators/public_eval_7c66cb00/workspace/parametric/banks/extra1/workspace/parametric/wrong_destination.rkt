(rule!
 ;; Discover color-keyed destination bands with uniform interiors and equal
 ;; left/right markers. Split the upper staging area by color and four-neighbor
 ;; connectivity. Each component falls independently to its own band's floor,
 ;; keeping its columns and shape and adopting the band's marker color. All
 ;; lookups use the untouched input, so recoloring cannot cascade between bands.
 (lambda (g)
  (let ()
   (define background (at g 0 0))
   (define band-rows
    (for/list ((r (range h))
      #:when (and (= (at g r 0) (at g r (- w 1)))
                   (not (= (at g r 0) (at g r 1)))
                   (for/and ((c (range 1 (- w 1)))) (= (at g r c) (at g r 1))))) r))
   (define stage (apply min band-rows))
   (define source (subgrid g 0 0 (- stage 1) (- w 1)))
   (define cleared (grid-from-fn h w (lambda (r c) (if (< r stage) background (at g r c)))))
   (for/fold ((out cleared)) ((obj (objects source background)))
    (let* ((matching (filter (lambda (r) (= (at g r 1) (obj-color obj))) band-rows))
           (marker (at g (apply min matching) 0))
           (shift (- (apply max band-rows) (obj-r2 obj))))
     (for/fold ((painted out)) ((p (obj-cells obj)))
      (set-cell painted (+ (first p) shift) (second p) marker)))))))
