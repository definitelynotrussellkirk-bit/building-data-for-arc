(rule!
 ;; Recover each solid bar independently, preserving its position, width,
 ;; and color. Sort centered heights along the cyan axis, then redraw.
 ;; Even heights have one more cell above the axis than below. Separated equal colors remain
 ;; separate bars. Transposed-axis inputs are an authored grammar extension.
 (lambda (g)
  (let ()
   (define descending? #f)
   (define cyan (find-color g 6))
   (define vertical? (> (length (remove-duplicates (map first cyan))) 1))
   (define (tr a)
    (for/list ((c (range (length (first a)))))
     (for/list ((r (range (length a)))) (list-ref (list-ref a r) c))))
   (define source (if vertical? (tr g) g))
   (define nr (length source))
   (define nc (length (first source)))
   (define axis (first (first (find-color source 6))))
   (define (v r c) (safe-at source r c -1))
   (define bars
    (let scan ((c 0) (found '()))
     (cond ((>= c nc) (reverse found))
      ((member (v axis c) '(6 8)) (scan (+ c 1) found))
      (else
       (let* ((color (v axis c))
              (end (let walk ((j c))
                     (if (and (< j nc) (= (v axis j) color)) (walk (+ j 1)) j)))
              (above (let walk ((d 1))
                      (if (and (<= d axis)
                         (for/and ((j (range c end))) (= (v (- axis d) j) color)))
                       (walk (+ d 1)) (- d 1))))
              (below (let walk ((d 1))
                      (if (and (< (+ axis d) nr)
                         (for/and ((j (range c end))) (= (v (+ axis d) j) color)))
                       (walk (+ d 1)) (- d 1)))))
        (scan end (cons (list c (- end 1) color (+ above below 1)) found)))))))
   (define assigned-heights
    (sort (map fourth bars) (if descending? > <)))
   (define painted
    (for/fold ((out (build-grid nr nc (r c) (if (= r axis) 6 8))))
              ((bar bars) (size assigned-heights))
     (recolor-cells out
       (positions-in-rect (- axis (quotient size 2)) (first bar)
         (+ (- axis (quotient size 2)) size -1) (second bar))
       (third bar))))
   (if vertical? (tr painted) painted))))
