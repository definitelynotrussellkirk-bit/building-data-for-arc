(rule!
 ;; The biggest multicolor object is a PLATE whose holes are rimmed in
 ;; red(2); loose KEY tiles elsewhere carry red teeth. For each hole
 ;; region, find a key rotation whose teeth plug it exactly — teeth on
 ;; empty cells, key body on the red rim — and stamp it: teeth turn
 ;; red where empty, body colors overwrite the rim. Output the plate.
 (lambda (g)
   (let ()
     (define objs
       (sort-by (objects-multicolor g 0) (lambda (o) (- (obj-size o)))))
     (define plate (first objs))
     (define interior
       (subgrid g (obj-r1 plate) (obj-c1 plate)
                (obj-r2 plate) (obj-c2 plate)))
     (define ih (rows interior))
     (define iw (cols interior))
     (define (key-info kg)  ;; (grid teeth body-cells kh kw)
       (let* ((pos (grid-positions kg))
              (teeth (filter (lambda (p) (= (at kg (first p)
                                               (second p))
                                            2))
                             pos)))
         (list kg teeth
               (filter (lambda (p)
                         (let ((v (at kg (first p) (second p))))
                           (and (not (= v 2)) (not (= v 0)))))
                       pos)
               (rows kg) (cols kg))))
     (define oriented-keys
       (flatmap (lambda (obj)
                  (let ((kg (subgrid g (obj-r1 obj) (obj-c1 obj)
                                     (obj-r2 obj) (obj-c2 obj))))
                    (map key-info
                         (list kg (rotate-cw kg) (rotate-180 kg)
                               (rotate-ccw kg)))))
                (rest objs)))
     (define (match-for hole acc)  ;; (grid dr dc kh kw) plugging hole
       (let ((hsize (obj-size hole))
             (hr (min-of first (obj-cells hole)))
             (hc (min-of second (obj-cells hole))))
         (find-first
          (lambda (x) x)
          (map (lambda (ki)
                 (and (= (length (second ki)) hsize)
                      (let* ((dr (- hr (min-of first (second ki))))
                             (dc (- hc (min-of second (second ki))))
                             (ok? (lambda (cells want)
                                    (all? (lambda (rc)
                                            (let ((tr (+ (first rc) dr))
                                                  (tc (+ (second rc)
                                                         dc)))
                                              (and (in-bounds? tr tc
                                                               ih iw)
                                                   (= (at acc tr tc)
                                                      want))))
                                          cells))))
                        (and (ok? (second ki) 0)
                             (ok? (third ki) 2)
                             (list (first ki) dr dc (fourth ki)
                                   (nth ki 4))))))
               oriented-keys))))
     (for/fold ((acc interior))
               ((hole (in-list (objects-8 interior 2))))
       (let ((hit (match-for hole acc)))
         (if hit
             (let ((kg (first hit)) (dr (second hit)) (dc (third hit))
                   (kh (fourth hit)) (kw (nth hit 4)))
               (build-grid ih iw (r c)
                           (let ((kr (- r dr)) (kc (- c dc)))
                             (if (and (>= kr 0) (< kr kh)
                                      (>= kc 0) (< kc kw))
                                 (let ((kv (at kg kr kc)))
                                   (cond ((and (= kv 2)
                                               (zero? (at acc r c)))
                                          2)
                                         ((and (not (= kv 2))
                                               (not (= kv 0)))
                                          (let* ((payloads
                                                  (filter
                                                   (lambda (p)
                                                     (let ((v (at kg (first p)
                                                                  (second p))))
                                                       (and (not (= v 2))
                                                            (not (= v 0)))))
                                                   (grid-positions kg)))
                                                 (other
                                                  (find-first
                                                   (lambda (p)
                                                     (not (and (= (first p) kr)
                                                               (= (second p) kc))))
                                                   payloads)))
                                            (at kg (first other)
                                                   (second other))))
                                         (else (at acc r c))))
                                 (at acc r c)))))
             acc))))))