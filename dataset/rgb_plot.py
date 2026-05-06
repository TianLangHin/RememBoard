import cv2
import matplotlib.pyplot as plt
import numpy as np
import os

def image_histograms(path, figure_name, title):
    plt.figure()
    colours = []
    for i, (code, colour) in enumerate(zip('bgr', ['Blue', 'Green', 'Red'])):
        hist = np.zeros((256, 1))
        image_list = os.listdir(path)
        for image_name in image_list:
            img = cv2.imread(os.path.join(path, image_name))
            hist += cv2.calcHist(img, [i], None, [256], [0, 256])
        hist /= len(image_list)
        colours.append(hist)
        plt.plot(hist, color=code, label=colour)
        print(figure_name, colour)
    plt.legend()
    plt.xlim([0, 256])
    plt.xlabel('Pixel value')
    plt.ylabel('Average occurrences')
    plt.title(title)
    plt.savefig(figure_name)

if __name__ == '__main__':
    image_histograms(
        os.path.join(os.getcwd(), '..', '..', 'ModelTesting', 'data-wooden-wc2021'),
        'rgb-plot-wooden.png',
        'RGB Intensity Plots (Wooden Board WC 2021)')
    image_histograms(
        os.path.join(os.getcwd(), '..', '..', 'ModelTesting', 'data-handheld-wc2021'),
        'rgb-plot-handheld.png',
        'RGB Intensity Plots (Handheld Board WC 2021)')
    image_histograms(
        os.path.join(os.getcwd(), '..', '..', 'ModelTesting', 'data-wooden-wc1987'),
        'rgb-plot-wooden-unseen.png',
        'RGB Intensity Plots (Wooden Board, Unseen WC 1987)')
    image_histograms(
        os.path.join(os.getcwd(), '..', '..', 'ModelTesting', 'data-handheld-wc1987'),
        'rgb-plot-handheld-unseen.png',
        'RGB Intensity Plots (Handheld Board, Unseen WC 1987)')
