# K230矩形检测系统 - 简化示例

"""
这是一个简化版本的K230矩形检测示例
适合学习和快速测试使用
"""

import time
import math
from media.sensor import *
from media.display import *
from media.media import *
from machine import UART, FPIOA, TOUCH

# 简化配置
LASER_X, LASER_Y = 240, 160
mode = "1"

def simple_center_calc(corners):
    """简单的中心点计算"""
    if len(corners) == 4:
        cx = sum(pt[0] for pt in corners) / 4
        cy = sum(pt[1] for pt in corners) / 4
        return (int(cx), int(cy))
    return None

def simple_error_handling(cx, cy, lx, ly, uart):
    """简化的误差处理"""
    error_x = cx - lx
    error_y = cy - ly

    # 简单格式化
    data = f"@{error_x:+05.0f}{error_y:+05.0f}!"
    uart.write(data)
    print(f"发送: {data}")

# 主程序
try:
    print("启动简化检测程序...")

    # 初始化硬件
    sensor = Sensor(width=480, height=320)
    sensor.reset()
    sensor.set_framesize(width=480, height=320)
    sensor.set_pixformat(Sensor.RGB565)

    Display.init(Display.ST7701, width=800, height=480, to_ide=True)
    MediaManager.init()
    sensor.run()

    # 串口配置
    fpioa = FPIOA()
    fpioa.set_function(11, FPIOA.UART2_TXD)
    fpioa.set_function(12, FPIOA.UART2_RXD)
    uart = UART(UART.UART2, 115200)

    frame_count = 0

    while True:
        frame_count += 1
        img = sensor.snapshot(chn=CAM_CHN_ID_0)

        # 每10帧处理一次(提高性能)
        if frame_count % 10 == 0:
            # 这里可以添加简化的检测逻辑
            # 示例：固定中心点测试
            test_center = (240, 160)
            simple_error_handling(test_center[0], test_center[1],
                                 LASER_X, LASER_Y, uart)

        # 绘制激光点和中心
        img.draw_circle(int(LASER_X), int(LASER_Y), 5, (0,0,255), 2)
        img.draw_cross(240, 160, (255,0,0), 2, 10)

        # 显示信息
        img.draw_string_advanced(10, 10, 15, f"Frame: {frame_count}", (255,255,255))
        img.draw_string_advanced(10, 30, 15, f"Mode: {mode}", (255,255,255))

        # 显示图像
        img.compressed_for_ide()
        Display.show_image(img, x=160, y=80)

except KeyboardInterrupt:
    print("程序停止")
except Exception as e:
    print(f"错误: {e}")
finally:
    if isinstance(sensor, Sensor):
        sensor.stop()
    Display.deinit()
    MediaManager.deinit()
    print("清理完成")