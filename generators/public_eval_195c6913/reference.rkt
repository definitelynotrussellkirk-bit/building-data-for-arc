(rule!
 ;; Read the detached 2x2 swatches in reading order: a cyclic path sequence,
 ;; followed by a collision-marker swatch. Top-left gives the wall color;
 ;; the most frequent remaining color gives the traversable corridor.
 ;; Each left-edge seed alternates east and the declared vertical direction.
 ;; Mark the blocked forward cell, pivot at the last free cell, and preserve
 ;; sequence phase across turns. Stop at the canvas edge or a blocked new leg.
 ;; Erase the legend swatches; all routing uses the original input terrain.
 (lambda (g)
  (let ()
   (define vertical-step -1)
   (define wall (at g 0 0))
   (define colors (grid-colors g wall))
   (define road (if (null? colors) wall (pick-max colors (lambda (v) (count-color g v)))))
   (define swatches
    (filter (lambda (o) (and (not (= (obj-color o) road)) (= (obj-size o) 4)
                              (= (obj-h o) 2) (= (obj-w o) 2))) (objects g wall)))
   (if (< (length swatches) 3) g
    (let ()
     (define raw-pattern (map obj-color (take swatches (- (length swatches) 1))))
     (define pattern raw-pattern)
     (define marker (obj-color (last swatches)))
     (define starts (filter (lambda (r) (= (at g r 0) (first raw-pattern))) (range (rows g))))
     (define clean (for/fold ((out g)) ((o swatches))
                    (for/fold ((canvas out)) ((p (obj-cells o)))
                     (set-cell canvas (first p) (second p) wall))))
     (define (free? r c)
      (and (in-bounds? r c (rows g) (cols g)) (= (at g r c) road)))
     (define (walk out r c heading phase fuel)
      (let* ((painted (set-cell out r c (list-ref pattern (modulo phase (length pattern)))))
             (nr (if (= heading 0) r (+ r vertical-step)))
             (nc (if (= heading 0) (+ c 1) c)))
       (cond
        ((or (= fuel 0) (not (in-bounds? nr nc (rows g) (cols g)))) painted)
        ((free? nr nc) (walk painted nr nc heading (+ phase 1) (- fuel 1)))
        (else
         (let* ((marked (if (= (at g nr nc) wall) (set-cell painted nr nc marker) painted))
                (pc c)
                (next-heading (- 1 heading))
                (tr (if (= next-heading 0) r (+ r vertical-step)))
                (tc (if (= next-heading 0) (+ pc 1) pc)))
          (if (free? tr tc)
              (walk marked tr tc next-heading (+ phase 1) (- fuel 1)) marked))))))
     (for/fold ((out clean)) ((r starts))
      (walk out r 0 0 0 (* 2 (+ (rows g) (cols g))))))))))
