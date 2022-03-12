import numpy as np
import PIL.Image as Image
import winsound
import cv2

sample_file = 'image/sample.png'


def evaluate_by_shape(im1, im2=None):
    im1 = image_filter(im1)
    if not im2:
        im2 = cv2.cvtColor(cv2.imread(sample_file), cv2.COLOR_RGB2GRAY)
    if im1.shape != im2.shape:

        return -1
    sq_diff = (im1 - im2)
    for i in range(im1.shape[0]):
        for j in range(im1.shape[1]):
            sq_diff[i][j] = 1 if sq_diff[i][j] > 0 else 0
    sq_diff = sq_diff ** 2
    return sq_diff.sum() / (im1.shape[0] * im1.shape[1])


'''cv2图像转PIL
:param im: cv2图像，numpy.ndarray
:return: PIL图像，PIL.Image
'''


# noinspection PyBroadException
def cv2pil(im):
    try:
        return Image.fromarray(cv2.cvtColor(im, cv2.COLOR_BGR2RGB))
    except Exception as e:
        return Image.fromarray(cv2.cvtColor(im, cv2.COLOR_BGRA2RGBA))


'''PIL图像转cv2
:param im: PIL图像，PIL.Image
:return: cv2图像，numpy.ndarray
'''


# noinspection PyBroadException
def pil2cv(im):
    # try:
    return cv2.cvtColor(np.array(im), cv2.COLOR_RGB2BGR)
    # except Exception as e:
    #     return cv2.cvtColor(np.array(im), cv2.COLOR_RGB2BGR)


def image_convert(im):
    gray = cv2.cvtColor(im, cv2.COLOR_BGR2GRAY)
    im = cv2.cvtColor(im, cv2.COLOR_BGR2GRAY)
    # im = cv2.adaptiveThreshold(gray, 255, cv2.ADAPTIVE_THRESH_MEAN_C, cv2.THRESH_BINARY, 25, 10)
    # ret, im = cv2.threshold(gray, 127, 255, cv2.THRESH_BINARY)
    return im


def image_filter(im):
    gray = cv2.cvtColor(im, cv2.COLOR_BGR2GRAY)
    im = cv2.cvtColor(im, cv2.COLOR_BGR2GRAY)
    im = cv2.adaptiveThreshold(gray, 255, cv2.ADAPTIVE_THRESH_MEAN_C, cv2.THRESH_BINARY_INV, 9, -5)
    # im = cv2.adaptiveThreshold(gray, 255, cv2.ADAPTIVE_THRESH_GAUSSIAN_C, cv2.THRESH_BINARY_INV, 13, -15)
    # ret, im = cv2.threshold(gray, 127, 255, cv2.THRESH_BINARY)
    return im


def text_filter(im):
    gray = cv2.cvtColor(im, cv2.COLOR_BGR2GRAY)
    ret, im = cv2.threshold(gray, 150, 255, cv2.THRESH_BINARY_INV, im)
    return im


# 蜂鸣器提醒
def beep(level=0):
    if level == 0:
        winsound.Beep(2000, 500)
    while level > 0:
        winsound.Beep(2000, 500)
        winsound.Beep(1600, 500)
        level -= 1


if __name__ == '__main__':
    rect = [811, 142, 1111, 272]
    import main as gui
    import time

    # img = cv2.imread('E:/new/fish_name/2022-03-10 22-46-54.jpg')
    # gui.get_fish_info_text(img)

    # gui.save_img(img, 'fish_name')
    # img2 = cv2.imread('E:/new/2022-03-09 16-54-34.jpg')
    # img = text_filter(img)
    # cv2.imshow("1", img)
    # cv2.waitKey(0)
    # print(gui.get_fish_info_text(img))
    # print(gui.get_fish_info_text(img2))

    # save_path = 'E:/new/fish_name/'
    # file_lists = os.listdir(save_path)
    # for img_name in file_lists:
    #     print(img_name)
    #     print(gui.get_fish_info_text(cv2.imread(save_path+img_name)))

