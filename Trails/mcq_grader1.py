import cv2
import json
from ultralytics import YOLO
import os

# Configuration
MODEL_PATH = 'yolov8_bubbles_best.pt'
SAMPLE_IMAGE = 'DATASETS/sheet27.jpg'  # Using your actual image name
OUTPUT_JSON = 'results2.json'
SAVE_IMAGE = 'output2.jpg'  # Instead of showing, we'll save

# Adjusted template (you'll need to fine-tune these)
TEMPLATE = {
    "q1-15": {
        "position": [0.15, 0.25, 0.45, 0.85],  # Try adjusting these
        "questions": 15
    },
    "q16-30": {
        "position": [0.55, 0.25, 0.85, 0.85],
        "questions": 15
    } 
}

# Make sure these are the actual correct answers
CORRECT_ANSWERS = {
    1: "A", 2: "A", 3: "A", 4: "A", 5: "A",
    6: "A", 7: "A", 8: "C", 9: "A", 10: "A",
    11: "A", 12: "A", 13: "C", 14: "A", 15: "A",
    16: "A", 17: "A", 18: "C", 19: "A", 20: "A",
    21: "A", 22: "A", 23: "C", 24: "A", 25: "A",
    26: "A", 27: "A", 28: "C", 29: "A", 30: "A"
}

def predict_sheet(image_path):
    model = YOLO(MODEL_PATH)
    results = model.predict(image_path)
    return results[0].boxes.xyxy, results[0].boxes.conf, results[0].boxes.cls

def map_to_questions(boxes, classes, image_size):
    width, height = image_size
    questions = {i: [] for i in range(1, 31)}
    
    for box, cls in zip(boxes, classes):
        x_center = (box[0] + box[2]) / 2
        y_center = (box[1] + box[3]) / 2
        option = chr(65 + int(cls))
        
        for section_name, section in TEMPLATE.items():
            x1, y1, x2, y2 = section["position"]
            abs_x1, abs_y1 = x1 * width, y1 * height
            abs_x2, abs_y2 = x2 * width, y2 * height
            
            if (abs_x1 <= x_center <= abs_x2 and 
                abs_y1 <= y_center <= abs_y2):
                
                section_height = abs_y2 - abs_y1
                rel_y = y_center - abs_y1
                q_index = min(int((rel_y / section_height) * section["questions"]), section["questions"]-1)
                
                q_num = q_index + 1 
                if section_name == "q16-30":
                    q_num += 15
                
                # Only keep highest confidence answer per question
                if not questions[q_num] or conf > questions[q_num][1]:
                    questions[q_num] = [option, float(conf)]
    
    return questions

def grade_answers(question_map):
    score = 0
    results = []
    
    for q_num, (marked, conf) in question_map.items():
        correct = CORRECT_ANSWERS.get(q_num, "?")
        
        if marked == correct:
            status = "Correct"
            score += 1
        else:
            status = f"Wrong (marked {marked})"
        
        results.append({
            "question": q_num,
            "marked": marked,
            "correct": correct,
            "status": status,
            "confidence": conf
        })
    
    return {
        "score": score,
        "total": len(CORRECT_ANSWERS),
        "details": results
    }

def save_visualization(image_path, boxes, classes):
    image = cv2.imread(image_path)
    class_names = ['A', 'B', 'C', 'D', 'E',"INVALID"]
    
    for box, cls in zip(boxes, classes):
        x1, y1, x2, y2 = map(int, box)
        cv2.rectangle(image, (x1, y1), (x2, y2), (0, 255, 0), 2)
        cv2.putText(image, class_names[int(cls)], (x1, y1-10),
                   cv2.FONT_HERSHEY_SIMPLEX, 0.9, (0,255,0), 2)
    
    cv2.imwrite(SAVE_IMAGE, image)
    print(f"Visualization saved to {SAVE_IMAGE}")

def main():
    if not os.path.exists(SAMPLE_IMAGE):
        print(f"Error: Image file {SAMPLE_IMAGE} not found!")
        return
    
    # 1. Run prediction
    boxes, confs, classes = predict_sheet(SAMPLE_IMAGE)
    print(f"Detected {len(boxes)} answer marks")
    
    # 2. Map to questions (using only highest confidence per question)
    image = cv2.imread(SAMPLE_IMAGE)
    question_map = {}
    for q_num in range(1, 31):
        question_map[q_num] = ["", 0.0]  # [answer, confidence]
    
    for box, conf, cls in zip(boxes, confs, classes):
        x_center = (box[0] + box[2]) / 2
        y_center = (box[1] + box[3]) / 2
        option = chr(65 + int(cls))
        
        for section_name, section in TEMPLATE.items():
            x1, y1, x2, y2 = section["position"]
            abs_x1, abs_y1 = x1 * image.shape[1], y1 * image.shape[0]
            abs_x2, abs_y2 = x2 * image.shape[1], y2 * image.shape[0]
            
            if (abs_x1 <= x_center <= abs_x2 and 
                abs_y1 <= y_center <= abs_y2):
                
                section_height = abs_y2 - abs_y1
                rel_y = y_center - abs_y1
                q_index = min(int((rel_y / section_height) * section["questions"]), section["questions"]-1)
                
                q_num = q_index + 1 
                if section_name == "q16-30":
                    q_num += 15
                
                if conf > question_map[q_num][1]:
                    question_map[q_num] = [option, float(conf)]
    
    # 3. Grade answers
    results = grade_answers(question_map)
    
    # 4. Save results
    print(f"\nScore: {results['score']}/{results['total']}")
    for item in results["details"]:
        print(f"Q{item['question']}: {item['status']} (conf: {item['confidence']:.2f})")
    
    save_visualization(SAMPLE_IMAGE, boxes, classes)
    with open(OUTPUT_JSON, 'w') as f:
        json.dump(results, f, indent=2)
    print(f"\nDetailed results saved to {OUTPUT_JSON}")

if __name__ == "__main__":
    main()