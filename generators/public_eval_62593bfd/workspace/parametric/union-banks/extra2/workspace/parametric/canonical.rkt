(rule!
 ;; Find monochromatic 8-connected objects against the modal background.
 ;; Repeated cell-count classes dock at the top; singleton classes dock
 ;; at the bottom. Each rigid translation preserves its horizontal position.
 (lambda (g)
   (let ()
     (define bg (mode g -1))
     (define os (objects-8 g bg))
     (define stage-a
       (for/fold ((out (empty-grid (rows g) (cols g) bg))) ((o os))
         (let* ((repeated (> (count (lambda (other) (= (obj-size o) (obj-size other))) os) 1))
                (delta (if repeated (- (obj-r1 o)) (- (rows g) 1 (obj-r2 o)))))
           (for/fold ((canvas out)) ((p (obj-cells o)))
             (set-cell canvas (+ (first p) delta) (second p) (obj-color o))))))
     stage-a)))
