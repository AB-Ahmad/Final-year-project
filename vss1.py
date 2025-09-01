import os
import cv2
import numpy as np
from ultralytics import YOLO
from sklearn.cluster import KMeans
import json

# ================= CONFIGURATION =================
MCQ_MODEL_PATH = "models/yolov8_bubbles_best.pt"
INPUT_IMAGE = "Test_images/alaa.jpg"
OUTPUT_DIR = "outputs"
NUM_QUESTIONS = 30
NUM_OPTIONS = 5
CLASS_NAMES = ['A', 'B', 'C', 'D', 'E', 'INVALID']

CORRECT_ANSWERS = {
    1: "B", 2: "C", 3: "C", 4: "B", 5: "D",
    6: "D", 7: "B", 8: "C", 9: "B", 10: "C",
    11: "B", 12: "B", 13: "C", 14: "B", 15: "B",
    16: "A", 17: "B", 18: "E", 19: "C", 20: "E",
    21: "B", 22: "C", 23: "A", 24: "D", 25: "B",
    26: "B", 27: "E", 28: "C", 29: "A", 30: "A"
}

os.makedirs(OUTPUT_DIR, exist_ok=True)

# ================= HELPER FUNCTIONS =================
def load_yolo_model(model_path):
    return YOLO(model_path)

def predict_bubbles(model, img):
    results = model(img)[0]
    detections = []
    for box in results.boxes:
        x1, y1, x2, y2 = map(int, box.xyxy[0])
        x_c = int((x1 + x2) / 2)
        y_c = int((y1 + y2) / 2)
        cls = CLASS_NAMES[int(box.cls)]
        conf = float(box.conf)
        detections.append((x_c, y_c, cls, conf, (x1, y1, x2, y2)))
    return detections

def apply_mapping(detections, num_questions=NUM_QUESTIONS, num_options=NUM_OPTIONS):
    if not detections:
        return {}
    
    coords = np.array([[det[1]] for det in detections])  # y_center
    kmeans = KMeans(n_clusters=num_questions, random_state=0).fit(coords)
    row_labels = kmeans.labels_

    mapping = {}
    for row in range(num_questions):
        row_items = [(det, row_labels[i]) for i, det in enumerate(detections) if row_labels[i] == row]
        if not row_items:
            continue

        # sort left-right
        row_items = sorted(row_items, key=lambda x: x[0][0])

        q_num = row + 1
        for idx, (det, _) in enumerate(row_items[:num_options]):
            x, y, cls, conf, box = det
            opt = chr(ord('a') + idx)  # a,b,c,d,e
            q_label = f"q{q_num}_{opt}"
            mapping[q_label] = {"class": cls, "conf": conf, "bbox": box}
    return mapping

def visualize_mapping(img, mapping, save_path):
    for q_label, det in mapping.items():
        x1, y1, x2, y2 = det["bbox"]
        cls = det["class"]
        cv2.rectangle(img, (x1, y1), (x2, y2), (0, 255, 0), 2)
        cv2.putText(img, f"{q_label} ({cls})", (x1, y1-5),
                    cv2.FONT_HERSHEY_SIMPLEX, 0.5, (0,0,255), 2)
    cv2.imwrite(save_path, img)
    print(f"✅ Saved mapped visualization: {save_path}")

def grade_answers(mapping):
    question_map = {i: "-" for i in range(1, NUM_QUESTIONS+1)}
    for q_label, det in mapping.items():
        q_num = int(q_label[1:q_label.index('_')])
        cls = det["class"]
        # choose the first detected class (option a-e) as marked
        if question_map[q_num] == "-":
            question_map[q_num] = cls

    score = 0
    results_list = []
    for q_num, marked in question_map.items():
        correct = CORRECT_ANSWERS.get(q_num, "?")
        if marked == correct:
            status = "Correct"
            score += 1
        elif marked == "INVALID":
            status = "Invalid Mark"
        elif marked != "-":
            status = f"Wrong (marked {marked})"
        else:
            status = "Blank"
        results_list.append({
            "question": q_num,
            "marked": marked,
            "correct": correct,
            "status": status
        })
    return {"score": score, "total": NUM_QUESTIONS, "details": results_list}

# ================= MAIN =================
if __name__ == "__main__":
    img = cv2.imread(INPUT_IMAGE)
    model = load_yolo_model(MCQ_MODEL_PATH)

    # Step 1: Predict bubbles
    detections = predict_bubbles(model, img)
    cv2.imwrite(os.path.join(OUTPUT_DIR, "yolo_detections.jpg"), img.copy())

    # Step 2: Map bubbles to questions
    mapping = apply_mapping(detections)

    # Step 3: Visualize mapping
    vis_img = img.copy()
    visualize_mapping(vis_img, mapping, os.path.join(OUTPUT_DIR, "mapped_qs.jpg"))

    # Step 4: Grade answers
    results = grade_answers(mapping)

    # Save results
    with open(os.path.join(OUTPUT_DIR, "results.json"), "w") as f:
        json.dump(results, f, indent=2)

    print(f"\n📊 Score: {results['score']} / {results['total']}")
    print("✅ All outputs saved in folder:", OUTPUT_DIR)
