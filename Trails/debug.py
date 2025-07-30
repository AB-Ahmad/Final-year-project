import cv2
import numpy as np
from ultralytics import YOLO

# Configuration
MODEL_PATH = 'yolov8_bubbles_best.pt'
IMAGE_PATH = 'DATASETS/sheet01.jpg'
DEBUG_OUTPUT = 'debug_output1.jpg'

# Template setup (adjust these)
TEMPLATE = {
    "q1-15": {
        "position": [0.12, 0.30, 0.42, 0.90],  # Left section (x1,y1,x2,y2)
        "questions": 15
    },
    "q16-30": {
        "position": [0.52, 0.30, 0.82, 0.90],  # Right section
        "questions": 15
    }
}

def visualize_mapping():
    # Load model and image
    model = YOLO(MODEL_PATH)
    image = cv2.imread(IMAGE_PATH)
    h, w = image.shape[:2]
    
    # Run prediction
    results = model.predict(image)
    boxes = results[0].boxes.xyxy.cpu().numpy()
    classes = results[0].boxes.cls.cpu().numpy()
    confs = results[0].boxes.conf.cpu().numpy()
    
    # Draw template regions
    for section_name, section in TEMPLATE.items():
        x1, y1, x2, y2 = section["position"]
        abs_x1, abs_y1 = int(x1 * w), int(y1 * h)
        abs_x2, abs_y2 = int(x2 * w), int(y2 * h)
        
        # Draw section boundary
        cv2.rectangle(image, (abs_x1, abs_y1), (abs_x2, abs_y2), (0, 255, 0), 2)
        
        # Draw question dividers
        section_height = abs_y2 - abs_y1
        for q in range(section["questions"] + 1):
            y = abs_y1 + int((q / section["questions"]) * section_height)
            cv2.line(image, (abs_x1, y), (abs_x2, y), (255, 0, 0), 1)
    
    # Draw predictions with question numbers
    for box, cls, conf in zip(boxes, classes, confs):
        x1, y1, x2, y2 = map(int, box)
        center_x = (x1 + x2) // 2
        center_y = (y1 + y2) // 2
        
        # Determine question number
        q_num = None
        for section_name, section in TEMPLATE.items():
            sx1, sy1, sx2, sy2 = section["position"]
            abs_sx1, abs_sy1 = int(sx1 * w), int(sy1 * h)
            abs_sx2, abs_sy2 = int(sx2 * w), int(sy2 * h)
            
            if (abs_sx1 <= center_x <= abs_sx2 and 
                abs_sy1 <= center_y <= abs_sy2):
                
                section_height = abs_sy2 - abs_sy1
                rel_y = center_y - abs_sy1
                q_index = min(int((rel_y / section_height) * section["questions"]), section["questions"]-1)
                
                q_num = q_index + 1 
                if section_name == "q16-30":
                    q_num += 15
                break
        
        # Draw detection
        color = (0, 0, 255) if q_num is None else (255, 0, 255)
        cv2.rectangle(image, (x1, y1), (x2, y2), color, 2)
        
        label = f"Q{q_num if q_num else '?'}:{chr(65 + int(cls))}({conf:.2f})"
        cv2.putText(image, label, (x1, y1 - 10), 
                   cv2.FONT_HERSHEY_SIMPLEX, 0.5, color, 1)
    
    # Save debug image
    cv2.imwrite(DEBUG_OUTPUT, image)
    print(f"Debug visualization saved to {DEBUG_OUTPUT}")

if __name__ == "__main__":
    visualize_mapping()