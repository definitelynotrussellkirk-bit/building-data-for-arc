(rule!
  (let ((colors (grid-colors g 0)))
    (grid-from-fn h w
      (lambda (r c)
        (let ((v (cell-at g r c)))
          (if (not (= v 0))
              v
              (let ((fill-color
                      (find-first
                        (lambda (color)
                          (let ((pts (find-color g color)))
                            (or
                              (any?
                                (lambda (p1)
                                  (any?
                                    (lambda (p2)
                                      (and (= (fst p1) r) (= (fst p2) r)
                                           (<= (min (snd p1) (snd p2)) c)
                                           (<= c (max (snd p1) (snd p2)))))
                                    pts))
                                pts)
                              (any?
                                (lambda (p1)
                                  (any?
                                    (lambda (p2)
                                      (and (= (snd p1) c) (= (snd p2) c)
                                           (<= (min (fst p1) (fst p2)) r)
                                           (<= r (max (fst p1) (fst p2)))))
                                    pts))
                                pts))))
                        colors)))
                (if fill-color fill-color 0))))))))