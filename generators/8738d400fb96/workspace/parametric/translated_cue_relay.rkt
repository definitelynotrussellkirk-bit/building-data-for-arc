(rule!
  (let* ((shape (argmax obj-size (filter (lambda (o) (= (obj-color o) 3)) (objects g 0))))
         (a (first (find-color g 2)))
         (b (first (find-color g 1)))
         (dr (- (first b) (first a)))
         (dc (- (second b) (second a)))
         (moved (map (lambda (p) (list (+ (first p) dr) (+ (second p) dc))) (obj-cells shape)))
         (visible (filter (lambda (p) (in-bounds? (first p) (second p) h w)) moved))
         (cue-colors
           (remove-duplicates
             (filter (lambda (v) (and (>= v 4) (<= v 9)))
                     (map (lambda (p) (at g (first p) (second p))) visible))))
         (cue (first cue-colors))
         (relay-cells (find-color g cue)))
    (paint-cells (empty-grid h w 0) (append moved relay-cells) 8)))
