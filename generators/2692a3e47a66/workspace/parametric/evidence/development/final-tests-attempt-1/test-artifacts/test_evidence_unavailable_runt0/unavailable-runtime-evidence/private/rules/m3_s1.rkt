(rule! (lambda (g)
         (let* ((h (rows g))
                (w (cols g))
                (bg (mode g -1)))
           (reduce (lambda (acc color)
                     (if (= color bg)
                         acc
                         (let* ((objs (filter (lambda (o) (= (obj-color o) color))
                                              (objects g bg))))
                           (if (< (length objs) 3)
                               acc
                               (let* ((cleared (paint-cells acc (find-color g color) bg)))
                                 (reduce (lambda (a obj)
                                           (let* ((height (+ 1
                                                             (- (obj-r2 obj)
                                                                (obj-r1 obj))))
                                                  (width (+ 1
                                                            (- (obj-c2 obj)
                                                               (obj-c1 obj))))
                                                  (dr (if (< (* 2 (obj-r1 obj)) h)
                                                          height
                                                          (- height)))
                                                  (dc (if (< (* 2 (obj-c1 obj)) w)
                                                          width
                                                          (- width))))
                                             (reduce (lambda (aa cell)
                                                       (let* ((nr (+ (fst cell) dr))
                                                              (nc (+ (snd cell) dc)))
                                                         (if (in-bounds? nr nc h w)
                                                             (set-cell aa nr nc color)
                                                             aa)))
                                                     a
                                                     (obj-cells obj))))
                                         cleared
                                         objs))))))
                   g
                   (range 0 10)))))