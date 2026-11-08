(rule!
 ;; Whole-component variant: original four-connected foreground components
 ;; touched by any green stripe are recolored outside the projected band.
 ;; The only yellow object is a contiguous segment on one outside edge.
 ;; It defines an inward axis and a band of the same width. Overwrite that
 ;; band with yellow, background, yellow, background, green, background,
 ;; repeated from the marker. On green stripes, recolor every original
 ;; foreground pixel on the whole transverse line, not the gaps between them.
 (lambda (g)
   (let ()
     (define bg (mode g -1))
     (define marker (find-color g 4))
     (if (null? marker) g
       (let ()
         (define rlo (min-of first marker))
         (define rhi (max-of first marker))
         (define clo (min-of second marker))
         (define chi (max-of second marker))
         (define horizontal (= rlo rhi))
         (define forward (if horizontal (= rlo 0) (= clo 0)))
         (define lo (if horizontal clo rlo))
         (define hi (if horizontal chi rhi))
         (define (depth r c)
           (if horizontal (if forward r (- h 1 r))
                          (if forward c (- w 1 c))))
         (define selected
           (flatmap obj-cells
             (filter (lambda (o)
                       (and (not (= (obj-color o) 4))
                            #t))
                     (objects g bg))))
         (cellmap g (r c v)
           (let* ((d (depth r c))
                  (t (if horizontal c r))
                  (green (= (modulo d 6) 4)))
             (cond ((and (<= lo t) (<= t hi))
                    (cond (green 3) ((= (modulo d 2) 0) 4) (else bg)))
                   ((member (list r c) selected) 3)
                   (else v)))))))))
