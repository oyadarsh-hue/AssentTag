"""Face-shaped privacy masks, shared by feed, notifications and stories."""
import cv2
import dlib
import numpy as np
from threading import Lock
from face_utils import predictor, dlib_lock


_segmentation_lock = Lock()


def _smooth_outline(points, passes=2):
    """Round contour corners without overshooting into hair/background."""
    points = np.asarray(points, dtype=float)
    for _ in range(passes):
        following = np.roll(points, -1, axis=0)
        points = np.stack((.75*points+.25*following,
                           .25*points+.75*following), axis=1).reshape(-1,2)
    return np.rint(points).astype(np.int32)


def _forehead_points(frame, landmarks, down, face_height):
    """Estimate the skin/hair boundary above each brow in the face's own axes."""
    lab = cv2.cvtColor(frame, cv2.COLOR_BGR2LAB).astype(np.float32)
    height, width = frame.shape[:2]
    brows = landmarks[17:27]
    radius = max(1, round(face_height * .018))

    def sample(point):
        px, py = np.rint(point).astype(int)
        if not (radius <= px < width-radius and radius <= py < height-radius):
            return None
        return np.median(lab[py-radius:py+radius+1, px-radius:px+radius+1], axis=(0,1))

    depths = []
    # Follow the first sustained skin-to-hair transition independently at each
    # brow. A fixed dome cropped forehead skin on some faces and covered hair
    # on others. Use the last skin sample, not the third sample inside the hair.
    for index, brow in enumerate(brows):
        # Start above the eyebrow itself, so dark eyebrow hairs are not skin seeds.
        seed = sample(brow - down * face_height * .10)
        depth = face_height * .43
        misses = 0
        if seed is not None:
            step = max(1, face_height*.01)
            for distance in np.arange(face_height*.12, face_height*.60, step):
                color = sample(brow - down * distance)
                misses = misses+1 if color is None or np.linalg.norm(color-seed) > 30 else 0
                if misses >= 3:
                    depth = max(face_height*.06, distance-2*step)
                    break
        depths.append(depth)
    return brows - np.asarray(depths)[:,None]*down


def _segment_outline(frame, landmarks, down, horizontal, face_height):
    """Refine the upper silhouette locally; landmark features are hard seeds.

    GrabCut learns foreground/background colours from this face, rather than
    using a skin-colour threshold shared by people with different skin tones.
    """
    jaw = landmarks[:17]
    brow = landmarks[17:27].mean(axis=0)
    side = (jaw-brow) @ horizontal
    top = np.array([brow+horizontal*side.min()-down*face_height*.70,
                    brow+horizontal*side.max()-down*face_height*.70])
    envelope = np.vstack((jaw, top[::-1]))
    lo = np.maximum(0, np.floor(envelope.min(axis=0)-face_height*.12)).astype(int)
    hi = np.minimum(frame.shape[1::-1], np.ceil(envelope.max(axis=0)+face_height*.12)).astype(int)
    roi = frame[lo[1]:hi[1],lo[0]:hi[0]]
    labels = np.full(roi.shape[:2], cv2.GC_BGD, np.uint8)
    cv2.fillPoly(labels,[np.rint(envelope-lo).astype(np.int32)],cv2.GC_PR_FGD)
    core = cv2.convexHull(np.rint(landmarks-lo).astype(np.int32))
    cv2.fillConvexPoly(labels,core,cv2.GC_FGD)
    lab = cv2.cvtColor(roi,cv2.COLOR_BGR2LAB)
    seeds = landmarks[[19,20,23,24]]-down*face_height*.10-lo
    samples = [lab[int(np.clip(p[1],0,roi.shape[0]-1)),int(np.clip(p[0],0,roi.shape[1]-1)),0]
               for p in seeds]
    skin_light = float(np.median(samples))
    yy,xx = np.indices(roi.shape[:2])
    above_brows = ((xx+lo[0]-brow[0])*down[0]+(yy+lo[1]-brow[1])*down[1]) < -face_height*.08
    # Dark glasses are mandatory foreground; dark hair above the brows is
    # background. Without separate seeds, glasses can teach GrabCut to keep hair.
    skin_chroma = np.median([lab[int(np.clip(p[1],0,roi.shape[0]-1)),int(np.clip(p[0],0,roi.shape[1]-1)),1:]
                             for p in seeds],axis=0)
    chroma_distance = np.linalg.norm(lab[:,:,1:].astype(float)-skin_chroma,axis=2)
    labels[above_brows & (lab[:,:,0] < skin_light*.70) & (chroma_distance>12)
           & (labels!=cv2.GC_FGD)] = cv2.GC_BGD
    forehead_skin = (above_brows & (labels==cv2.GC_PR_FGD)
                     & (lab[:,:,0]>=skin_light*.40) & (chroma_distance<12))
    labels[forehead_skin] = cv2.GC_FGD
    # Border hair and background are samples for the competing colour model.
    # GrabCut initializes its colour clusters randomly. The same photograph
    # must keep the same boundary on every request, including concurrent ones.
    with _segmentation_lock:
        cv2.setRNGSeed(0)
        cv2.grabCut(roi,labels,None,np.zeros((1,65),np.float64),
                    np.zeros((1,65),np.float64),4,cv2.GC_INIT_WITH_MASK)
    selected = np.uint8((labels==cv2.GC_FGD)|(labels==cv2.GC_PR_FGD))*255
    contours,_ = cv2.findContours(selected,cv2.RETR_EXTERNAL,cv2.CHAIN_APPROX_SIMPLE)
    if not contours:
        raise ValueError('No face silhouette')
    contour = max(contours,key=cv2.contourArea)
    contour = cv2.approxPolyDP(contour,max(1,face_height*.006),True).reshape(-1,2)
    selected.fill(0)
    cv2.fillPoly(selected,[_smooth_outline(contour,passes=1)],255)
    result = np.zeros(frame.shape[:2],np.uint8)
    result[lo[1]:hi[1],lo[0]:hi[0]]=selected
    return result


def face_mask(frame, face):
    height, width = frame.shape[:2]
    x, y, w, h = (float(face[k]) for k in ('x', 'y', 'w', 'h'))
    if not all(np.isfinite([x, y, w, h])) or w <= 0 or h <= 0:
        raise ValueError('Invalid face geometry')
    if x + w <= 0 or y + h <= 0 or x >= width or y >= height:
        raise ValueError('Face geometry outside image')
    # Rounded temples, narrower jaw and chin; also covers the forehead.
    outline = np.array([[-.10,.05],[-.04,-.23],[.22,-.38],[.78,-.38],
                        [1.04,-.23],[1.10,.05],[1.08,.62],[.90,.96],
                        [.66,1.13],[.34,1.13],[.10,.96],[-.08,.62]])
    points = outline * [w, h] + [x, y]
    landmarks = None
    fitted = False
    if predictor is not None and min(w, h) >= 16:
        try:
            rect = dlib.rectangle(int(max(0,x)), int(max(0,y)),
                                  int(min(width-1,x+w)), int(min(height-1,y+h)))
            with dlib_lock:
                shape = predictor(cv2.cvtColor(frame, cv2.COLOR_BGR2RGB), rect)
            landmarks = np.array([(shape.part(i).x, shape.part(i).y) for i in range(68)], dtype=float)
            jaw, brow = landmarks[:17], landmarks[17:27].mean(axis=0)
            span = np.linalg.norm(jaw[-1] - jaw[0])
            if not .45*w <= span <= 1.8*w:
                raise ValueError('Unreliable landmarks')
            # Eyes provide a stable head-tilt axis, including faces turned sideways.
            eyes = landmarks[42:48].mean(axis=0)-landmarks[36:42].mean(axis=0)
            horizontal = eyes / max(np.linalg.norm(eyes), 1)
            down = np.array([-horizontal[1], horizontal[0]])
            if np.dot(jaw[8]-brow, down) < 0:
                down = -down
            face_height = max(h*.65, np.dot(jaw[8]-brow, down))
            forehead = _forehead_points(frame, landmarks, down, face_height)
            # Preserve the actual cheeks and jaw; no ellipse or convex-hull rounding.
            points = np.vstack((jaw, forehead[::-1]))
            fitted = True
        except Exception:
            pass  # Keep the conservative anatomical fallback, never remove the mask.
    mask = np.zeros((height, width), dtype=np.uint8)
    cv2.fillPoly(mask, [np.rint(points).astype(np.int32)], 255)
    if fitted:
        try:
            mask = _segment_outline(frame,landmarks,down,horizontal,face_height)
        except (cv2.error, ValueError):
            pass  # Preserve the landmark mask if colour segmentation is ambiguous.
        # Keep brows, eyes, nose and lips fully opaque even for unusual face poses.
        cv2.fillConvexPoly(mask, cv2.convexHull(np.rint(landmarks[17:]).astype(np.int32)), 255)
        # Spectacle frames/arms can extend beyond facial landmarks at the temples.
        # Widen only this narrow eye band, in the face's tilted coordinate system.
        center = landmarks[36:48].mean(axis=0)
        jaw_x = (landmarks[:17]-center) @ horizontal
        eye_y = (landmarks[36:48]-center) @ down
        left, right = jaw_x.min()-span*.09, jaw_x.max()+span*.09
        top, bottom = eye_y.min()-face_height*.025, eye_y.max()+face_height*.25
        guard = np.array([center+horizontal*a+down*b for a,b in
                          [(left+3,top),(right-3,top),(right,top+3),(right,bottom-3),
                           (right-3,bottom),(left+3,bottom),(left,bottom-3),(left,top+3)]])
        # Keep the individual hairline's concavities; a convex hull bridged
        # across hair and produced an oversized generic oval.
        lower_hull = cv2.convexHull(np.rint(np.vstack((guard,landmarks))).astype(np.int32)).reshape(-1,2)
        cv2.fillPoly(mask, [_smooth_outline(lower_hull,passes=1)], 255)
        # Rounded edges must never uncover the actual eyes, brows, nose or lips.
        cv2.fillConvexPoly(mask, cv2.convexHull(np.rint(landmarks).astype(np.int32)), 255)
        contours,_ = cv2.findContours(mask,cv2.RETR_EXTERNAL,cv2.CHAIN_APPROX_SIMPLE)
        contour = max(contours,key=cv2.contourArea)
        contour = cv2.approxPolyDP(contour,max(1,face_height*.006),True).reshape(-1,2)
        mask.fill(0)
        cv2.fillPoly(mask,[_smooth_outline(contour,passes=2)],255)
        cv2.fillConvexPoly(mask,cv2.convexHull(np.rint(landmarks).astype(np.int32)),255)
    # No outward dilation or feathering: every pixel outside the selected
    # facial contour remains unchanged. Facial features remain fully opaque.
    return mask


def blur_private_face(frame, face):
    mask = face_mask(frame, face)
    ys, xs = np.nonzero(mask)
    if not len(xs):
        raise ValueError('Empty privacy mask')
    left, right, top, bottom = xs.min(), xs.max()+1, ys.min(), ys.max()+1
    roi = frame[top:bottom, left:right]
    # Very coarse resampling removes features before smoothing the result.
    tiny = cv2.resize(roi, (3,3), interpolation=cv2.INTER_AREA)
    blurred = cv2.resize(tiny, (roi.shape[1],roi.shape[0]), interpolation=cv2.INTER_LINEAR)
    alpha = mask[top:bottom,left:right,None].astype(np.float32)/255
    frame[top:bottom,left:right] = np.rint(blurred*alpha + roi*(1-alpha)).astype(np.uint8)
