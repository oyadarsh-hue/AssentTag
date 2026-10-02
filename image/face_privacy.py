"""Face-shaped privacy masks, shared by feed, notifications and stories."""
import cv2
import dlib
import numpy as np
from face_utils import predictor, dlib_lock


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
    # Hair reaches lower at the temples: do not project outer brow points as
    # high as the center of the forehead (which produced pointed hair spikes).
    position = np.linspace(0, 1, len(brows))
    caps = face_height * (.08 + .40 * np.sin(np.pi*position)**.65)
    for index, brow in enumerate(brows):
        # Start above the eyebrow itself, so dark eyebrow hairs are not skin seeds.
        seed = sample(brow - down * face_height * .10)
        depth = face_height * .43
        misses = 0
        if seed is not None:
            for distance in np.arange(face_height*.16, face_height*.53, max(1,face_height*.015)):
                color = sample(brow - down * distance)
                misses = misses+1 if color is None or np.linalg.norm(color-seed) > 34 else 0
                if misses >= 3:
                    # Retain a small overlap at the boundary instead of leaving a skin strip.
                    depth = max(face_height*.22, distance)
                    break
        depths.append(min(depth, caps[index]))
    # Smooth isolated lighting changes while retaining the individual's hairline slope.
    depths = np.convolve(np.pad(depths, (1,1), mode='edge'), [1/3]*3, mode='valid')
    depths = np.minimum(depths, caps)
    return brows - depths[:,None]*down


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
        # Keep brows, eyes, nose and lips fully opaque even for unusual face poses.
        cv2.fillConvexPoly(mask, cv2.convexHull(np.rint(landmarks[17:]).astype(np.int32)), 255)
        # Spectacle frames/arms can extend beyond facial landmarks at the temples.
        # Widen only this narrow eye band, in the face's tilted coordinate system.
        center = landmarks[36:48].mean(axis=0)
        jaw_x = (landmarks[:17]-center) @ horizontal
        brow_y = (landmarks[17:27]-center) @ down
        eye_y = (landmarks[36:48]-center) @ down
        left, right = jaw_x.min()-span*.07, jaw_x.max()+span*.07
        top, bottom = brow_y.min()-face_height*.05, eye_y.max()+face_height*.15
        guard = np.array([center+horizontal*((left+right)/2+(right-left)/2*np.cos(t))
                          +down*((top+bottom)/2+(bottom-top)/2*np.sin(t))
                          for t in np.linspace(0,2*np.pi,40,endpoint=False)])
        # Join the guard to the fitted outline so protection has a continuous
        # silhouette rather than rectangular wings beside the eyes.
        outline = np.vstack((points, guard, landmarks[17:]))
        hull = cv2.convexHull(np.rint(outline).astype(np.int32)).reshape(-1,2)
        mask.fill(0)
        cv2.fillPoly(mask, [_smooth_outline(hull)], 255)
        # Rounded edges must never uncover the actual eyes, brows, nose or lips.
        cv2.fillConvexPoly(mask, cv2.convexHull(np.rint(landmarks).astype(np.int32)), 255)
    padding = max(2, round(min(w,h)*(.015 if fitted else .045)))
    kernel = cv2.getStructuringElement(cv2.MORPH_ELLIPSE, (padding*2+1, padding*2+1))
    mask = cv2.dilate(mask, kernel)
    # Feather only OUTSIDE the opaque core: facial detail is never blended back in.
    feather = cv2.GaussianBlur(mask, (padding*2+1, padding*2+1), 0)
    return np.maximum(mask, feather)


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
