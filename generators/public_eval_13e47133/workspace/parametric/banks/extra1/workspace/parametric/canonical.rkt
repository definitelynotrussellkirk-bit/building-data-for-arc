(rule!
 ;; The modal color is background; the largest remaining color forms walls.
 ;; Partition the nonwall cells by four-connectivity. In each region repeatedly
 ;; erode all eight neighboring directions to obtain inward square-ring layers.
 ;; Sparse nonbackground cues define colors at their measured layer depths;
 ;; missing early colors are background. The deepest cue fixes palette length.
 ;; Repeat that ordered palette cyclically over all layers, preserving walls.
 (lambda (g)
  (let ()
   (define bg (pick-max (grid-colors g) (lambda (x) (count-color g x))))
   (define wall (pick-max (grid-colors g bg) (lambda (x) (count-color g x))))
   (define regions
    (objects (grid-from-fn (rows g) (cols g) (lambda (r c) (if (= (at g r c) wall) 0 1))) 0))
   (define (erode cells)
    (if (null? cells) '()
     (let* ((inside
       (filter (lambda (p)
        (andmap (lambda (d) (member (list (+ (first p) (first d)) (+ (second p) (second d))) cells)) all-8-deltas)) cells))
       (edge (filter (lambda (p) (not (member p inside))) cells)))
      (cons edge (erode inside)))))
   (define (marked layer)
    (filter (lambda (p) (not (= (at g (first p) (second p)) bg))) layer))
   (for/fold ((out g)) ((obj regions))
    (let ()
     (define cells (obj-cells obj))
     (define layers (erode cells))
     (define cue-depths (filter (lambda (d) (not (null? (marked (list-ref layers d))))) (range (length layers))))
     (define palette-size (if (null? cue-depths) 1 (+ 1 (apply max cue-depths))))
     (define palette
      (for/list ((d (range palette-size)))
       (let ((cues (marked (list-ref layers d))))
        (if (null? cues) bg
         (let ((colors (sort (remove-duplicates (map (lambda (p) (at g (first p) (second p))) cues)) <)))
          (pick-max colors (lambda (color) (count-if (lambda (p) (= (at g (first p) (second p)) color)) cues))))))))
     (define painting-layers layers)
     (for/fold ((acc out)) ((layer painting-layers) (depth (range (length painting-layers))))
      (let ((index (modulo depth palette-size)))
       (paint-cells acc layer (list-ref palette index)))))))))
