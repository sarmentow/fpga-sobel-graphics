import cv2
import numpy as np
import pyvirtualcam

w, h = 160, 120

cap = cv2.VideoCapture(0)

with pyvirtualcam.Camera(width=w, height=h, fps=30) as cam:
    print(f'Câmera virtual ativa: {cam.device}')
    
    while True:
        ret, frame = cap.read()
        if not ret: break

        resized = cv2.resize(frame, (w, h))
        
        gray_3bit = cv2.cvtColor(resized, cv2.COLOR_BGR2GRAY) & 0xF0
        
        gx = cv2.Sobel(gray_3bit, cv2.CV_64F, 1, 0, ksize=3)
        gy = cv2.Sobel(gray_3bit, cv2.CV_64F, 0, 1, ksize=3)
        sobel = cv2.convertScaleAbs(cv2.magnitude(gx, gy))

        frame_out = cv2.cvtColor(sobel, cv2.COLOR_GRAY2RGB)
        
        cam.send(frame_out)
        cam.sleep_until_next_frame()