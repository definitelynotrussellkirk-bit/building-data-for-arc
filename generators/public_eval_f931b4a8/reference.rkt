(rule!
 ;; Split the even square into four equal quadrants. Nonzero pixels in the
 ;; upper-left and upper-right count the requested output rows and columns.
 ;; Expand each lower-left palette pixel to a quadrant-sized constant block.
 ;; Repeat the lower-right stencil over that backing: nonzero stencil pixels
 ;; overwrite it and zero pixels expose it. An entirely absent stencil means
 ;; repeat the palette directly, without block expansion. Crop to the counts.
 (lambda (g)
  (let ()
   (define side (quotient (rows g) 2))
   (define output-height
    (for*/sum ((r (range side)) (c (range side))) (if (= (at g r c) 0) 0 1)))
   (define output-width
    (for*/sum ((r (range side)) (c (range side))) (if (= (at g r (+ side c)) 0) 0 1)))
   (define has-stencil
    (for*/or ((r (range side)) (c (range side))) (not (= (at g (+ side r) (+ side c)) 0))))
   (define backing
    (for/list ((r (range output-height)))
     (for/list ((c (range output-width)))
      (if has-stencil
       (at g (+ side (quotient r side)) (quotient c side))
       (at g (+ side (modulo r side)) (modulo c side))))))
   (for/list ((r (range output-height)))
    (for/list ((c (range output-width)))
     (let ((ink (at g (+ side (modulo r side)) (+ side (modulo c side)))))
      (if (= ink 0) (at backing r c) ink)))))))
