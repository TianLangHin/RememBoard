import cv2
import numpy as np
import os

# This is the IP webcam address through which the photos of the chessboard are taken.
ip_webcam = input('Webcam IP: ')

# This will be the folder name that all the images are collected into.
category = input('Image folder: ')

if not os.path.exists(os.path.join(os.getcwd(), category)):
    os.mkdir(category)

ply_number = 1
while True:
    key = input(f'Move {ply_number} image: ')
    cap = cv2.VideoCapture(f'http://{ip_webcam}/video')
    ret, frame = cap.read()
    if not ret:
        print('End')
        break
    if key == 'quit':
        break
    cv2.imwrite(os.path.join(os.getcwd(), category, f'{ply_number:0>4}.png'), frame)
    ply_number += 1
