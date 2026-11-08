(rule!
 (let ((dummy 0))
  (define dirs4 (list (list -1 0) (list 1 0) (list 0 -1) (list 0 1)))
  (define (arrow-dir code)
   (cond ((= code 1) (list -1 0))
         ((= code 2) (list 0 1))
         ((= code 3) (list 1 0))
         ((= code 4) (list 0 -1))
         (else #f)))
  (define (arrow-pos obj)
   (first
    (filter values
     (for*/list ((p (in-list (obj-cells obj))) (d (in-list dirs4)))
      (let ((rr (+ (first p) (first d))) (cc (+ (second p) (second d))))
       (if (and (in-bounds? rr cc (rows g) (cols g))
                (arrow-dir (at g rr cc)))
           (list rr cc)
           #f))))))
  (define (obj-dir obj)
   (let ((p (arrow-pos obj)))
    (arrow-dir (at g (first p) (second p)))))
  (define (sweep-cells cells dr dc)
   (remove-duplicates
    (append cells
     (apply append
      (map
       (lambda (cell)
        (let loop ((r (+ (first cell) dr))
                   (c (+ (second cell) dc))
                   (acc (list)))
         (if (in-bounds? r c (rows g) (cols g))
             (loop (+ r dr) (+ c dc) (cons (list r c) acc))
             (reverse acc))))
       cells)))))
  (define obj-grid
   (grid-from-fn (rows g) (cols g)
    (lambda (r c) (let ((v (at g r c))) (if (>= v 5) v 0)))))
  (define objs (objects obj-grid 0))
  (define probe (first (filter (lambda (obj) (= (obj-color obj) 9)) objs)))
  (define probe-cell (first (obj-cells probe)))
  (define pdir (obj-dir probe))
  (define trace
   (let loop ((r (+ (first probe-cell) (first pdir)))
              (c (+ (second probe-cell) (second pdir)))
              (path (list probe-cell))
              (first-hit #f)
              (last-hit #f))
    (cond
     ((not (in-bounds? r c (rows g) (cols g)))
      (list (reverse path) first-hit last-hit))
     ((>= (at g r c) 5)
      (loop (+ r (first pdir)) (+ c (second pdir)) path
            (if first-hit first-hit (list r c))
            (list r c)))
     (else
      (loop (+ r (first pdir)) (+ c (second pdir))
            (if first-hit path (cons (list r c) path))
            first-hit last-hit)))))
  (define path (first trace))
  (define hit (first (rest (rest trace))))
  (if (not hit)
      (paint-cells (empty-grid (rows g) (cols g) 0) path 9)
      (let* ((target (first (filter (lambda (obj) (member? hit (obj-cells obj))) objs)))
             (tdir (obj-dir target))
             (out (paint-cells (empty-grid (rows g) (cols g) 0) path 9)))
       (paint-cells out
                    (sweep-cells (obj-cells target) (first tdir) (second tdir))
                    (obj-color target))))))
