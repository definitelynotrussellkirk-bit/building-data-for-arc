(rule!
  (let* ((guides (find-color g 5))
         (work (grid-from-fn (rows g) (cols g)
                 (lambda (r c)
                   (let ((v (at g r c)))
                     (if (and (not (= v 0)) (not (= v 5))) v 0)))))
         (same-row (and (= (length guides) 2)
                        (= (first (first guides)) (first (second guides)))))
         (mirrored
          (if same-row
              (for*/fold ([out work]) ([r (in-range (rows g))] [c (in-range (cols g))])
                (let ((v (at work r c)))
                  (if (not (= v 0)) (set-cell out (- (- (rows g) 1) r) c v) out)))
              (for*/fold ([out work]) ([r (in-range (rows g))] [c (in-range (cols g))])
                (let ((v (at work r c)))
                  (if (not (= v 0)) (set-cell out r (- (- (cols g) 1) c) v) out))))))
    (define bridged
      (for*/fold ([out mirrored]) ([r (in-range (rows g))] [c (in-range (cols g))])
        (let ((v (at work r c)))
          (cond
            [(= v 0) out]
            [same-row
             (let ((mr (- (- (rows g) 1) r)))
               (for/fold ([acc out]) ([rr (in-range (+ r 1) mr)])
                 (if (= (at acc rr c) 0) (set-cell acc rr c v) acc)))]
            [else
             (let ((mc (- (- (cols g) 1) c)))
               (for/fold ([acc out]) ([cc (in-range (+ c 1) mc)])
                 (if (= (at acc r cc) 0) (set-cell acc r cc v) acc)))]))))
    (paint-cells bridged guides 5)))
