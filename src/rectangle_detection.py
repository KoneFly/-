import time
import os
import math
from media.sensor import *
from media.display import *
from media.media import *
from time import ticks_ms
from machine import UART
from machine import Pin
from machine import FPIOA
from machine import TOUCH
import struct
import cv_lite

sensor = None
tp = TOUCH(0)
fpioa = FPIOA()
mode="1"
laser_x, laser_y = 260,166.5
LCD_WIDTH, LCD_HEIGHT = 800, 480         # 物理分辨率
DISPLAY_WIDTH, DISPLAY_HEIGHT = 480, 320  # 显示分辨率

# 模式切换相关变量
touch_start_time = 0
long_press_threshold = 3000  # 3秒长按切换模式



'''
'''







def err_handling(center_x, center_y, laser_x, laser_y, uart):
    # 定义死区范围，可根据实际需求调整
    dead_zone = 5  # X和Y轴共用同一死区阈值，也可分别定义dead_zone_x和dead_zone_y

    error_x = (center_x - laser_x)
    error_y = (center_y - laser_y)

    # 死区处理：当偏差绝对值小于等于死区阈值时，视为0
    if abs(error_x) <= dead_zone:
        error_x = 0
    if abs(error_y) <= dead_zone:
        error_y = 0

    print(f"与中心的偏差（经过死区处理）为：{error_x}, {error_y}")

    # 处理X轴偏差
    abs_x = abs(int(error_x * 1))  # 取绝对值并放大1倍
    formatted_x = f"{abs_x:04d}"    # 格式化为4位数，不足补零
    prefix_x = '0' if error_x >= 0 else '1'  # 正数为0，负数为1
    final_x = prefix_x + formatted_x  # 组合成5位数

    # 处理Y轴偏差
    abs_y = abs(int(error_y * 1))
    formatted_y = f"{abs_y:04d}"
    prefix_y = '0' if error_y >= 0 else '1'
    final_y = prefix_y + formatted_y

    # 通过串口发送数据
    uart.write("@")                     # 起始标志
    uart.write(f"{final_x}{final_y}")   # 发送10位数据
    uart.write("!")                     # 结束标志
    print(f"发送数据：{final_x}{final_y}")

def calculate_center(corners):
    """计算矩形中心坐标（优化版：只要有4个角点就返回中心）"""
    if len(corners) == 4:  # 确保有4个角点
        # 计算所有角点的平均值
        center_x = sum(pt[0] for pt in corners) / 4
        center_y = sum(pt[1] for pt in corners) / 4
        return (center_x, center_y)
    return None  # 不符合条件返回None

def sort_corners(corners):
    """将角点按左上→右上→右下→左下排序（便于中心计算）"""
    center = calculate_center(corners)
    # 按与中心的夹角排序
    sorted_corners = sorted(corners, key=lambda p: math.atan2(p[1]-center[1], p[0]-center[0]))
    # 调整起点为左上角（x+y最小的点）
    if len(sorted_corners) == 4:
        left_top = min(sorted_corners, key=lambda p: p[0]+p[1])
        index = sorted_corners.index(left_top)
        sorted_corners = sorted_corners[index:] + sorted_corners[:index]
    return sorted_corners





try:
    print("Starting real-time rectangle detection...")
    # 初始化计时器
    start_time = ticks_ms()
    frame_count = 0

    # 初始化硬件
    fpioa = FPIOA()
    sensor = Sensor(width=480, height=320)
    sensor.reset()
    fpioa.set_function(11, FPIOA.UART2_TXD)
    fpioa.set_function(12, FPIOA.UART2_RXD)
    uart = UART(UART.UART2, 115200)
    sensor.set_framesize(width=480, height=320)
    sensor.set_pixformat(Sensor.RGB565)
    Display.init(Display.ST7701, width=800, height=480, to_ide=True)
    MediaManager.init()
    sensor.run()
    # --------------------------- A4纸检测参数（核心适配） ---------------------------
    # A4纸宽高比约1:1.414（210mm×297mm），参数围绕此特征设计
    canny_thresh1 = 40         # 边缘检测低阈值（适应纸张边缘）
    canny_thresh2 = 120        # 边缘检测高阈值
    approx_epsilon = 0.02      # 多边形拟合精度（A4纸边缘较规则，用小值）
    area_min_ratio = 0.01       # 最小面积占比（A4纸通常是图像中较大区域）
    max_angle_cos = 1.5        # 角度余弦阈值（A4纸接近标准矩形）
    gaussian_blur_size = 5     # 高斯模糊（减少纸张表面纹理干扰）

    # A4纸筛选核心参数
    MIN_AREA = 5000/4            # 最小面积（根据640×480分辨率调整）
    MAX_AREA = 640*480*0.8     # 最大面积（不超过图像80%）
    MIN_ASPECT_RATIO = 0.6     # 1/1.414≈0.7，稍宽松容错
    MAX_ASPECT_RATIO = 1.5     # 1.414接近1.5

    image_shape = [sensor.height(), sensor.width()]  # [高, 宽] 用于cv_lite
    a4_center = None  # 存储A4纸中心坐标


    while True:
        # 更新帧计数和FPS计算
        frame_count += 1
        current_time = ticks_ms()
        os.exitpoint()
        img = sensor.snapshot(chn=CAM_CHN_ID_0)

        # ============= 模式切换检测 =============
        # 检测长按切换模式
        touch_data = tp.read()
        if touch_data[2]:  # 检测到触摸
            if touch_start_time == 0:
                touch_start_time = current_time
            elif current_time - touch_start_time >= long_press_threshold:
                # 长按3秒，切换模式
                mode = "2" if mode == "1" else "1"
                print(f"模式切换为: {mode}")
                touch_start_time = 0  # 重置计时
        else:
            touch_start_time = 0  # 释放触摸，重置计时



        if mode=="1":
            gray_img = img.to_grayscale()
            img_np = gray_img.to_numpy_ref()
            rects = cv_lite.grayscale_find_rectangles_with_corners(
                image_shape,
                img_np,
                canny_thresh1,
                canny_thresh2,
                approx_epsilon,
                area_min_ratio,
                max_angle_cos,
                gaussian_blur_size
            )


            # 2. 筛选符合A4特征的矩形
            best_a4_rect = None
            best_corners = None
            max_area = 0  # 优先选择面积最大的矩形（A4纸通常是最大的矩形）

            for rect in rects:
                # rect格式: [x, y, w, h, c1.x, c1.y, c2.x, c2.y, c3.x, c3.y, c4.x, c4.y]
                corners = [
                    (rect[4], rect[5]),
                    (rect[6], rect[7]),
                    (rect[8], rect[9]),
                    (rect[10], rect[11])
                ]

                # 计算矩形面积和宽高比
                width, height = rect[2], rect[3]
                area = width * height
                aspect_ratio = width / height if height > 0 else 0

                # 筛选符合A4纸特征的矩形
                if (MIN_AREA <= area <= MAX_AREA and
                    MIN_ASPECT_RATIO <= aspect_ratio <= MAX_ASPECT_RATIO):

                    # 绘制候选矩形（绿色）
                    img.draw_line(corners[0][0], corners[0][1], corners[1][0], corners[1][1], color=(0, 255, 0), thickness=3)
                    img.draw_line(corners[1][0], corners[1][1], corners[2][0], corners[2][1], color=(0, 255, 0), thickness=3)
                    img.draw_line(corners[2][0], corners[2][1], corners[3][0], corners[3][1], color=(0, 255, 0), thickness=3)
                    img.draw_line(corners[3][0], corners[3][1], corners[0][0], corners[0][1], color=(0, 255, 0), thickness=3)

                    # 选择面积最大的作为最佳A4矩形
                    if area > max_area:
                        max_area = area
                        best_a4_rect = rect
                        best_corners = corners
                else:
                    # 绘制不符合条件的矩形（红色，较细）
                    img.draw_line(corners[0][0], corners[0][1], corners[1][0], corners[1][1], color=(255, 0, 0), thickness=1)
                    img.draw_line(corners[1][0], corners[1][1], corners[2][0], corners[2][1], color=(255, 0, 0), thickness=1)
                    img.draw_line(corners[2][0], corners[2][1], corners[3][0], corners[3][1], color=(255, 0, 0), thickness=1)
                    img.draw_line(corners[3][0], corners[3][1], corners[0][0], corners[0][1], color=(255, 0, 0), thickness=1)

            # 处理最佳A4矩形
            if best_corners:
                # 高亮显示最佳矩形（黄色加粗）
                img.draw_line(best_corners[0][0], best_corners[0][1], best_corners[1][0], best_corners[1][1], color=(255, 255, 0), thickness=5)
                img.draw_line(best_corners[1][0], best_corners[1][1], best_corners[2][0], best_corners[2][1], color=(255, 255, 0), thickness=5)
                img.draw_line(best_corners[2][0], best_corners[2][1], best_corners[3][0], best_corners[3][1], color=(255, 255, 0), thickness=5)
                img.draw_line(best_corners[3][0], best_corners[3][1], best_corners[0][0], best_corners[0][1], color=(255, 255, 0), thickness=5)

                # 角点排序和中心计算
                sorted_corners = sort_corners(best_corners)
                a4_center = calculate_center(best_corners)
                if a4_center:
                    cx, cy = map(int, a4_center)
                    img.draw_cross(cx, cy, color=(255, 0, 0), thickness=3, size=10)
                    img.draw_circle(int(round(laser_x,)), int(round(laser_y)), 2, color=(0, 0, 255), thickness=3)
                    img.draw_line(int(round(cx)), int(round(cy)), int(round(laser_x)), int(round(laser_y)), color=(255, 255, 0), thickness=2)
                    err_handling(cx, cy, laser_x, laser_y, uart)

                    # 显示检测信息
                    img.draw_string_advanced(10, 70, 12, f"检测到A4纸 面积:{max_area:.0f}", color=(0, 255, 0))
            else:
                a4_center = None
                img.draw_string_advanced(10, 10,15, "No A4 detected", color=(255, 0, 0))
                uart.write("@")                         # 起始标志
                uart.write(f"2000020000")               # 发送10位数据
                uart.write("!")                         # 结束标志
        elif mode=="2":
            # ============= 手动校准模式 =============
            # 显示当前激光坐标
            img.draw_circle(int(round(laser_x)), int(round(laser_y)), 5, color=(0, 0, 255), thickness=3)
            img.draw_string_advanced(10, 10, 15, f"校准模式 - 激光坐标: ({laser_x:.1f}, {laser_y:.1f})", color=(255, 255, 0))
            img.draw_string_advanced(10, 30, 15, "短按设置激光位置", color=(255, 255, 255))
            img.draw_string_advanced(10, 50, 15, "长按3秒退出校准模式", color=(255, 255, 255))

            # 检查短按触摸输入（用于设置激光位置）
            if touch_data[2] and touch_start_time == 0:  # 短按检测
                touch_x, touch_y = touch_data[0], touch_data[1]
                if 0 <= touch_x <= 480 and 0 <= touch_y <= 320:  # 确保坐标在有效范围内
                    laser_x, laser_y = touch_x, touch_y
                    print(f"激光坐标已更新为: ({laser_x}, {laser_y})")

                    # 简单的触摸反馈
                    img.draw_circle(int(touch_x), int(touch_y), 10, color=(255, 0, 0), thickness=2)
                    img.draw_string_advanced(int(touch_x)+15, int(touch_y), 12, "新位置", color=(255, 0, 0))

            # 显示十字准线帮助定位
            img.draw_line(0, int(laser_y), 480, int(laser_y), color=(100, 100, 100), thickness=1)
            img.draw_line(int(laser_x), 0, int(laser_x), 320, color=(100, 100, 100), thickness=1)







        # 计算FPS
        elapsed_time = (current_time - start_time) / 1000.0  # 转换为秒
        fps = frame_count / elapsed_time if elapsed_time > 0 else 0
        img.draw_string_advanced(10, 260, 15, f"FPS: {fps:.1f}", color=(255, 255, 255))
        # 显示图像
        img.compressed_for_ide()
        img_w, img_h = img.width(), img.height()
        Display.show_image(img,
                          x=(800 - sensor.width())//2,
                          y=(480 - sensor.height())//2)




except KeyboardInterrupt as e:
    print("用户停止: ", e)
except BaseException as e:
    print(f"异常: {e}")
finally:
    if isinstance(sensor, Sensor):
        sensor.stop()
    Display.deinit()
    os.exitpoint(os.EXITPOINT_ENABLE_SLEEP)
    time.sleep_ms(100)
    MediaManager.deinit()
    #uart2.deinit()
