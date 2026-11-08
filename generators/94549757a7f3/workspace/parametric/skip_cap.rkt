(rule!
  (let ((new-caps
          (filter-cells g
            (lambda (r c v) (= v 2)))))
    (cellmap g
      (r c v)
      (if (= v 0)
          (let ((cap-rows
                  (map first
                       (filter (lambda (p) (= (second p) c)) new-caps))))
            (if (and (>= (length cap-rows) 2)
                     (> r (first cap-rows))
                     (< r (last cap-rows)))
                2
                v))
          v))))
