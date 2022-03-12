# coding=utf-8
import logging
import operator
import sys
from ctypes import *
import pyautogui
import time
import random
import win32con
import win32gui
import cv2
import util
import cnocr

# root
logger = logging.getLogger(__name__)
logger.setLevel(level=logging.DEBUG)
formatter = logging.Formatter('%(asctime)s - %(levelname)s -  %(filename)s - %(lineno)d - %(message)s')
formatter2 = logging.Formatter('%(levelname)s - %(message)s')
logger.propagate = False
ai_mode = False

# StreamHandler
console = logging.StreamHandler(sys.stdout)
console.setLevel(level=logging.INFO)
console.setFormatter(formatter2)
logger.addHandler(console)

# FileHandler
file = logging.FileHandler("log.log", encoding='utf-8')
file.setLevel(level=logging.DEBUG)
file.setFormatter(formatter)
logger.addHandler(file)

'''
钓鱼辅助工具
三种竿钓鱼思路
浮子：通过浮标是否完全下沉和收杆时是否有鱼力条判断上鱼
路亚：抛竿收竿/左右拖竿，通过是否有鱼力条判断上鱼
海竿：按R，通过右下角是否弹出红色提示判断上鱼
'''

# 经测试，2k显示器的屏幕大小是2560*1440
# Russian Fishing4的窗口类名为 UnityWndClass， 窗口标题为Russian Fishing 4

# 各项参数
wnd_classname = 'UnityWndClass'
wnd_title = 'Russian Fishing 4'
color_type = ['red', 'green', 'blue']
rod_type = ['hand_rod', 'lure_rod', 'surf_rod']
rod_is_casting = False  # 竿是否抛出去了
fish_is_biting = False  # 鱼是否咬钩
line_is_cut = False  # 线是否断了
fish_count = 0  # 钓鱼计数
cast_count = 0  # 抛竿计数

save_path = 'E:/new/'
ocr = cnocr.CnOcr()

# 各判定点相对位置 基于1280*768的左下角坐标
window_size1 = [1296, 807]  # 窗口大小
window_size2 = [1298, 815]  # 窗口大小
default_pos = [311, 922]
fish_strip_level = [[635, -35], [515, -35], [450, -35]]  # 鱼力条的三个等级
fish_strip_mid = [650, -35]  # 鱼力条中点
fish_line_circle = [780, -70]  # 鱼线剩余圈
hunger_strip = [200, -132]  # 饥饿条
fish_info = [[615, -260], [615, -160], [680, -260], [680, -160]]  # 获得鱼的界面
fish_info_rect = [[450, -780], [850, -650]]  # 获得鱼的界面
notification = [940, -90]  # 右下通知的白色区域
notification2 = [960, -100]  # 右下通知的颜色区域
text = [458, -56]  # 提示”渔具准备好，可以抛掷一下“中”可“字的位置，精准度要求极高

float_rect = [[564, -260], [735, -90]]  # 手竿的浮漂框
text_rect = [[380, -70], [540, -50]]  # 提示文字框
strip_rect = [[380, -40], [915, -30]]  # 鱼力条提示框
quit_rect = [[[1070, -310], [1170, -200]], [[460, -320], [620, -290]], [[550, -140], [740, -120]]]  # 退出的判定点位

# 各种颜色
color_fish = [200, 214, 63]  # 有鱼的鱼力条，准确值，不受光线影响
color_fish_big = [200, 188, 0]  # 第一档大小的鱼，大于该值的第一个索引值
color_fish_line = [140, 140, 140]  # 鱼线状态，受光线影响，小于该值说明线快空了，非纺线钓鱼时会误判  [255,255,255]
color_hunger_empty = [206, 56, 21]  # 体力耗尽，不准确值，受光线影响 [144, 39, 15]
color_hunger_half = [229, 188, 0]  # 体力半满，不准确值，受光线影响 [223,183,0] [160, 132, 0]
color_hunger_full = [183, 199, 56]  # 体力充足，不准确值 [179,195,55] [176, 191, 54] [128,139,39] [167, 181, 51] 经判断，受早晚光线影响

color_info = [64, 64, 64]
color_info_focus = [102, 102, 102]
color_white = [255, 255, 255]  # 白色
color_white_lite = [140, 140, 140]  # 白色

color_red = [195, 60, 40]  # 红色提示
color_light_red = [185, 60, 80]  # 浅红色提示

''' 
工具类函数
'''


# Return True if given window is a real Windows application window.
def is_real_window(hwnd):
    if not win32gui.IsWindowVisible(hwnd):
        return False
    if win32gui.GetParent(hwnd) != 0:
        return False
    has_no_owner = win32gui.GetWindow(hwnd, win32con.GW_OWNER) == 0
    l_ex_style = win32gui.GetWindowLong(hwnd, win32con.GWL_EXSTYLE)
    if (((l_ex_style & win32con.WS_EX_TOOLWINDOW) == 0 and has_no_owner)
            or ((l_ex_style & win32con.WS_EX_APPWINDOW != 0) and not has_no_owner)):
        if win32gui.GetWindowText(hwnd):
            return True
    return False


# Return a list of array [x1, y1, x2, y2] for window rect.
def get_game_window(flag=True):
    # param1:需要传入窗口的类名
    # param2:需要传入窗口的标题
    hwnd = win32gui.FindWindow(wnd_classname, wnd_title)
    if is_real_window(hwnd):
        wnd_rect = win32gui.GetWindowRect(hwnd)  # [x1, y1, x2, y2]
        wnd_size = get_window_size(wnd_rect)  # [width, height]

        if wnd_size != window_size1 and wnd_size != window_size2:
            print("当前窗口大小：" + str(wnd_size[0]) + "*" + wnd_size[1])
            return False
        # print("窗口尺寸:", [wnd_rect[2]-wnd_rect[0], wnd_rect[3]-wnd_rect[1]])
        # print("窗口左下角坐标：", [wnd_rect[0], wnd_rect[3]])
        return [wnd_rect[0], wnd_rect[3]] if flag else wnd_rect
    return None


# 获取坐标点的颜色
def get_color(x, y):
    gdi32 = windll.gdi32
    user32 = windll.user32
    hdc = user32.GetDC(None)  # 获取颜色值
    pixel = gdi32.GetPixel(hdc, x, y)  # 提取RGB值q
    r = pixel & 0x0000ff
    g = (pixel & 0x00ff00) >> 8
    b = pixel >> 16
    return [r, g, b]


# 获取窗口大小
def get_window_size(wnd_rect):
    return [wnd_rect[2] - wnd_rect[0], wnd_rect[3] - wnd_rect[1]]


# 判断color1是否比color2浅（rgb值小），浅时返回True
def darker_than(color1, color2):
    if color1[0] < color2[0] and color1[1] < color2[1] and color1[2] < color2[2]:
        return True
    return False


# 通过相对坐标获得绝对坐标值
def get_pos(pos_zero, relative_pos):
    return pos_zero[0] + relative_pos[0], pos_zero[1] + relative_pos[1]


# 通过相对坐标获得矩形的绝对坐标
def get_rect_pos(pos_zero, relative_pos_rect):
    return [*get_pos(relative_pos_rect[0], pos_zero), *get_pos(relative_pos_rect[1], pos_zero)]


# 获取通知颜色与类型
def get_notification_type(rgb):
    max_index, max_number = max(enumerate(rgb), key=operator.itemgetter(1))
    color = color_type[max_index]
    return color


# 获取收鱼界面鱼的信息
def get_fish_info_text(im):
    text_list = ocr.ocr(util.text_filter(im))
    if len(text_list) < 2:
        print(text_list)
        return "识别信息有误"
    if text_list[0][0] == '风' or text_list[0][0] == 'R':
        text_list[0][0] = '√'
    fish_name = ''.join(text_list[0])
    fish_text = ''.join(text_list[1])
    return fish_name+","+fish_text


# 获取退出相关的坐标
def get_quit_pos(pos_base):
    pos1 = [random.uniform(quit_rect[0][0][0], quit_rect[0][1][0]),
            random.uniform(quit_rect[0][0][1], quit_rect[0][1][1])]
    pos2 = [random.uniform(quit_rect[1][0][0], quit_rect[1][1][0]),
            random.uniform(quit_rect[1][0][1], quit_rect[1][1][1])]
    pos3 = [random.uniform(quit_rect[2][0][0], quit_rect[2][1][0]),
            random.uniform(quit_rect[2][0][1], quit_rect[2][1][1])]
    return [*get_pos(pos_base, pos1)], [*get_pos(pos_base, pos2)], [*get_pos(pos_base, pos3)]


'''
操作类函数
'''


# 抛竿
def cast_rod(shift=True):
    global cast_count
    if shift:
        pyautogui.keyDown('shift')
    pyautogui.mouseDown()
    time.sleep(random.uniform(0, 1))
    pyautogui.mouseUp()
    if shift:
        pyautogui.keyUp('shift')
    time.sleep(random.uniform(2, 3))
    cast_count += 1
    logger.info("第" + str(cast_count) + "次抛竿完成")


# 路亚收竿
def lure_rod_pull(pos_base):
    global rod_is_casting, fish_is_biting
    pyautogui.mouseDown()
    logger.info("收线中")
    while True:
        time.sleep(2)
        if check_fish(pos_base):
            fish_is_biting = True
            logger.info("鱼上钩了")
            break
        if check_line_finished(pos_base):
            # logger.info("线收到底了")
            rod_is_casting = False
            break

    return


# 海竿收竿循环
def surf_rod_loop(pos_base):
    global fish_is_biting
    logger.info("等鱼中")
    while True:
        time.sleep(5)
        pyautogui.keyDown('r')
        pyautogui.keyUp('r')
        color = check_notification(pos_base)
        if color == 'red':
            fish_is_biting = True
            logger.info("鱼上钩了")
            break
    return


# 路亚拖竿循环
def lure_rod_loop():
    # 抛竿，收杆到贴近水面，左右拖动鱼竿
    return 0


# 手竿收竿循环
def hand_rod_loop():
    return 0


# 调摩擦轮
def change_friction(num):
    degree = 10 if num > 0 else -10
    num = abs(num)
    while num > 0:
        # logger.info("加摩擦轮" if degree > 0 else "减摩擦轮")
        pyautogui.scroll(degree)
        num -= 1


# 收鱼
def pull_fish(pos_base):
    friction = 22
    fct_cur = friction
    fct_max = 29
    fct_min = 10
    count = 0
    warning = 0
    global rod_is_casting, fish_is_biting, fish_count, line_is_cut
    pyautogui.mouseDown(button='left')
    pyautogui.keyDown('shift')
    pyautogui.keyDown('o')
    logger.info("跟鱼拉扯中")
    while True:
        # 大鱼松摩擦，小鱼加摩擦
        big_flag = check_big_fish(pos_base)
        if big_flag != 0:
            big_flag = min(max(fct_min, fct_cur+big_flag), fct_max) - fct_cur
            fct_cur = fct_cur + big_flag
            change_friction(big_flag)
        time.sleep(1)
        # 线收到底
        if check_line_finished(pos_base):
            logger.info("鱼跑了")
            break
        # 进入收获鱼的界面
        if check_fish_info(pos_base):
            fish_count += 1
            # 收鱼
            init_key()
            im = get_screen_shot(get_rect_pos(pos_base, fish_info_rect))
            save_img(im, 'fish_name')
            logger.info(get_fish_info_text(im) + "。累积收获" + str(fish_count) + "条鱼")
            confirm_fish()
            # if fish_count == 100:
            #     quick_quit()
            #     sys.exit()
            break
        # 判断线即将耗尽
        if check_line_exhausted(pos_base):
            print(warning)
            warning += 1
            if warning > 3:
                warning = 0
                util.beep(2)
                logger.info("线快用完了")
                if ai_mode:
                    init_key()
                    quick_quit(pos_base)
        # 判断拉线的过程中线断了
        if count > 2 and check_notification(pos_base) == 'red':
            logger.info("线断了")
            line_is_cut = True
            break
        # 要是鱼太小没识别到，等到了第50秒的时候自动提竿(路亚)
        if count > 50:
            pyautogui.keyDown('shift')
        count += 1
    # 恢复摩擦轮
    change_friction(friction-fct_cur)
    rod_is_casting = False
    fish_is_biting = False
    init_key()


# 确认鱼
def confirm_fish():
    pyautogui.press('space')


# 键位初始化
def init_key():
    pyautogui.mouseUp()
    pyautogui.keyUp('shift')
    pyautogui.keyUp('o')


# 战略性退出 pos_base 原点坐标
def quick_quit(pos_base=None):
    if pos_base is None:
        pos_base = default_pos
    pos_quit, pos_quit_confirm, pos_reenter = get_quit_pos(pos_base)
    pyautogui.press('esc')
    time.sleep(0.5)
    pyautogui.keyDown('shift')
    pyautogui.moveTo(pos_quit)
    pyautogui.click()
    pyautogui.keyUp('shift')
    pyautogui.moveTo(pos_quit_confirm)
    pyautogui.click()
    time.sleep(random.uniform(1, 3))
    pyautogui.moveTo(pos_reenter)
    pyautogui.click()
    time.sleep(10)
    # 判断是否进入成功
    logger.info("退出并重启成功")
    exit()


# 获取截图某区域的截屏
def get_screen_shot(rect):
    im = pyautogui.screenshot()
    im = im.crop(rect)
    return util.pil2cv(im)


# 截图存档
def save_shot(pos_base, shot_rect):
    float_pos = get_rect_pos(pos_base, shot_rect)
    im = get_screen_shot(float_pos)
    save_img(im)


# 保存图片
def save_img(im, path=''):
    filename = save_path + path + '/' + time.strftime("%Y-%m-%d %H-%M-%S", time.localtime(time.time())) + ".jpg"
    logger.debug("截图已保存到 " + filename)
    cv2.imwrite(filename, im)


'''
判断类函数
'''


# 鱼上钩
def check_fish(pos_base):
    fish_color = get_color(*get_pos(pos_base, fish_strip_level[0]))
    fish_color_mid = get_color(*get_pos(pos_base, fish_strip_mid))
    if fish_color[0] >= color_fish[0] and fish_color == fish_color_mid:
        return True
    return False


# 判断鱼的大小
def check_big_fish(pos_base):
    fish_color1 = get_color(*get_pos(pos_base, fish_strip_level[1]))
    fish_color2 = get_color(*get_pos(pos_base, fish_strip_level[2]))
    fish_color_mid = get_color(*get_pos(pos_base, fish_strip_mid))
    if fish_color2[0] >= color_fish_big[0] and fish_color2 == fish_color_mid:
        logger.info("鱼线接近临界值")
        util.beep(1)
        return -2
    if fish_color1[0] >= color_fish_big[0] and fish_color1 == fish_color_mid:
        logger.info("是条大鱼")
        util.beep()
        return 0
    return 1


# 判断线收到底
def check_line_finished(pos_base):
    pil_img = get_screen_shot(get_rect_pos(pos_base, text_rect))
    im = util.pil2cv(pil_img)
    res = util.evaluate_by_shape(im)
    if res < 0:
        logger.info("截图与参照图尺寸不匹配")
    elif res < 0.25:
        logger.info("识别到收线完成提示，误差率为：" + str(res))
        save_img(im)
        return True
    return False


# 判断鱼线耗尽
def check_line_exhausted(pos_base):
    line_color = get_color(*get_pos(pos_base, fish_line_circle))
    res = darker_than(line_color, color_fish_line)
    return res


# 判断饥饿
def check_hunger(pos_base):
    hunger_color = get_color(*get_pos(pos_base, hunger_strip))
    if hunger_color == color_hunger_empty:
        return 1
    elif hunger_color == color_hunger_half:
        return 2
    elif hunger_color == color_hunger_full:
        return 3


# 判断海竿调收线速度通知
def check_notification(pos_base):
    notification_color = get_color(*get_pos(pos_base, notification))
    if notification_color == color_white:
        notification_type = get_notification_type(get_color(*get_pos(pos_base, notification2)))
        return notification_type
    return None


# 判断鱼收上来了
def check_fish_info(pos_base):
    for fish_info_point in fish_info:
        fish_info_color = get_color(*get_pos(pos_base, fish_info_point))
        if fish_info_color != color_info:
            return False
    return True


# 开始钓鱼
def start_fishing(rod):
    global rod_is_casting, fish_is_biting
    logger.info("钓鱼辅助工具开始运行。程序运行过程中，请勿遮挡游戏窗口，也不要修改窗口分辨率。")
    logger.info("目前使用" + rod + "行为模式")
    while True:
        time.sleep(1)
        pos_zero = get_game_window()  # 获取窗口坐标
        if pos_zero is None:
            logger.info("获取游戏窗口失败,请启动游戏")
            return
        if not pos_zero:
            logger.info("请将游戏调为窗口模式，分辨率调为1280*768，否则将发生不可预知错误")
            continue
        # mouse_position_test(pos_zero)

        # 甩杆
        if not rod_is_casting:
            rod_is_casting = True
            cast_rod()

        # 收线
        if rod_is_casting:
            if rod == 'lure_rod':
                lure_rod_pull(pos_zero)
            if rod == 'surf_rod':
                surf_rod_loop(pos_zero)

        # 拉鱼
        if fish_is_biting:
            pull_fish(pos_zero)

        # 线断了
        if line_is_cut:
            init_key()
            break

        huger = check_hunger(pos_zero)
        if huger == 1:
            logger.info("没体力了")
            pyautogui.press('5')
        # elif huger == 2:
        #     logger.info("体力较充足")
        # elif huger == 3:
        #     logger.info("体力充足")

        init_key()


def three_surf_fishing(rod_nums=3):
    # rod_nums海杆个数，最大为3最小为2
    logger.info("多海竿切换模式，请将快捷键 1 - " + str(rod_nums) + " 设为海杆，并抛竿依次排开")
    rod_num = 1
    record = [0, 0, 0]
    while True:
        pos_zero = get_game_window()  # 获取窗口坐标
        if pos_zero is None:
            logger.info("获取游戏窗口失败,请启动游戏")
            return
        if not pos_zero:
            logger.info("请将游戏调为窗口模式，分辨率调为1280*768，否则将发生不可预知错误")
            continue
        # logger.info("切换为", rod_num, "号竿")
        pyautogui.press(str(rod_num))
        time.sleep(2)
        pyautogui.keyDown('r')
        pyautogui.keyUp('r')
        color = check_notification(pos_zero)
        if color == 'red':
            record[rod_num-1] += 1
            logger.info(str(rod_num) + "号竿第" + str(record[rod_num-1]) + "次上鱼，共上" + str(sum(record)) + "条鱼")
            pull_fish(pos_zero)
            cast_rod()
        rod_num = 1 if rod_num >= rod_nums else rod_num + 1
        time.sleep(3)


# 用于测试鼠标位置
def mouse_position_show(pos_base):
    while True:
        time.sleep(2)
        cur_pos = pyautogui.position()
        print(cur_pos[0] - pos_base[0], cur_pos[1] - pos_base[1])


# 移动坐标
def move_to(pos_zero, relative_pos):
    x, y = pos_zero[0] + relative_pos[0], pos_zero[1] + relative_pos[1]
    pyautogui.moveTo(x, y)
    time.sleep(5)
    return


# 检测相关位置是否偏移
def check():
    passed = 4
    print("请掏出海杆或者路亚，切到对话框模式，10s之后开始校验，请跟随指引完成校验")
    for i in range(10):
        print(9 - i)
        time.sleep(1)
    window = get_game_window()
    if window is None:
        print("找不到窗口，校验停止")
        exit()
    if not window:
        print("尺寸不对，请调成1280*768的窗口模式")
        passed -= 1

    print("请检查该位置是否为线圈判定圈剩余1/6的位置，不是请重新调整参数")
    move_to(window, fish_line_circle)
    if check_line_exhausted(window):
        print("线圈处判定有误")
        passed -= 1
    print("请检查该位置是否为鱼力条1/2偏左的位置，不是请重新调整参数")
    move_to(window, fish_strip_level[0])
    if check_fish(window):
        print("线圈处判定有误")
        passed -= 1
    print("请检查该位置是否为 提示\"钓具准备好，可以抛掷一下\"中\"可\"字口左下的位置，不是请重新调整参数")
    move_to(window, text)
    if not check_line_finished(window):
        print("线圈处判定有误")
        passed -= 1

    print("校验完成，共检测 4 项，通过", passed, "项")


# 实时监视某块位置
def monitor(target_rect):
    print("开始监视，在监视窗口内按ESC键停止监视，按space保存截图")
    flag = True
    while flag:
        window = get_game_window()
        if window is None:
            print("找不到窗口")
            return
        if not window:
            print("尺寸不对")
        im = get_screen_shot(get_rect_pos(window, target_rect))
        im = util.image_convert(im)
        cv2.namedWindow("image", 0)
        # cv2.resizeWindow("image", target_rect[1][0]-target_rect[0][0], text_rect[1][1]-target_rect[0][1])
        # cv2.moveWindow("image", 1100, 520)
        cv2.imshow('image', im)
        key = cv2.waitKey(1)
        if key != -1:
            print(key)
        if key == 32:
            save_img(im)
            print("截图已保存至", save_path)
        flag = key != 27
        time.sleep(1)


if __name__ == '__main__':
    logger.debug("-"*60)
    pyautogui.FAILSAFE = False
    pyautogui.PAUSE = 0.5
    rod_type = ['hand_rod', 'lure_rod', 'surf_rod']

    time.sleep(1)
    pyautogui.hotkey('alt', 'tab')
    auto = pyautogui.confirm(text='选择AI模式', title='AI选择', buttons=['只提醒', '危险自动退出'])
    if auto == '危险自动退出':
        ai_mode = True
    module = pyautogui.confirm(text='选择要执行的模式', title='模式选择', buttons=['路亚', '海竿', '三海竿'])
    if module == '路亚':
        my_rod = rod_type[1]
        start_fishing(my_rod)
    elif module == '海竿':
        my_rod = rod_type[0]
        start_fishing(my_rod)
    elif module == '三海竿':
        three_surf_fishing()
    time.sleep(1)

    quick_quit()
    # my_rod = rod_type[1]
    # 正常钓鱼
    #

    # 三海竿钓鱼
    # three_surf_fishing()
    # 在该段代码后测试各函数的功能
    win = get_game_window()
    if win is None:
        logger.info("找不到窗口")
        exit()
    if not win:
        logger.info("尺寸不对")

    # 点位检查
    # check()

    # 实时监测画面
    # monitor(float_rect)
    # while True:
    #     save_img(win, text_rect)
    #     time.sleep(1)

    # 打印鼠标所在相对游戏窗口左下角的坐标
    # mouse_position_show(win)

    # 刷制作脚本
    # while True:
    #     pyautogui.moveTo(*get_pos(win, [540, -100]))
    #     pyautogui.click()
    #     time.sleep(2)
    #     pyautogui.press('space')
    #     time.sleep(0.5)

    # 鼠标移动到某点
    # logger.info(check_line_exhausted(win))
    # logger.info(check_line_finished(win))
    # x1, y1 = get_pos(win, text)
    # logger.info(get_color(x1, y1))
    # pyautogui.moveTo(x1, y1)
