# K230激光校准工具

"""
独立的激光校准工具
用于精确设定激光器位置坐标
"""

import time
from media.sensor import *
from media.display import *
from media.media import *
from machine import TOUCH

class LaserCalibrator:
    def __init__(self):
        self.laser_x = 240.0
        self.laser_y = 160.0
        self.tp = TOUCH(0)
        self.calibration_points = []

    def save_calibration(self):
        """保存校准结果到配置文件"""
        config_data = f"""# 自动生成的校准配置
# 生成时间: {time.strftime('%Y-%m-%d %H:%M:%S')}

# 激光器坐标
DEFAULT_LASER_X = {self.laser_x}
DEFAULT_LASER_Y = {self.laser_y}

# 校准点记录
CALIBRATION_POINTS = {self.calibration_points}
"""
        # 在实际应用中这里应该写入文件
        print("校准配置:")
        print(config_data)

    def run_calibration(self):
        """运行校准程序"""
        try:
            print("启动激光校准工具...")

            # 初始化硬件
            sensor = Sensor(width=480, height=320)
            sensor.reset()
            sensor.set_framesize(width=480, height=320)
            sensor.set_pixformat(Sensor.RGB565)

            Display.init(Display.ST7701, width=800, height=480, to_ide=True)
            MediaManager.init()
            sensor.run()

            calibration_step = 0
            last_touch_time = 0

            while True:
                img = sensor.snapshot(chn=CAM_CHN_ID_0)

                # 绘制当前激光位置
                img.draw_circle(int(self.laser_x), int(self.laser_y), 8, (0,0,255), 3)

                # 绘制十字准线
                img.draw_line(0, int(self.laser_y), 480, int(self.laser_y), (100,100,100), 1)
                img.draw_line(int(self.laser_x), 0, int(self.laser_x), 320, (100,100,100), 1)

                # 显示校准信息
                img.draw_string_advanced(10, 10, 16, "激光校准工具", (255,255,0))
                img.draw_string_advanced(10, 35, 14, f"当前位置: ({self.laser_x:.1f}, {self.laser_y:.1f})", (255,255,255))
                img.draw_string_advanced(10, 55, 14, "点击设置激光位置", (255,255,255))
                img.draw_string_advanced(10, 75, 14, "长按3秒保存并退出", (0,255,0))

                # 显示校准步骤
                if calibration_step < 5:
                    img.draw_string_advanced(10, 100, 12, f"校准步骤: {calibration_step+1}/5", (255,255,0))
                    img.draw_string_advanced(10, 120, 12, "请将激光点对准目标位置", (255,255,255))

                # 处理触摸输入
                touch_data = self.tp.read()
                current_time = time.ticks_ms()

                if touch_data[2]:  # 有触摸
                    if last_touch_time == 0:
                        last_touch_time = current_time

                    touch_duration = current_time - last_touch_time

                    if touch_duration < 500:  # 短按 - 设置位置
                        touch_x, touch_y = touch_data[0], touch_data[1]
                        if 0 <= touch_x <= 480 and 0 <= touch_y <= 320:
                            self.laser_x = touch_x
                            self.laser_y = touch_y

                            # 记录校准点
                            self.calibration_points.append((touch_x, touch_y))
                            calibration_step += 1

                            print(f"校准点 {calibration_step}: ({touch_x}, {touch_y})")

                            # 绘制校准反馈
                            img.draw_circle(int(touch_x), int(touch_y), 12, (255,0,0), 2)

                    elif touch_duration >= 3000:  # 长按 - 保存退出
                        print("保存校准结果...")
                        self.save_calibration()
                        break

                    # 显示长按进度
                    if touch_duration > 1000:
                        progress = min(touch_duration / 3000.0, 1.0)
                        bar_width = int(200 * progress)
                        img.draw_line(10, 280, 10 + bar_width, 280, (0,255,0), 5)
                        img.draw_string_advanced(10, 260, 12, f"保存进度: {progress*100:.0f}%", (0,255,0))

                else:
                    last_touch_time = 0

                # 显示已校准的点
                for i, point in enumerate(self.calibration_points[-5:]):  # 显示最近5个点
                    img.draw_circle(int(point[0]), int(point[1]), 4, (0,255,0), 2)
                    img.draw_string_advanced(int(point[0])+10, int(point[1]), 10, f"{i+1}", (0,255,0))

                # 显示图像
                img.compressed_for_ide()
                Display.show_image(img, x=160, y=80)

        except KeyboardInterrupt:
            print("校准被中断")
        except Exception as e:
            print(f"校准错误: {e}")
        finally:
            if isinstance(sensor, Sensor):
                sensor.stop()
            Display.deinit()
            MediaManager.deinit()
            print("校准工具已退出")

# 运行校准
if __name__ == "__main__":
    calibrator = LaserCalibrator()
    calibrator.run_calibration()