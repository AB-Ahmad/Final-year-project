import os
import cv2
import numpy as np

# Paths
LABEL_DIR = r"C:\Users\Ahmad Bala\runs\detect\predict2\labels"
IMAGE_DIR = r"C:\Users\Ahmad Bala\Desktop\MCQ PJ\mcq-grading.v2i.yolov8\test\images"

# Answer key
answer_key = {
    f"q{i}": opt for i, opt in zip(range(1, 31),
    ["a", "a", "c", "d", "e",  # q1 - q5
     "a", "b", "c", "d", "e",  # q6 - q10
     "a", "b", "c", "d", "e",  # q11 - q15
     "a", "b", "c", "d", "e",  # q16 - q20
     "a", "b", "c", "d", "e",  # q21 - q25
     "a", "b", "c", "d", "e"]  # q26 - q30
)}

# Get question and option from x, y
def get_question_option(x, y, img_shape):
    height, width = img_shape[:2]
    half_split = height // 2
    row_height = half_split // 15
    col_width = width // 5

    if y < half_split:
        row = y // row_height
    else:
        row = 15 + (y - half_split) // row_height

    col = x // col_width

    question = f"q{min(row + 1, 30)}"
    option = ["a", "b", "c", "d", "e"][min(col, 4)]
    return question, option

# Show bounding boxes visually
def visualize_student(image_path, label_path, student_id):
    image = cv2.imread(image_path)
    if image is None:
        print(f"⚠️ Could not read image: {image_path}")
        return

    h, w = image.shape[:2]
    selections = {}

    with open(label_path, "r") as f:
        for line in f:
            parts = line.strip().split()
            if len(parts) < 5:
                continue
            _, x_c, y_c, bw, bh = map(float, parts)
            x = int(x_c * w)
            y = int(y_c * h)
            box_w = int(bw * w)
            box_h = int(bh * h)

            q, opt = get_question_option(x, y, image.shape)
            selections.setdefault(q, []).append((opt, (x, y, box_w, box_h)))

    for q, bubbles in selections.items():
        for opt, (x, y, bw, bh) in bubbles:
            color = (128, 128, 128)  # Gray by default
            if len(bubbles) > 1:
                color = (0, 0, 255)  # Red for multiple
            elif q in answer_key:
                color = (0, 255, 0) if opt == answer_key[q] else (0, 0, 255)

            # Draw rectangle and label
            top_left = (x - bw // 2, y - bh // 2)
            bottom_right = (x + bw // 2, y + bh // 2)
            cv2.rectangle(image, top_left, bottom_right, color, 2)
            cv2.putText(image, f"{q}_{opt}", (x - 10, y - 10), cv2.FONT_HERSHEY_SIMPLEX, 0.5, color, 1)

    cv2.imshow(f"📄 {student_id}", image)
    cv2.waitKey(0)
    cv2.destroyAllWindows()

# Run visualization
if __name__ == "__main__":
    for label_file in os.listdir(LABEL_DIR):
        if not label_file.endswith(".txt"):
            continue
        student_id = label_file.replace(".txt", "")
        label_path = os.path.join(LABEL_DIR, label_file)
        image_path = os.path.join(IMAGE_DIR, student_id + ".jpg")

        if not os.path.exists(image_path):
            print(f"⚠️ Missing image for {student_id}")
            continue

        visualize_student(image_path, label_path, student_id)
