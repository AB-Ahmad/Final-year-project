import cv2
import numpy as np

# === CONFIG ===
INPUT_IMAGE = 'Test_images/rotate.jpg'     # replace with your actual image
OUTPUT_IMAGE = 'aligned_sheet.jpg'
DEBUG_THRESH = 'debug_thresh.jpg'
DEBUG_CONTOURS = 'debug_contours.jpg'
WARP_WIDTH, WARP_HEIGHT = 1000, 1400        # based on your template size

def detect_markers(image):
    gray = cv2.cvtColor(image, cv2.COLOR_BGR2GRAY)
    _, thresh = cv2.threshold(gray, 50, 255, cv2.THRESH_BINARY_INV)

    # Save threshold image for inspection
    cv2.imwrite(DEBUG_THRESH, thresh)
    print(f"🧪 Saved binary threshold image: {DEBUG_THRESH}")

    contours, _ = cv2.findContours(thresh, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)

    marker_candidates = []
    for cnt in contours:
        approx = cv2.approxPolyDP(cnt, 0.02 * cv2.arcLength(cnt, True), True)
        if len(approx) == 4:
            x, y, w, h = cv2.boundingRect(approx)
            area = w * h
            aspect = w / h
            # RELAXED FILTER for testing
            if 10 < w < 200 and 10 < h < 200 and 0.7 < aspect < 1.3:
                marker_candidates.append((x + w // 2, y + h // 2))  # center

    # Debug: draw contours
    debug_img = image.copy()
    for pt in marker_candidates:
        cv2.circle(debug_img, (int(pt[0]), int(pt[1])), 10, (0, 0, 255), -1)
    cv2.imwrite(DEBUG_CONTOURS, debug_img)
    print(f"🧪 Saved debug contour visualization: {DEBUG_CONTOURS}")

    if len(marker_candidates) != 4:
        raise Exception(f"Expected 4 markers, but found {len(marker_candidates)}")

    return np.array(sorted(marker_candidates, key=lambda pt: pt[1]))  # sort by y

def order_points(pts):
    """Order: TL, TR, BL, BR"""
    pts = sorted(pts, key=lambda p: (p[1], p[0]))
    top_pts = sorted(pts[:2], key=lambda p: p[0])
    bottom_pts = sorted(pts[2:], key=lambda p: p[0])
    return np.array([top_pts[0], top_pts[1], bottom_pts[0], bottom_pts[1]], dtype="float32")

def warp_image(image, src_pts, size=(1000, 1400)):
    dst_pts = np.array([
        [0, 0],
        [size[0]-1, 0],
        [0, size[1]-1],
        [size[0]-1, size[1]-1]
    ], dtype="float32")
    matrix = cv2.getPerspectiveTransform(src_pts, dst_pts)
    warped = cv2.warpPerspective(image, matrix, size)
    return warped

# === RUN ===
image = cv2.imread(INPUT_IMAGE)
try:
    markers = detect_markers(image)
    ordered_markers = order_points(markers)
    aligned = warp_image(image, ordered_markers, size=(WARP_WIDTH, WARP_HEIGHT))
    cv2.imwrite(OUTPUT_IMAGE, aligned)
    print(f"✅ Aligned sheet saved as {OUTPUT_IMAGE}")
except Exception as e:
    print("❌ Error:", e)
