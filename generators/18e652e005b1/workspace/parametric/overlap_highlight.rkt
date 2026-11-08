(rule!
  (let* ((commands (filter (lambda (v) (not (= v 0))) (last g)))
         (base (subgrid g 0 0 (- (rows g) 2) (- (cols g) 1)))
         (motif (crop-to-content base))
         (mh (rows motif))
         (mw (cols motif))
         (stride (max 1 (- mw 1)))
         (out-w (+ mw (* (- (length commands) 1) stride))))
    (grid-from-fn
     mh out-w
     (lambda (r c)
       (let ((contributors
              (filter
               (lambda (i)
                 (let ((offset (- c (* i stride))))
                   (and (>= offset 0)
                        (< offset mw)
                        (not (= (at motif r offset) 0)))))
               (range (length commands)))))
         (cond
           ((empty? contributors) 0)
           ((> (length contributors) 1) 8)
           (else (list-ref commands (first contributors)))))))))
