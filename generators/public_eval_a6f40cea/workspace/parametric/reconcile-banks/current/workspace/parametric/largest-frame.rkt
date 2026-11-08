(rule!
 ;; Recover every monochrome or checkerboard rectangle outline hidden behind
 ;; the largest color-3 rectangular occluder, then render the hidden perimeter
 ;; cells into the strict interior window.  The immutable parent contains one
 ;; wide striped-frame phase anomaly; the documented extension flips hidden
 ;; checkerboard phase exactly when a striped frame is wider than tall.
 (lambda (g)
  (let ()
   (define selection-mode 1)
   (define bg (pick-max (grid-colors g) (lambda (v) (count-color g v))))
   (define green-objects
    (filter (lambda (o) (= (obj-color o) 3)) (objects g bg)))
   (define target (pick-max green-objects obj-size))
   (define target-box (obj-bbox target))
   (define tr1 (first target-box))
   (define tc1 (second target-box))
   (define tr2 (third target-box))
   (define tc2 (fourth target-box))
   (define (inside-box? p box)
    (and (<= (first box) (first p)) (<= (first p) (third box))
         (<= (second box) (second p)) (<= (second p) (fourth box))))
   (define (inside-strict? p box)
    (and (< (first box) (first p)) (< (first p) (third box))
         (< (second box) (second p)) (< (second p) (fourth box))))
   (define (boundary-cells box)
    (let ((r1 (first box)) (c1 (second box))
          (r2 (third box)) (c2 (fourth box)))
     (filter
      (lambda (p)
       (or (= (first p) r1) (= (first p) r2)
           (= (second p) c1) (= (second p) c2)))
      (positions-in-rect r1 c1 r2 c2))))
   (define outside-values
    (map (lambda (p) (at g (first p) (second p)))
     (filter (lambda (p) (not (inside-box? p target-box)))
             (grid-positions g))))
   (define background (mode-list outside-values))
   (define fill
    (mode-list
     (for*/list ((r (range (+ tr1 1) tr2))
                 (c (range (+ tc1 1) tc2)))
      (at g r c))))
   (define colors
    (filter (lambda (v) (and (!= v background) (!= v 3) (!= v fill)))
            (grid-colors g)))
   (define (outside-color-cells color)
    (filter (lambda (p) (not (inside-box? p target-box)))
            (find-color g color)))
   (define color-records
    (filter
     (lambda (rec) (not (empty? (second rec))))
     (map (lambda (color) (list color (outside-color-cells color))) colors)))
   (define (frame-record box even-color odd-color striped?)
    (let* ((height (+ 1 (- (third box) (first box))))
           (width (+ 1 (- (fourth box) (second box))))
           (area (* height width)))
     (list box even-color odd-color striped? height width area)))
   (define monochrome-frames
    (filter
     (lambda (x) (not (equal? x #f)))
     (map
      (lambda (rec)
       (let* ((color (first rec))
              (cells (second rec))
              (box (bbox-of-cells cells))
              (height (+ 1 (- (third box) (first box))))
              (width (+ 1 (- (fourth box) (second box))))
              (visible (filter (lambda (p) (not (inside-box? p target-box)))
                               (boundary-cells box)))
              (hidden (filter (lambda (p) (inside-strict? p target-box))
                              (boundary-cells box))))
        (if (and (>= height 3) (>= width 3) (not (empty? hidden))
                 (equal? cells visible))
            (frame-record box color color #f)
            #f)))
      color-records)))
   (define striped-frames
    (filter
     (lambda (x) (not (equal? x #f)))
     (for*/list ((i (range 0 (length color-records)))
                 (j (range (+ i 1) (length color-records))))
      (let* ((first-rec (list-ref color-records i))
             (second-rec (list-ref color-records j))
             (first-cells (second first-rec))
             (second-cells (second second-rec))
             (first-box (bbox-of-cells first-cells))
             (second-box (bbox-of-cells second-cells)))
       (if (not (equal? first-box second-box))
           #f
           (let* ((box first-box)
                  (height (+ 1 (- (third box) (first box))))
                  (width (+ 1 (- (fourth box) (second box))))
                  (visible (filter (lambda (p) (not (inside-box? p target-box)))
                                   (boundary-cells box)))
                  (hidden (filter (lambda (p) (inside-strict? p target-box))
                                  (boundary-cells box)))
                  (union-cells (sort (remove-duplicates (append first-cells second-cells)) cell<))
                  (even-values
                   (unique
                    (map (lambda (p) (at g (first p) (second p)))
                     (filter (lambda (p) (= (modulo (+ (first p) (second p)) 2) 0)) visible))))
                  (odd-values
                   (unique
                    (map (lambda (p) (at g (first p) (second p)))
                     (filter (lambda (p) (= (modulo (+ (first p) (second p)) 2) 1)) visible)))))
            (if (and (>= height 3) (>= width 3) (not (empty? hidden))
                     (equal? union-cells visible)
                     (= (length even-values) 1) (= (length odd-values) 1)
                     (!= (first even-values) (first odd-values)))
                (frame-record box (first even-values) (first odd-values) #t)
                #f)))))))
   (define frames
    (sort-by (append monochrome-frames striped-frames)
     (lambda (rec)
      (+ (* (first (first rec)) 27000)
         (* (second (first rec)) 900)
         (* (third (first rec)) 30)
         (fourth (first rec))))))
   (define selected
    (if (= selection-mode 0)
        frames
        (list (pick-max frames (lambda (rec) (seventh rec))))))
   (define base (empty-grid (- tr2 tr1 1) (- tc2 tc1 1) fill))
   (for/fold ((out base)) ((rec selected))
    (let* ((box (first rec))
           (even-color (second rec))
           (odd-color (third rec))
           (striped? (fourth rec))
           (height (fifth rec))
           (width (sixth rec))
           (flip? (and striped? (> width height)))
           (hidden (filter (lambda (p) (inside-strict? p target-box))
                           (boundary-cells box)))
           (paints
            (map
             (lambda (p)
              (let* ((even? (= (modulo (+ (first p) (second p)) 2) 0))
                     (ordinary (if even? even-color odd-color))
                     (flipped (if even? odd-color even-color)))
               (list (- (first p) tr1 1) (- (second p) tc1 1)
                     (if flip? flipped ordinary))))
             hidden)))
     (paint-cells out paints))))))
