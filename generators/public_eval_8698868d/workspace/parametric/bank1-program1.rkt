(rule!
 ;; Background is the unique modal color, including zero as a possible foreground.
 ;; The largest square objects tile a panel; detached S-2 squares are templates.
 ;; Match using background area; component connectivity is four, not eight.
 ;; Inset the selected pattern by one cell and replace its background with tile color.
 ;; Erase the original clues and return only the completed panel's bounding rectangle.
 (lambda (g)
  (let ()
   (define bg (mode g -1))
   (define all (objects g bg))
   (define size (apply max (map obj-h all)))
   (define tiles (filter (lambda (o) (and (= (obj-h o) size) (= (obj-w o) size))) all))
   (define templates (filter (lambda (o) (and (= (obj-h o) (- size 2)) (= (obj-w o) (- size 2)))) all))
   (define (crop o) (subgrid g (obj-r1 o) (obj-c1 o) (obj-r2 o) (obj-c2 o)))
   (define (measure o) (count-color (crop o) bg))
   (define (before? a b) (or (< (obj-r1 a) (obj-r1 b)) (and (= (obj-r1 a) (obj-r1 b)) (< (obj-c1 a) (obj-c1 b)))))
   (define box (bbox-of-cells (apply append (map obj-cells tiles))))
   (define blank (empty-grid (+ 1 (- (third box) (first box))) (+ 1 (- (fourth box) (second box))) bg))
   (for/fold ((out blank)) ((tile tiles))
    (let* ((chosen (let ((found (filter (lambda (o) (= (measure o) (measure tile))) templates)))
          (first found)))
           (pattern (crop chosen)))
     (for*/fold ((a out)) ((r (range size)) (c (range size)))
      (let ((value (if (and (> r 0) (< r (- size 1)) (> c 0) (< c (- size 1)))
                      (let ((v (at pattern (- r 1) (- c 1)))) (if (= v bg) (obj-color tile) v))
                      (obj-color tile))))
       (set-cell a (+ (- (obj-r1 tile) (first box)) r) (+ (- (obj-c1 tile) (second box)) c) value))))))))
