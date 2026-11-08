(rule!
 ;; The corner KEY at (0,0) picks the transform for the remaining shape
 ;; (cropped to content): 1 -> flip-lr, 2 -> flip-ud, else unchanged.
 (let* ((key (at g 0 0))
        (obj (crop-to-content (set-cell g 0 0 0))))
   (cond ((= key 1) (flip-lr obj))
         ((= key 2) (flip-ud obj))
         (else obj))))