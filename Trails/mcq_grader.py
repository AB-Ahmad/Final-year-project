from ultralytics import YOLO
import os
import cv2

# Load model
model = YOLO("best.pt")

# Define image folder
image_dir = "mcq-grading.v2i.yolov8/test/images"

# Define answer key
answer_key = {
    "q1": "b", "q2": "c", "q3": "", "q4": "d", "q5": "e",
    "q6": "b", "q7": "a", "q8": "b", "q9": "e", "q10": "d",
    "q11": "a", "q12": "b", "q13": "d", "q14": "b", "q15": "e",
    "q16": "b", "q17": "", "q18": "c", "q19": "a", "q20": "d",
    "q21": "", "q22": "c", "q23": "b", "q24": "a", "q25": "a",
    "q26": "b", "q27": "b", "q28": "", "q29": "d", "q30": "e"
}



# Column thresholds for options A–E (X-coordinates may need adjustment!)
OPTION_COLUMNS = {
    "a": (30, 80),
    "b": (81, 130),
    "c": (131, 180),
    "d": (181, 230),
    "e": (231, 280)
}

# Y-range per question (may vary depending on your paper scan size)
def get_question_number(y, height):
    top_section = [i * height // 30 for i in range(1, 16)]
    bottom_section = [i * height // 30 + height // 2 for i in range(1, 16)]
    question_lines = top_section + bottom_section
    for i, y_threshold in enumerate(question_lines):
        if y <= y_threshold:
            return f"q{i+1}"
    return None

def get_option(x):
    for opt, (x_min, x_max) in OPTION_COLUMNS.items():
        if x_min <= x <= x_max:
            return opt
    return None

# Process each test image
for filename in os.listdir(image_dir):
    if not filename.endswith(".jpg"):
        continue
    path = os.path.join(image_dir, filename)
    image = cv2.imread(path)
    height, width = image.shape[:2]

    results = model(path)[0]
    preds = results.boxes.xyxy.cpu().numpy()  # x1, y1, x2, y2

    # Gather selections
    selections = {}
    for box in preds:
        x1, y1, x2, y2 = box[:4]
        x_center = int((x1 + x2) / 2)
        y_center = int((y1 + y2) / 2)

        question = get_question_number(y_center, height)
        option = get_option(x_center)

        if question and option:
            selections.setdefault(question, []).append(option)

    # Grade
    score = 0
    detailed = {}
    for q in answer_key:
        selected = selections.get(q, [])
        if len(selected) == 1 and selected[0] == answer_key[q]:
            score += 1
            detailed[q] = "✔"
        elif len(selected) == 0:
            detailed[q] = "○"  # Unanswered
        else:
            detailed[q] = "✘"  # Multiple or wrong

    print(f"\n🧑 Student: {filename}")
    print(f"✅ Score: {score}/30")
    print("📋 Detail:", detailed)
