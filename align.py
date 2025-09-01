import matplotlib.pyplot as plt
import cv2

# Load image
img_path = "debug_outputs/aligned_sheet.jpg"   # change this to your sheet image
img = cv2.imread(img_path)
img_rgb = cv2.cvtColor(img, cv2.COLOR_BGR2RGB)

points = []

def onclick(event):
    if event.xdata is not None and event.ydata is not None:
        x, y = int(event.xdata), int(event.ydata)
        points.append((x, y))
        print(f"Clicked: ({x}, {y})")

        # If 2 points clicked → compute bounding box
        if len(points) == 2:
            (x1, y1), (x2, y2) = points
            x = min(x1, x2)
            y = min(y1, y2)
            w = abs(x2 - x1)
            h = abs(y2 - y1)
            print(f"\n✅ Bounding Box: ({x}, {y}, {w}, {h})\n")

            # Draw rectangle on the image
            rect = plt.Rectangle((x, y), w, h, fill=False, color="red", linewidth=2)
            plt.gca().add_patch(rect)
            plt.draw()

            # Reset points for next box
            points.clear()

fig, ax = plt.subplots()
ax.imshow(img_rgb)
cid = fig.canvas.mpl_connect('button_press_event', onclick)
plt.show()
