from pypylon import pylon
from utils import update_image, update_graphs, resize_image
import cv2
import numpy as np
import matplotlib.pyplot as plt
from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg

class CameraManager:
    def __init__(self, display_var):
        self.camera = None
        self.display_var = display_var
        self.line_counts = []
        self.blob_counts = []
        self.fig = None
        self.ax = None
        self.converter = None
        self.blob_detector = None

        # Initialize camera
        self.setup_camera()

    def setup_camera(self):
        self.release_camera()
        self.camera = pylon.InstantCamera(pylon.TlFactory.GetInstance().CreateFirstDevice())
        self.camera.Open()
        self.converter = pylon.ImageFormatConverter()
        self.converter.OutputPixelFormat = pylon.PixelType_BGR8packed
        self.blob_detector = self.setup_blob_detector()

    def release_camera(self):
        if self.camera is not None:
            if self.camera.IsGrabbing():
                self.camera.StopGrabbing()
            self.camera.Close()
            self.camera = None

    def setup_blob_detector(self):
        params = cv2.SimpleBlobDetector_Params()
        params.filterByArea = True
        params.minArea = 150
        params.filterByCircularity = True
        params.minCircularity = 0.1
        params.filterByConvexity = True
        params.minConvexity = 0.5
        params.filterByInertia = True
        params.minInertiaRatio = 0.01
        return cv2.SimpleBlobDetector_create(params)

    def initialize_graph(self):
        self.fig, self.ax = plt.subplots(2, 1, figsize=(5, 8))
        return self.fig, self.ax

    def create_canvas(self, fig, parent):
        canvas = FigureCanvasTkAgg(fig, master=parent)
        return canvas

    def start_video_feed(self):
        if self.camera and not self.camera.IsGrabbing():
            try:
                self.camera.StartGrabbing(pylon.GrabStrategy_LatestImages)
                self.update_camera_feed()
                print("Video feed started.")
            except Exception as e:
                print(f"Failed to start video feed: {e}")

    def stop_video_feed(self):
        if self.camera and self.camera.IsGrabbing():
            self.camera.StopGrabbing()
            print("Video feed stopped.")

    def update_camera_feed(self):
        if self.camera and self.camera.IsGrabbing():
            try:
                grabResult = self.camera.RetrieveResult(500, pylon.TimeoutHandling_ThrowException)
                if grabResult.GrabSucceeded():
                    image = self.converter.Convert(grabResult).GetArray()
                    self.process_image(image)
                grabResult.Release()
                self.camera.StartGrabbing(pylon.GrabStrategy_LatestImages)
            except Exception as e:
                print(f"Error during camera feed update: {e}")

    def process_image(self, image):
        display_image = image
        if self.display_var.get() == "lines":
            display_image, _ = self.detect_lines(image)
        elif self.display_var.get() == "blobs":
            display_image, _ = self.detect_blobs(image)
        elif self.display_var.get() == "color":
            display_image = self.color_segmentation(image)
        elif self.display_var.get() == "edges":
            display_image = self.edge_detection(image)
        elif self.display_var.get() == "contours":
            display_image = self.contour_detection(image)
        elif self.display_var.get() == "shapes":
            display_image = self.shape_detection(image)
        else:
            line_image, line_count = self.detect_lines(image)
            blob_image, blob_count = self.detect_blobs(image)
            display_image = cv2.addWeighted(line_image, 0.5, blob_image, 0.5, 0)
            self.line_counts.append(line_count)
            self.blob_counts.append(blob_count)

        display_image = resize_image(display_image, 770, 400)
        update_image(self.video_label, display_image)
        update_graphs(self.ax, self.canvas, self.line_counts, self.blob_counts)

    def detect_lines(self, image):
        gray = cv2.cvtColor(image, cv2.COLOR_BGR2GRAY)
        blurred_gray = cv2.GaussianBlur(gray, (5, 5), 0)
        edges = cv2.Canny(blurred_gray, 100, 200, apertureSize=3)
        lines = cv2.HoughLinesP(edges, 1, np.pi / 180, 50, minLineLength=50, maxLineGap=20)
        line_image = image.copy()
        if lines is not None:
            for line in lines:
                x1, y1, x2, y2 = line[0]
                cv2.line(line_image, (x1, y1), (x2, y2), (0, 255, 0), 2)
        return line_image, len(lines) if lines is not None else 0

    def detect_blobs(self, image):
        keypoints = self.blob_detector.detect(image)
        blob_image = cv2.drawKeypoints(image, keypoints, None, (0, 0, 255), cv2.DRAW_MATCHES_FLAGS_DRAW_RICH_KEYPOINTS)
        return blob_image, len(keypoints)

    def color_segmentation(self, image):
        hsv = cv2.cvtColor(image, cv2.COLOR_BGR2HSV)
        lower_bound = np.array([0, 120, 70])
        upper_bound = np.array([180, 255, 255])
        mask = cv2.inRange(hsv, lower_bound, upper_bound)
        segmented_image = cv2.bitwise_and(image, image, mask=mask)
        return segmented_image

    def edge_detection(self, image):
        gray = cv2.cvtColor(image, cv2.COLOR_BGR2GRAY)
        edges = cv2.Canny(gray, 100, 200)
        edge_image = cv2.cvtColor(edges, cv2.COLOR_GRAY2BGR)
        return edge_image

    def contour_detection(self, image):
        gray = cv2.cvtColor(image, cv2.COLOR_BGR2GRAY)
        blurred = cv2.GaussianBlur(gray, (5, 5), 0)
        edged = cv2.Canny(blurred, 50, 150)
        contours, _ = cv2.findContours(edged, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)
        contour_image = image.copy()
        cv2.drawContours(contour_image, contours, -1, (0, 255, 0), 2)
        return contour_image

    def shape_detection(self, image):
        gray = cv2.cvtColor(image, cv2.COLOR_BGR2GRAY)
        blurred = cv2.GaussianBlur(gray, (5, 5), 0)
        edged = cv2.Canny(blurred, 50, 150)
        contours, _ = cv2.findContours(edged, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)
        shape_image = image.copy()
        for contour in contours:
            approx = cv2.approxPolyDP(contour, 0.04 * cv2.arcLength(contour, True), True)
            if len(approx) == 3:
                shape = "Triangle"
            elif len(approx) == 4:
                (x, y, w, h) = cv2.boundingRect(approx)
                ar = w / float(h)
                shape = "Square" if 0.95 <= ar <= 1.05 else "Rectangle"
            elif len(approx) == 5:
                shape = "Pentagon"
            else:
                shape = "Circle"
            cv2.drawContours(shape_image, [approx], -1, (0, 255, 0), 2)
            x, y = approx[0][0]
            cv2.putText(shape_image, shape, (x, y - 10), cv2.FONT_HERSHEY_SIMPLEX, 1.0, (0, 255, 0), 2)
        return shape_image
