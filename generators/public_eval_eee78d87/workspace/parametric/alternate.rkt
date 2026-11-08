(rule!
 ;; Recover the tight non-orange motif and its two-dimensional period.
 ;; Center two copies per axis; their foreground is maroon, the outer
 ;; continuation black. Orange is preserved. The admitted extension sets
 ;; output dimensions to 2*input+4; all official inputs are 6x6.
 ;; Tiling: alternating_mirror; ablation: none.
 (lambda (g)
  (let ()
   (define raw (crop-to-content g 7))
   (define motif raw)
   (define mh (rows motif))
   (define mw (cols motif))
   (define HH (+ (* 2 h) 4))
   (define WW (+ (* 2 w) 4))
   (define sr (- (/ HH 2) mh))
   (define sc (- (/ WW 2) mw))
   (build-grid HH WW (r c)
    (let* ((dr (- r sr)) (dc (- c sc))
           (mr (if (odd? (/ (- dr (modulo dr mh)) mh)) (- mh 1 (modulo dr mh)) (modulo dr mh))) (mc (if (odd? (/ (- dc (modulo dc mw)) mw)) (- mw 1 (modulo dc mw)) (modulo dc mw))))
     (if (= (at motif mr mc) 7) 7
         (if (and (<= sr r) (< r (+ sr (* 2 mh))) (<= sc c) (< c (+ sc (* 2 mw)))) 9 0)))))))
