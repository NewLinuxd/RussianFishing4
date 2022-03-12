import os
import util
import cv2
import numpy as np


path_true = 'image/text_true/'
path_false = 'image/text_false/'
save_path = 'image/filtered/'


def image_filter(im):
    gray = cv2.cvtColor(im, cv2.COLOR_BGR2GRAY)
    im = cv2.cvtColor(im, cv2.COLOR_BGR2GRAY)
    im = cv2.adaptiveThreshold(gray, 255, cv2.ADAPTIVE_THRESH_MEAN_C, cv2.THRESH_BINARY_INV, 9, -5)
    # im = cv2.adaptiveThreshold(gray, 255, cv2.ADAPTIVE_THRESH_GAUSSIAN_C, cv2.THRESH_BINARY_INV, 25, 10)
    # ret, im = cv2.threshold(gray, 127, 255, cv2.THRESH_BINARY)
    return im


def evaluate_by_color(im):
    point_num = len(im) * len(im[0])
    white_point = 0
    for line in im:
        for point in line:
            if point > 127:
                white_point += 1
    return white_point / point_num


# 生成处理后的图片
def transfer_image(path):
    file_lists = os.listdir(path)  # 列出文件夹下所有的目录与文件
    evaluation_list = []
    for img_name in file_lists:
        img_path = os.path.join(path, img_name)
        im = cv2.imread(img_path)
        filtered_img = image_filter(im)
        evaluation = evaluate_by_color(filtered_img)
        evaluation_list.append(evaluation)
        cv2.imwrite(save_path+img_name.split('.')[0]+'.png', filtered_img)
    return evaluation_list


# def onaptivethreshold(x):
#     value = cv2.getTrackbarPos("value", "Threshold")
#     shift = cv2.getTrackbarPos("shift", "Threshold")
#     if value < 3:
#         value = 3
#     if value % 2 == 0:
#         value = value + 1
#     args = cv2.adaptiveThreshold(img, 255, cv2.ADAPTIVE_THRESH_MEAN_C, cv2.THRESH_BINARY_INV, value, shift-10)
#     gaus = cv2.adaptiveThreshold(img, 255, cv2.ADAPTIVE_THRESH_GAUSSIAN_C, cv2.THRESH_BINARY_INV, value, shift-10)
#     cv2.imshow("Args", args)
#     cv2.imshow("Gaus", gaus)


def evaluate_by_shape(im1, im2):
    if im1.shape != im2.shape:
        return -1
    sq_diff = (im1 - im2) ** 2
    return sq_diff.sum() / (im1.shape[0] * im1.shape[1])


if __name__ == '__main__':
    # set_false = transfer_image(path_false)
    # set_true = transfer_image(path_true)

    # util.paint([np.full(len(set_true), 1.0), np.array(set_true)], [np.full(len(set_false), 0.0), np.array(set_false)])
    #
    # img = cv2.cvtColor(cv2.imread(save_path+'true-41.png'), cv2.COLOR_RGB2GRAY)
    img2 = cv2.cvtColor(cv2.imread('image/sample.png'), cv2.COLOR_RGB2GRAY)

    img = cv2.imread('E:/new/2022-03-08 19-10-34.jpg')
    print(util.evaluate_by_shape(img))
    # file_lists = os.listdir(save_path)
    # for img_name in file_lists:
    #     img = cv2.cvtColor(cv2.imread(save_path+img_name), cv2.COLOR_RGB2GRAY)
    #     print(img_name.split('.')[0], evaluate_by_shape(img, img2))

    # cv2.namedWindow("Threshold", cv2.WINDOW_NORMAL)
    # cv2.createTrackbar("value", "Threshold", 0, 25, onaptivethreshold)
    # cv2.createTrackbar("shift", "Threshold", 0, 35, onaptivethreshold)
    #
    # cv2.imshow("Threshold", img)
    # cv2.waitKey(0)

