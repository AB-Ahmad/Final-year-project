import cv2
import numpy as np
from sklearn.cluster import KMeans



def load_yolo_labels(label_path, img_width, img_height):
    bubbles = []
    with open(label_path, "r") as file:
        for line in file:
            cls, x_c, y_c, w, h = map(float, line.strip().split())
            x = x_c * img_width
            y = y_c * img_height
            w = w * img_width
            h = h * img_height
            bubbles.append([x, y, w, h])
    return bubbles


def assign_question_option_mapping(bubbles, num_questions=30, num_options=5, image=None):
    bubbles = np.array(bubbles)
    half = num_questions // 2
    options = [chr(ord('a') + i) for i in range(num_options)]
    x_median = np.median(bubbles[:, 0])

    left_zone = bubbles[bubbles[:, 0] <= x_median]
    right_zone = bubbles[bubbles[:, 0] > x_median]

    def process_zone(zone_bubbles, question_start):
        y_centers = zone_bubbles[:, 1].reshape(-1, 1)
        kmeans = KMeans(n_clusters=half, n_init='auto', random_state=0)
        labels = kmeans.fit_predict(y_centers)

        row_dict = {i: [] for i in range(half)}
        for i, label in enumerate(labels):
            row_dict[label].append(zone_bubbles[i])
        sorted_rows = sorted(row_dict.items(), key=lambda x: np.mean([b[1] for b in x[1]]))

        mapping = {}
        for i, (_, row_bubbles) in enumerate(sorted_rows):
            q_num = question_start + i
            row_bubbles_sorted = sorted(row_bubbles, key=lambda b: b[0])
            for j, bubble in enumerate(row_bubbles_sorted[:num_options]):
                key = f"q{q_num}_{options[j]}"
                mapping[key] = bubble.tolist()
        return mapping

    left_mapping = process_zone(left_zone, question_start=1)
    right_mapping = process_zone(right_zone, question_start=half + 1)
    full_mapping = {**left_mapping, **right_mapping}

    if image is not None:
        visualize_bubbles(image, full_mapping)

    return full_mapping

def visualize_bubbles(image, mapping_dict, output_path="mapped_output.jpg"):
    font = cv2.FONT_HERSHEY_SIMPLEX
    font_scale = 0.4
    thickness = 1

    for label, box in mapping_dict.items():
        x, y, w, h = box
        top_left = (int(x - w / 2), int(y - h / 2))
        bottom_right = (int(x + w / 2), int(y + h / 2))
        cv2.rectangle(image, top_left, bottom_right, (0, 255, 0), 1)
        cv2.putText(image, label, (top_left[0], top_left[1] - 3), font, font_scale, (0, 0, 255), thickness)

    cv2.imwrite(output_path, image)
    print(f"✅ Saved labeled image to {output_path}")

if __name__ == "__main__":
    image_path = "sheet08.jpg"
    label_path = "C:/Users/Ahmad Bala/runs/detect/predict12/labels/sheet08_jpg.rf.422227d46a4e2e67325f08dea3662294.txt"


    image = cv2.imread(image_path)
    h, w = image.shape[:2]

    bubbles = load_yolo_labels(label_path, w, h)
    mapping = assign_question_option_mapping(bubbles, num_questions=30, num_options=5, image=image)




