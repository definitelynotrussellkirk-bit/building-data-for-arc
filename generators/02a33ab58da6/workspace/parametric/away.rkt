(rule!
  (let ((maxd (+ h w))
        (dirs (list (list -1 0) (list 1 0) (list 0 -1) (list 0 1))))
    (define (move-for gp dir)
      (let* ((gr (first gp))
             (gc (second gp))
             (dr (first dir))
             (dc (second dir))
             (k-step
              (find-first
               (lambda (i)
                 (let ((nr (+ gr (* dr i)))
                       (nc (+ gc (* dc i))))
                   (and (in-bounds? nr nc h w)
                        (zero? (at g nr nc)))))
               (range 1 maxd)))
             (k-valid
              (and k-step
                   (for/and ((j (range 1 k-step)))
                     (= (at g (+ gr (* dr j)) (+ gc (* dc j))) 2)))))
        (and
         k-valid
         (let* ((kr (+ gr (* dr k-step)))
                (kc (+ gc (* dc k-step)))
                (tail-end
                 (find-first
                  (lambda (i)
                    (let ((nr (+ kr (* dr i)))
                          (nc (+ kc (* dc i))))
                      (or (not (in-bounds? nr nc h w))
                          (!= (at g nr nc) 2))))
                  (range 1 maxd)))
                (tlen (if tail-end (- tail-end 1) 0))
                (pdr (if (zero? dc) 0 (if (< kr (/ h 2)) -1 1)))
                (pdc (if (zero? dr) 0 (if (< kc (/ w 2)) -1 1))))
           (and (> tlen 0) (list kr kc dr dc pdr pdc tlen))))))
    (let ((moves
           (filter
            (lambda (m) m)
            (flatmap
             (lambda (gp)
               (map (lambda (dir) (move-for gp dir)) dirs))
             (find-color g 5)))))
      (cellmap
       g (r c v)
       (let* ((removed
               (find
                (lambda (m)
                  (for/or ((i (range 0 (nth m 6))))
                    (and (= r (+ (first m) (* (third m) (+ i 1))))
                         (= c (+ (second m) (* (nth m 3) (+ i 1)))))))
                moves))
              (added
               (find
                (lambda (m)
                  (for/or ((i (range 0 (nth m 6))))
                    (and (= r (+ (first m) (* (nth m 4) (+ i 1))))
                         (= c (+ (second m) (* (nth m 5) (+ i 1)))))))
                moves)))
         (cond (added 2) (removed 7) (else v)))))))
