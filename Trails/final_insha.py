import os
import cv2
import numpy as np
from scipy.spatial import KDTree
from sklearn.cluster import DBSCAN

# CONFIGURATION
LABEL_DIR = r"C:\\Users\\Ahmad Bala\\runs\\detect\\predict12\\labels"
IMAGE_DIR = r"C:\\Users\\Ahmad Bala\\Desktop\\MCQ PJ\\mcq-grading.v2i.yolov8\\test\\images"
OUTPUT_DIR = "graded_visuals"
DEBUG_MODE = True

os.makedirs(OUTPUT_DIR, exist_ok=True)

# Answer key
answer_key = {
    f"q{i}": opt for i, opt in zip(range(1, 31), 
    ["a", "a", "c", "d", "e",
     "a", "b", "c", "d", "e",
     "a", "b", "c", "d", "e",
     "a", "b", "c", "d", "e",
     "a", "b", "c", "d", "e",
     "a", "b", "c", "d", "e"])
}

def normalize_sheet(image):
    """Apply perspective correction using registration marks"""
    gray = cv2.cvtColor(image, cv2.COLOR_BGR2GRAY)
    blurred = cv2.GaussianBlur(gray, (5, 5), 0)
    edged = cv2.Canny(blurred, 50, 150)
    
    # Find registration marks (implement your specific mark detection)
    contours, _ = cv2.findContours(edged, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)
    marks = []
    for cnt in contours:
        area = cv2.contourArea(cnt)
        if 100 < area < 1000:
            x, y, w, h = cv2.boundingRect(cnt)
            marks.append((x + w//2, y + h//2))
    
    if len(marks) >= 4:
        src_pts = np.array(sorted(marks, key=lambda p: (p[1], p[0]))[:4], dtype="float32")
        h, w = image.shape[:2]
        dst_pts = np.array([[0,0], [w,0], [w,h], [0,h]], dtype="float32")
        M = cv2.getPerspectiveTransform(src_pts, dst_pts)
        return cv2.warpPerspective(image, M, (w, h))
    return image

def detect_zones_projection(image):
    """Use projection profiles to detect answer zones"""
    gray = cv2.cvtColor(image, cv2.COLOR_BGR2GRAY)
    _, thresh = cv2.threshold(gray, 200, 255, cv2.THRESH_BINARY_INV)
    
    # Horizontal projection
    horiz_proj = np.sum(thresh, axis=1)
    threshold = np.mean(horiz_proj) * 2
    zones = []
    in_zone = False
    start_y = 0
    
    for i, val in enumerate(horiz_proj):
        if val > threshold and not in_zone:
            in_zone = True
            start_y = i
        elif val <= threshold and in_zone:
            in_zone = False
            if i - start_y > 50:  # Minimum zone height
                zones.append((0, start_y, image.shape[1], i))
    
    return zones[:2]  # Return top 2 zones

def load_bubbles(label_path, image_shape):
    """Load YOLO detections and convert to image coordinates"""
    bubbles = []
    with open(label_path, "r") as f:
        for line in f:
            parts = line.strip().split()
            if len(parts) == 5:
                _, x_c, y_c, w_c, h_c = map(float, parts)
                x = int(x_c * image_shape[1])
                y = int(y_c * image_shape[0])
                w = int(w_c * image_shape[1])
                h = int(h_c * image_shape[0])
                conf = 0.9  # Default confidence if not provided
                bubbles.append((x, y, w, h, conf))
    return bubbles

def generate_dynamic_anchors(bubbles, zone, base_q_index):
    """Generate anchors based on actual bubble positions"""
    x1, y1, x2, y2 = zone
    zone_bubbles = [(x, y) for x, y, w, h, conf in bubbles 
                   if x1 <= x <= x2 and y1 <= y <= y2]
    
    if not zone_bubbles:
        return {}
    
    # Cluster bubbles into questions
    clustering = DBSCAN(eps=50, min_samples=3).fit(zone_bubbles)
    anchors = {}
    
    for label in set(clustering.labels_):
        if label == -1:  # Noise
            continue
            
        # Get bubbles for this question
        question_bubbles = [b for b, l in zip(bubbles, clustering.labels_) 
                          if l == label and b[4] > 0.7]  # Confidence check
        
        if not question_bubbles:
            continue
            
        # Sort vertically to assign options (A-E)
        question_bubbles.sort(key=lambda b: b[1])
        qnum = base_q_index + label + 1
        
        for i, (x, y, w, h, conf) in enumerate(question_bubbles[:5]):  # Max 5 options
            anchors[f"q{qnum}_{chr(97 + i)}"] = (x + w//2, y + h//2)
    
    return anchors

def match_bubbles_to_anchors(bubbles, anchors):
    """Improved matching using spatial indexing"""
    if not anchors:
        return {}
    
    anchor_points = np.array(list(anchors.values()))
    anchor_keys = list(anchors.keys())
    tree = KDTree(anchor_points)
    
    matches = {}
    for x, y, w, h, conf in bubbles:
        # Find nearest anchors within distance threshold
        dists, indices = tree.query([x + w//2, y + h//2], 
                                  k=3, 
                                  distance_upper_bound=50)
        
        if np.isfinite(dists[0]):
            key = anchor_keys[indices[0]]
            matches.setdefault(key, []).append((x + w//2, y + h//2, conf))
    
    return matches

def grade_answers(matches, answer_key):
    """Calculate score based on matched bubbles"""
    score = 0
    detailed = {}
    
    for q in answer_key:
        # Find all options selected for this question
        selected = [k.split("_")[1] for k in matches if k.startswith(q + "_")]
        
        if len(selected) == 1:
            if selected[0] == answer_key[q]:
                detailed[q] = "✔"
                score += 1
            else:
                detailed[q] = "✘"
        elif len(selected) > 1:
            detailed[q] = "?"
        else:
            detailed[q] = "○"
    
    return score, detailed

def visualize_results(image, matches, anchors, score, detailed):
    """Draw visualization with results"""
    # Draw all anchors
    for key, (x, y) in anchors.items():
        cv2.circle(image, (x, y), 5, (0, 255, 0), 1)
        if DEBUG_MODE:
            cv2.putText(image, key, (x - 20, y - 10), 
                       cv2.FONT_HERSHEY_SIMPLEX, 0.4, (0, 255, 0), 1)
    
    # Draw matches and grading
    for key, points in matches.items():
        q, opt = key.split("_")
        ax, ay = anchors[key]
        
        # Draw line from anchor to bubble
        for x, y, conf in points:
            cv2.line(image, (ax, ay), (x, y), (0, 0, 255), 1)
            cv2.circle(image, (x, y), 8, (0, 0, 255), 2)
        
        # Draw grading symbol
        symbol = detailed.get(q, "?")
        color = (0, 255, 0) if symbol == "✔" else \
               (0, 0, 255) if symbol in ("✘", "?") else \
               (200, 200, 200)
        
        cv2.putText(image, f"{q} {symbol}", (ax - 15, ay - 20), 
                   cv2.FONT_HERSHEY_SIMPLEX, 0.6, color, 2)
    
    # Add score
    cv2.putText(image, f"Score: {score}/30", (20, 40), 
               cv2.FONT_HERSHEY_SIMPLEX, 1, (0, 0, 255), 2)
    return image

def process_sheet(label_path, image_path):
    """Main processing pipeline"""
    image = cv2.imread(image_path)
    if image is None:
        print(f"❌ Could not load image: {image_path}")
        return
    
    # Preprocessing
    image = normalize_sheet(image)
    h, w = image.shape[:2]
    
    # Load YOLO detections
    bubbles = load_bubbles(label_path, (h, w))
    
    # Detect zones
    zones = detect_zones_projection(image)
    if len(zones) < 2:
        print(f"⚠️ Only {len(zones)} zones detected")
        return
    
    # Generate anchors for each zone
    anchors_top = generate_dynamic_anchors(bubbles, zones[0], 0)
    anchors_bottom = generate_dynamic_anchors(bubbles, zones[1], 15)
    anchors = {**anchors_top, **anchors_bottom}
    
    # Match bubbles to anchors
    matches = match_bubbles_to_anchors(bubbles, anchors)
    
    # Grade answers
    score, detailed = grade_answers(matches, answer_key)
    
    # Visualize results
    result_img = visualize_results(image.copy(), matches, anchors, score, detailed)
    
    # Save output
    out_path = os.path.join(OUTPUT_DIR, os.path.basename(image_path))
    cv2.imwrite(out_path, result_img)
    
    print(f"✅ {os.path.basename(image_path)}: {score}/30")
    if DEBUG_MODE:
        print("📋 Grading details:", detailed)

# Main execution
if __name__ == "__main__":
    for label_file in os.listdir(LABEL_DIR):
        if not label_file.endswith(".txt"):
            continue
        
        sid = os.path.splitext(label_file)[0]
        label_path = os.path.join(LABEL_DIR, label_file)
        image_path = os.path.join(IMAGE_DIR, f"{sid}.jpg")
        
        if os.path.exists(image_path):
            process_sheet(label_path, image_path)