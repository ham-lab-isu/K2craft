import cv2
from PIL import Image, ImageTk

def update_image(label, image):
    image = cv2.cvtColor(image, cv2.COLOR_BGR2RGB)
    image = Image.fromarray(image)
    image = ImageTk.PhotoImage(image)
    label.config(image=image)
    label.image = image

def update_graphs(ax, canvas, line_counts, blob_counts):
    ax[0].clear()
    ax[0].plot(line_counts, 'r-')
    ax[0].set_title('Line Detection Count')
    ax[1].clear()
    ax[1].plot(blob_counts, 'b-')
    ax[1].set_title('Blob Detection Count')
    canvas.draw()
    canvas.flush_events()

def resize_image(image, width, height):
    return cv2.resize(image, (width, height), interpolation=cv2.INTER_AREA)
