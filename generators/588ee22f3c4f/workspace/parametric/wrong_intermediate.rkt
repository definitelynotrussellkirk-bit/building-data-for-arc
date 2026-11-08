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
             (let ((rr (+ r 1)))
               (if (and (< rr (rows g)) (= (at out rr c) 0)) (set-cell out rr c v) out))]
            [else
             (let ((cc (+ c 1)))
               (if (and (< cc (cols g)) (= (at out r cc) 0)) (set-cell out r cc v) out))]))))
    (paint-cells bridged guides 5)))
