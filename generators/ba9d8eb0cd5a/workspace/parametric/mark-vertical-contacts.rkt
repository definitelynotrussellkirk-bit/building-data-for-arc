(rule!
  (let ((packed (gravity g "left")))
    (grid-from-fn (rows packed) (cols packed)
      (lambda (r c)
        (let ((v (at packed r c)))
          (if (and (not (= v 0))
                   (or (and (> r 0)
                            (not (= (at packed (- r 1) c) 0)))
                       (and (< r (- (rows packed) 1))
                            (not (= (at packed (+ r 1) c) 0)))))
              2
              v))))))
