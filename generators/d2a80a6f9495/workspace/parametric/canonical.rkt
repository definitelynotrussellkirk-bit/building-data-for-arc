(rule! (lambda (g)
         (let* ((objs (objects-multicolor g 0)))
           (reduce (lambda (acc obj)
                     (let* ((cells (obj-cells obj))
                            (colors (unique (map (lambda (p) (at g (fst p) (snd p)))
                                                 cells))))
                       (if (!= 2 (length colors))
                           acc
                           (let* ((ka (first colors))
                                  (kb (nth colors 1)))
                             (reduce (lambda (g2 p)
                                       (set-cell g2
                                                 (fst p)
                                                 (snd p)
                                                 (if (= ka (at g (fst p) (snd p)))
                                                     kb
                                                     ka)))
                                     acc
                                     cells)))))
                   g
                   objs))))