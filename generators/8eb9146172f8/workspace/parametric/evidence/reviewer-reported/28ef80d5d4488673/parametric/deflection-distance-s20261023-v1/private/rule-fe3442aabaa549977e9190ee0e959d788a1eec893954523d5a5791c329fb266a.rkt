(rule! (lambda (g)
         (let* ((h (rows g))
                (w (cols g)))
           (let* ((cyan-cells (find-color g 8))
                  (red-cells (find-color g 2))
                  (cyan-rows (map first cyan-cells))
                  (cyan-cols (map second cyan-cells))
                  (red-rows (map first red-cells))
                  (red-cols (map second red-cells))
                  (cyan-edge (cond
                               ((andmap (lambda (r) (zero? r)) cyan-rows) 'top)
                               ((andmap (lambda (r) (= r (- h 1))) cyan-rows) 'bottom)
                               ((andmap (lambda (c) (zero? c)) cyan-cols) 'left)
                               (else 'right)))
                  (red-edge (cond
                              ((andmap (lambda (r) (zero? r)) red-rows) 'top)
                              ((andmap (lambda (r) (= r (- h 1))) red-rows) 'bottom)
                              ((andmap (lambda (c) (zero? c)) red-cols) 'left)
                              (else 'right)))
                  (shift-val (cond
                               ((eq? red-edge 'top) 1)
                               ((eq? red-edge 'bottom) -1)
                               ((eq? red-edge 'left) 1)
                               (else -1)))
                  (process-cyan (lambda (grid cell)
                                  (let ((cr (first cell))
                                        (cc (second cell)))
                                    (cond
                                      ((eq? cyan-edge 'top) (let loop
                                             ((r 0) (current-c cc) (gr grid))
                                             (if (>= r h)
                                                 gr
                                                 (let ((new-c (if (member r red-rows)
                                                                  (+ current-c
                                                                     shift-val)
                                                                  current-c)))
                                                   (if (and (>= new-c 0) (< new-c w))
                                                       (loop (+ r 1)
                                                             new-c
                                                             (set-cell gr r new-c 8))
                                                       (loop (+ r 1) new-c gr))))))
                                      ((eq? cyan-edge 'left) (let loop
                                             ((c 0) (current-r cr) (gr grid))
                                             (if (>= c w)
                                                 gr
                                                 (let ((new-r (if (member c red-cols)
                                                                  (+ current-r
                                                                     shift-val)
                                                                  current-r)))
                                                   (if (and (>= new-r 0) (< new-r h))
                                                       (loop (+ c 1)
                                                             new-r
                                                             (set-cell gr new-r c 8))
                                                       (loop (+ c 1) new-r gr))))))
                                      ((eq? cyan-edge 'right) (let loop
                                             ((c (- w 1)) (current-r cr) (gr grid))
                                             (if (< c 0)
                                                 gr
                                                 (let ((new-r (if (member c red-cols)
                                                                  (+ current-r
                                                                     shift-val)
                                                                  current-r)))
                                                   (if (and (>= new-r 0) (< new-r h))
                                                       (loop (- c 1)
                                                             new-r
                                                             (set-cell gr new-r c 8))
                                                       (loop (- c 1) new-r gr))))))
                                      ((eq? cyan-edge 'bottom) (let loop
                                             ((r (- h 1)) (current-c cc) (gr grid))
                                             (if (< r 0)
                                                 gr
                                                 (let ((new-c (if (member r red-rows)
                                                                  (+ current-c
                                                                     shift-val)
                                                                  current-c)))
                                                   (if (and (>= new-c 0) (< new-c w))
                                                       (loop (- r 1)
                                                             new-c
                                                             (set-cell gr r new-c 8))
                                                       (loop (- r 1) new-c gr))))))
                                      (else grid))))))
             (reduce process-cyan g cyan-cells)))))