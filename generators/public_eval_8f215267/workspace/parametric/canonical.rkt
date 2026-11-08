(rule!
 ;; Find the wide hollow rectangular frames, whose colors are tally keys.
 ;; Remove those frames from an analysis copy, then segment the remaining
 ;; same-color objects with the declared connectivity. Count them per key.
 ;; Preserve only the frames and encode each count as isolated same-color
 ;; dots on the central row, right aligned, with one blank cell between dots
 ;; and a blank margin before the right wall. Unlisted colors disappear.
 ;; The canonical extension uses four-neighbor connectivity; all original
 ;; examples are reproduced without relying on fixed colors or locations.
 (lambda (g)
  (let ()
   (define connectivity 4)
   (define bg (at g 0 0))
   (define (frame? o)
    (and (>= (obj-h o) 5) (>= (obj-w o) 7)
         (= (obj-size o) (- (* 2 (+ (obj-h o) (obj-w o))) 4))
         (for/and ((p (obj-cells o)))
          (or (= (first p) (obj-r1 o)) (= (first p) (obj-r2 o))
              (= (second p) (obj-c1 o)) (= (second p) (obj-c2 o))))))
   (define frames (filter frame? (objects g bg)))
   (define body
    (for/fold ((out g)) ((f frames))
     (for/fold ((canvas out)) ((p (obj-cells f)))
      (set-cell canvas (first p) (second p) bg))))
   (define pieces (if (= connectivity 8) (objects-8 body bg) (objects body bg)))
   (define base (empty-grid (rows g) (cols g) bg))
   (for/fold ((out base)) ((f frames) (index (range (length frames))))
    (let ()
     (define key-color (obj-color f))
     (define matches (filter (lambda (o) (= (obj-color o) key-color)) pieces))
     (define raw-count (length matches))
     (define n raw-count)
     (define capacity (quotient (- (obj-w f) 3) 2))
     (define border (for/fold ((canvas out)) ((p (obj-cells f)))
                     (set-cell canvas (first p) (second p) (obj-color f))))
     (for/fold ((canvas border)) ((k (range 1 (+ 1 (min capacity n)))))
      (set-cell canvas (quotient (+ (obj-r1 f) (obj-r2 f)) 2)
                (- (obj-c2 f) (* 2 k)) (obj-color f))))))))
