import cv2
import numpy as np
from ultralytics import YOLO
import json

def process_answer_sheet(image_path):
    # Load image and model
    image = cv2.imread(image_path)
    gray = cv2.cvtColor(image, cv2.COLOR_BGR2GRAY)
    model = YOLO('yolov8_bubbles_best.pt')
    
    # Step 1: Detect answer sections using contours
    blurred = cv2.GaussianBlur(gray, (5,5), 0)
    _, thresh = cv2.threshold(blurred, 0, 255, cv2.THRESH_BINARY_INV + cv2.THRESH_OTSU)
    
    # Find contours of answer sections
    contours, _ = cv2.findContours(thresh, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)
    answer_sections = []
    
    for cnt in contours:
        area = cv2.contourArea(cnt)
        if area > 50000:  # Filter for large contours (answer sections)
            x,y,w,h = cv2.boundingRect(cnt)
            answer_sections.append((x,y,w,h))
    
    # Sort sections left to right
    answer_sections = sorted(answer_sections, key=lambda x: x[0])
    
    if len(answer_sections) != 2:
        raise ValueError("Could not detect exactly 2 answer sections")
    
    # Step 2: Detect individual question rows in each section
    def detect_rows(section_img):
        edges = cv2.Canny(section_img, 50, 150)
        lines = cv2.HoughLinesP(edges, 1, np.pi/180, threshold=50,
                              minLineLength=section_img.shape[1]//2,
                              maxLineGap=10)
        if lines is None:
            return None
        
        y_coords = sorted({(line[0][1] + line[0][3])//2 for line in lines})
        return [y for y in y_coords if 20 < y < section_img.shape[0]-20]
    
    # Process left section (Q1-15)
    left_x, left_y, left_w, left_h = answer_sections[0]
    left_section = gray[left_y:left_y+left_h, left_x:left_x+left_w]
    left_rows = detect_rows(left_section)
    
    # Process right section (Q16-30)
    right_x, right_y, right_w, right_h = answer_sections[1]
    right_section = gray[right_y:right_y+right_h, right_x:right_x+right_w]
    right_rows = detect_rows(right_section)
    
    # Step 3: Create dynamic question mapping
    question_areas = {}
    
    # Map left section questions (Q1-15)
    for i in range(min(15, len(left_rows)-1)):
        y_start = left_rows[i] + left_y
        y_end = left_rows[i+1] + left_y
        question_areas[i+1] = {
            'x1': left_x,
            'y1': y_start,
            'x2': left_x + left_w,
            'y2': y_end,
            'options': {
                'A': (left_x + int(left_w*0.1), 
                'B': (left_x + int(left_w*0.3)),
                'C': (left_x + int(left_w*0.5)),
                'D': (left_x + int(left_w*0.7)),
                'E': (left_x + int(left_w*0.9))
            }
        }
    
    # Map right section questions (Q16-30)
    for i in range(min(15, len(right_rows)-1)):
        y_start = right_rows[i] + right_y
        y_end = right_rows[i+1] + right_y
        question_areas[i+16] = {
            'x1': right_x,
            'y1': y_start,
            'x2': right_x + right_w,
            'y2': y_end,
            'options': {
                'A': (right_x + int(right_w*0.1)), 
                'B': (right_x + int(right_w*0.3)),
                'C': (right_x + int(right_w*0.5)),
                'D': (right_x + int(right_w*0.7)),
                'E': (right_x + int(right_w*0.9))
            }
        }
        
    
    # Step 4: Run detection and map to questions
    results = model.predict(image)
    boxes = results[0].boxes.xyxy.cpu().numpy()
    classes = results[0].boxes.cls.cpu().numpy()
    confs = results[0].boxes.conf.cpu().numpy()
    
    # Create visualization
    debug_img = image.copy()
    cv2.drawContours(debug_img, contours, -1, (0,255,0), 3)
    
    # Process detections
    graded_answers = {}
    for box, cls, conf in zip(boxes, classes, confs):
        x1, y1, x2, y2 = map(int, box)
        center_x, center_y = (x1+x2)//2, (y1+y2)//2
        option = chr(65 + int(cls))
        
        # Find which question this belongs to
        for q_num, area in question_areas.items():
            if (area['y1'] <= center_y <= area['y2'] and 
                area['x1'] <= center_x <= area['x2']):
                
                # Determine closest option
                min_dist = float('inf')
                selected_option = None
                for opt, opt_x in area['options'].items():
                    dist = abs(center_x - opt_x)
                    if dist < min_dist:
                        min_dist = dist
                        selected_option = opt
                
                if min_dist < 50:  # Max allowed distance from option center
                    if q_num not in graded_answers or conf > graded_answers[q_num]['confidence']:
                        graded_answers[q_num] = {
                            'option': selected_option,
                            'confidence': float(conf),
                            'box': [x1,y1,x2,y2]
                        }
        
        # Draw detection on debug image
        color = (255,0,255) if option in ['A','B','C','D','E'] else (0,0,255)
        cv2.rectangle(debug_img, (x1,y1), (x2,y2), color, 2)
        cv2.putText(debug_img, option, (x1,y1-10), 
                   cv2.FONT_HERSHEY_SIMPLEX, 0.9, color, 2)
    
    # Draw question areas on debug image
    for q_num, area in question_areas.items():
        cv2.rectangle(debug_img, (area['x1'],area['y1']), 
                     (area['x2'],area['y2']), (255,255,0), 1)
        cv2.putText(debug_img, f"Q{q_num}", (area['x1'],area['y1']-10),
                   cv2.FONT_HERSHEY_SIMPLEX, 0.5, (255,255,0), 1)
    
    # Save outputs
    cv2.imwrite('contour_debug.jpg', debug_img)
    
    # Grade answers (using your CORRECT_ANSWERS dictionary)
    final_results = grade_answers(graded_answers, CORRECT_ANSWERS)
    with open('contour_results.json', 'w') as f:
        json.dump(final_results, f, indent=2)
    
    return final_results

def grade_answers(detections, correct_answers):
    results = []
    score = 0
    
    for q_num in range(1, 31):
        detected = detections.get(q_num, None)
        correct = correct_answers.get(q_num, "?")
        
        if not detected:
            status = "Unanswered"
        else:
            if detected['option'] == correct:
                status = "Correct"
                score += 1
            else:
                status = f"Wrong (marked {detected['option']})"
        
        results.append({
            "question": q_num,
            "status": status,
            "marked": detected['option'] if detected else None,
            "correct": correct,
            "confidence": detected['confidence'] if detected else 0
        })
    
    return {
        "score": score,
        "total": len(correct_answers),
        "details": results
    }

# Example usage
if __name__ == "__main__":
    results = process_answer_sheet("sheet11.jpg")
    print(f"Final Score: {results['score']}/{results['total']}")