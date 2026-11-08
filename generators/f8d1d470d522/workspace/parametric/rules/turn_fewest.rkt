(rule! (lambda (g)
         (let* ((h (rows g))
                (w (cols g)))
           (begin
             (define marks (find-color g 9))
             (if (< (length marks) 2)
                 g
                 (let* ((start (fst marks))
                        (goal (snd marks))
                        (dirs (list (list 0 1) (list 1 0) (list 0 -1) (list -1 0)))
                        (best-path #f)
                        (best-len 999)
                        (best-turns 999))
                   (define (adjacent-7? r c)
                     (for/or ((d dirs))
                             (let ((nr (+ r (fst d)))
                                   (nc (+ c (snd d))))
                               (and (in-bounds? nr nc h w) (= (at g nr nc) 7)))))
                   (define (allowed? r c)
                     (let ((v (at g r c)))
                       (and (or (= v 8) (= v 9)) (or (= v 9) (not (adjacent-7? r c))))))
                   (define (better? len turns)
                     (or (< len best-len) (and (= len best-len) (< turns best-turns))))
                   (define (dfs cur path prev-dir turns)
                     (let ((len (length path)))
                       (when
                         (and
                           (<= len best-len)
                           (or (< len best-len) (< turns best-turns)))
                         (if (equal? cur goal)
                             (when
                               (better? len turns)
                               (set! best-len len)
                               (set! best-turns turns)
                               (set! best-path path))
                             (for-each (lambda (d)
                                         (let* ((nr (+ (fst cur) (fst d)))
                                                (nc (+ (snd cur) (snd d)))
                                                (np (list nr nc)))
                                           (when
                                             (and
                                               (in-bounds? nr nc h w)
                                               (allowed? nr nc)
                                               (not (member np path)))
                                             (dfs np
                                                  (append path (list np))
                                                  d
                                                  (if (or
                                                        (not prev-dir)
                                                        (equal? prev-dir d))
                                                      turns
                                                      (+ turns 1))))))
                                       dirs)))))
                   (dfs start (list start) #f 0)
                   (if best-path (paint-cells g best-path 9) g)))))))