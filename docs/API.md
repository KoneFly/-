# API 文档

## 主要函数接口

### err_handling(center_x, center_y, laser_x, laser_y, uart)

**功能**: 处理检测中心与激光点的偏差，并通过串口发送控制数据

**参数**:
- `center_x` (float): 检测到的矩形中心X坐标
- `center_y` (float): 检测到的矩形中心Y坐标
- `laser_x` (float): 激光器X坐标
- `laser_y` (float): 激光器Y坐标
- `uart` (UART): 串口对象

**返回值**: None

**功能说明**:
- 计算X、Y轴偏差
- 应用死区处理
- 格式化为串口协议数据
- 发送控制指令

### calculate_center(corners)

**功能**: 计算矩形的几何中心点

**参数**:
- `corners` (list): 矩形四个角点坐标列表 [(x1,y1), (x2,y2), (x3,y3), (x4,y4)]

**返回值**:
- `tuple`: (center_x, center_y) 中心点坐标
- `None`: 角点数量不足4个时

**算法**: 四个角点坐标的算术平均值

### sort_corners(corners)

**功能**: 将矩形角点按特定顺序排序

**参数**:
- `corners` (list): 原始角点坐标列表

**返回值**:
- `list`: 排序后的角点列表，顺序为左上→右上→右下→左下

**算法**:
1. 计算矩形中心
2. 按与中心的夹角排序
3. 调整起点为左上角

## 配置参数接口

### 检测参数

```python
# 边缘检测参数
CANNY_THRESH1 = 40      # 低阈值
CANNY_THRESH2 = 120     # 高阈值

# 形状筛选参数
MIN_AREA = 1250         # 最小面积
MAX_AREA = 153600       # 最大面积
MIN_ASPECT_RATIO = 0.6  # 最小宽高比
MAX_ASPECT_RATIO = 1.5  # 最大宽高比
```

### 控制参数

```python
DEAD_ZONE = 5                   # 死区范围(像素)
LONG_PRESS_THRESHOLD = 3000     # 长按阈值(毫秒)
```

## 串口通信协议

### 数据格式

```
@XXXXXYYYYY!
```

### 字段说明

| 字段 | 长度 | 说明 |
|------|------|------|
| @ | 1字节 | 起始标志 |
| XXXXX | 5字节 | X轴偏差(符号位+4位数值) |
| YYYYY | 5字节 | Y轴偏差(符号位+4位数值) |
| ! | 1字节 | 结束标志 |

### 符号位编码

- `0`: 正偏差(右/下)
- `1`: 负偏差(左/上)
- `2`: 特殊状态(无检测目标)

### 示例数据

```python
"@0012000050!"  # X+12, Y+5
"@1003010020!"  # X-30, Y-20
"@2000020000!"  # 无目标检测
```

## 触摸事件处理

### 触摸检测

```python
touch_data = tp.read()
is_touched = touch_data[2]      # 触摸状态
touch_x = touch_data[0]         # X坐标
touch_y = touch_data[1]         # Y坐标
```

### 长按检测逻辑

```python
if touch_data[2]:  # 检测到触摸
    if touch_start_time == 0:
        touch_start_time = current_time
    elif current_time - touch_start_time >= long_press_threshold:
        # 执行长按操作
        mode = "2" if mode == "1" else "1"
        touch_start_time = 0
else:
    touch_start_time = 0  # 重置计时
```

## 图像处理接口

### 矩形检测

```python
rects = cv_lite.grayscale_find_rectangles_with_corners(
    image_shape,        # [height, width]
    img_np,            # numpy图像数组
    canny_thresh1,     # 边缘检测低阈值
    canny_thresh2,     # 边缘检测高阈值
    approx_epsilon,    # 多边形拟合精度
    area_min_ratio,    # 最小面积比例
    max_angle_cos,     # 角度余弦阈值
    gaussian_blur_size # 高斯模糊核大小
)
```

### 返回数据格式

每个检测到的矩形包含12个元素:
```python
[x, y, w, h, c1.x, c1.y, c2.x, c2.y, c3.x, c3.y, c4.x, c4.y]
```

- `x, y, w, h`: 边界框坐标和尺寸
- `c1-c4`: 四个角点的坐标

## 绘图接口

### 基本绘图

```python
# 绘制线条
img.draw_line(x1, y1, x2, y2, color=(r,g,b), thickness=width)

# 绘制圆形
img.draw_circle(cx, cy, radius, color=(r,g,b), thickness=width)

# 绘制十字
img.draw_cross(cx, cy, color=(r,g,b), thickness=width, size=length)

# 绘制文本
img.draw_string_advanced(x, y, size, text, color=(r,g,b))
```

### 颜色常量

```python
COLORS = {
    'laser_point': (0, 0, 255),      # 蓝色
    'center_cross': (255, 0, 0),     # 红色
    'best_rect': (255, 255, 0),      # 黄色
    'candidate_rect': (0, 255, 0),   # 绿色
    'rejected_rect': (255, 0, 0),    # 红色
    'connection_line': (255, 255, 0), # 黄色
    'text_normal': (255, 255, 255),  # 白色
    'text_warning': (255, 0, 0),     # 红色
    'text_success': (0, 255, 0),     # 绿色
}
```

## 错误处理

### 异常类型

```python
try:
    # 主程序逻辑
    pass
except KeyboardInterrupt as e:
    print("用户停止: ", e)
except BaseException as e:
    print(f"异常: {e}")
finally:
    # 清理资源
    if isinstance(sensor, Sensor):
        sensor.stop()
    Display.deinit()
    MediaManager.deinit()
```

### 常见异常处理

1. **硬件初始化失败**: 检查硬件连接
2. **内存不足**: 释放不必要的对象
3. **触摸屏无响应**: 重新初始化触摸驱动
4. **串口通信失败**: 检查波特率和引脚配置