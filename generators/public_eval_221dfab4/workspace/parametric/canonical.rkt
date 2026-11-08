(rule!
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
         (cellmap g (r c v)
           (let* ((d (depth r c))
                  (t (if horizontal c r))
                  (green (= (modulo d 6) 4)))
             (cond ((and (<= lo t) (<= t hi))
                    (cond (green 3) ((= (modulo d 2) 0) 4) (else bg)))
                   ((and green (not (= v bg))) 3)
                   (else v)))))))))
