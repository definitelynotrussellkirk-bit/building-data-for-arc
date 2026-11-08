(rule!
 ;; Find the modal background, with lower color breaking a frequency tie.
 ;; For each other color, search horizontal integer and half-integer axes.
 ;; Retain the largest original same-color reflection overlap; the topmost
 ;; axis wins equal scores. Erase unpaired pixels, rather than filling gaps.
 (lambda (g)
  (let ()
   (define colors (grid-colors g))
   (define bg (for/fold ((best (first colors))) ((color colors))
    (if (> (count-color g color) (count-color g best)) color best)))
   (define (mirror p k) (list (- k (first p)) (second p)))
   (define (kept pts k) (filter (lambda (p) (member (mirror p k) pts)) pts))
   (for/fold ((out (for/list ((r (range h))) (for/list ((c (range w))) bg)))) ((color colors) #:when (not (= color bg)))
    (let* ((pts (find-color g color))
           (axis (for/fold ((best 0)) ((k (range (- (* 2 h) 1))))
             (if (> (length (kept pts k)) (length (kept pts best))) k best))))
     (for/fold ((acc out)) ((p (kept pts axis)))
      (set-cell acc (first p) (second p) color)))))))
