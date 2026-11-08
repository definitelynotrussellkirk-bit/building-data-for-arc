(rule!
 ;; Read the color of each horizontal input row.  Fold the first h-1 rows
 ;; around the center as one-cell concentric square layers, producing a
 ;; 2(h-1) by 2(h-1) output.  The repeated final input row supplies the same
 ;; center color as the innermost retained layer.
 (lambda (g)
  (let ()
   (define finish-mode 0)
   (define h (rows g))
   (define side (* 2 (- h 1)))
   (define layers (range 0 (- h 1)))
   (define (layer-index r c)
    (min r c (- side 1 r) (- side 1 c)))
   (define rings
    (build-grid side side (r c)
     (at g (layer-index r c) 0)))
   (define sequence (map (lambda (r) (at g r 0)) layers))
   (define runs
    (let loop ((i 1) (start 0) (current (first sequence)) (out '()))
     (if (= i (length sequence))
      (reverse (cons (list start (- i 1) current) out))
      (let ((value (list-ref sequence i)))
       (if (= value current)
        (loop (+ i 1) start current out)
        (loop (+ i 1) i value (cons (list start (- i 1) current) out)))))))
   (define (run-length run) (+ 1 (- (second run) (first run))))
   (define (run-cells run)
    (for*/list ((r (range 0 side)) (c (range 0 side))
                #:when (and (<= (first run) (layer-index r c))
                            (<= (layer-index r c) (second run))))
     (list r c)))
   (define components (objects rings -1))
   (define colors (remove-duplicates sequence))
   (define most-frequent
    (pick-max colors
     (lambda (v) (count-if (lambda (x) (= x v)) sequence))))
   (define largest-total
    (pick-max colors (lambda (v) (count-color rings v))))
   (define outer
    (first (filter (lambda (o) (member (list 0 0) (obj-cells o))) components)))
   (define center-cell (list (- (/ side 2) 1) (- (/ side 2) 1)))
   (define inner
    (first (filter (lambda (o) (member center-cell (obj-cells o))) components)))
   (define selected
    (cond
     ((= finish-mode 1) (obj-cells (pick-max components obj-size)))
     ((= finish-mode 2) (run-cells (pick-max runs run-length)))
     ((= finish-mode 3) (find-color rings most-frequent))
     ((= finish-mode 4) (find-color rings largest-total))
     ((= finish-mode 5) (obj-cells outer))
     ((= finish-mode 6) (obj-cells inner))
     (else '())))
   (if (= finish-mode 0) rings (paint-cells rings selected 9)))))
