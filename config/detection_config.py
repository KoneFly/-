# K230矩形检测配置文件
# Rectangle Detection Configuration for K230

# 显示分辨率配置
LCD_WIDTH, LCD_HEIGHT = 800, 480         # 物理分辨率
DISPLAY_WIDTH, DISPLAY_HEIGHT = 480, 320  # 显示分辨率

# 激光器初始位置 (可通过校准模式调整)
DEFAULT_LASER_X = 260
DEFAULT_LASER_Y = 166.5

# 串口配置
UART_BAUDRATE = 115200
UART_TX_PIN = 11  # FPIOA.UART2_TXD
UART_RX_PIN = 12  # FPIOA.UART2_RXD

# A4纸检测参数
CANNY_THRESH1 = 40         # 边缘检测低阈值
CANNY_THRESH2 = 120        # 边缘检测高阈值
APPROX_EPSILON = 0.02      # 多边形拟合精度
AREA_MIN_RATIO = 0.01      # 最小面积占比
MAX_ANGLE_COS = 1.5        # 角度余弦阈值
GAUSSIAN_BLUR_SIZE = 5     # 高斯模糊大小

# A4纸筛选参数
MIN_AREA = 5000/4            # 最小面积
MAX_AREA = 640*480*0.8     # 最大面积
MIN_ASPECT_RATIO = 0.6     # 最小宽高比
MAX_ASPECT_RATIO = 1.5     # 最大宽高比

# 控制参数
DEAD_ZONE = 5              # 死区范围（像素）
LONG_PRESS_THRESHOLD = 3000  # 长按切换模式时间阈值（毫秒）

# 颜色配置（RGB565格式）
COLORS = {
    'laser_point': (0, 0, 255),      # 蓝色 - 激光点
    'center_cross': (255, 0, 0),     # 红色 - 中心十字
    'best_rect': (255, 255, 0),      # 黄色 - 最佳矩形
    'candidate_rect': (0, 255, 0),   # 绿色 - 候选矩形
    'rejected_rect': (255, 0, 0),    # 红色 - 被拒绝的矩形
    'connection_line': (255, 255, 0), # 黄色 - 连接线
    'crosshair': (100, 100, 100),    # 灰色 - 十字准线
    'text_normal': (255, 255, 255),  # 白色 - 普通文本
    'text_warning': (255, 0, 0),     # 红色 - 警告文本
    'text_success': (0, 255, 0),     # 绿色 - 成功文本
    'text_calibration': (255, 255, 0) # 黄色 - 校准模式文本
}