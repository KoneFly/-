# 故障排除指南

## 常见问题分类

### 🔧 硬件相关问题

#### 问题1: 摄像头无图像输出

**症状**:
- 屏幕显示黑屏或噪点
- 程序运行但无图像处理结果

**可能原因**:
- 摄像头连接不良
- 供电不足
- 驱动初始化失败

**解决方案**:
```python
# 1. 检查硬件连接
# 2. 重新初始化摄像头
sensor = Sensor(width=480, height=320)
sensor.reset()
sensor.set_framesize(width=480, height=320)
sensor.set_pixformat(Sensor.RGB565)
sensor.run()

# 3. 检查供电
# 确保5V/2A供电充足
```

#### 问题2: 触摸屏无响应

**症状**:
- 触摸无反应
- 无法切换模式
- 校准功能失效

**解决方案**:
```python
# 1. 重新初始化触摸控制器
tp = TOUCH(0)

# 2. 检查触摸数据
touch_data = tp.read()
print(f"Touch data: {touch_data}")

# 3. 验证坐标范围
if 0 <= touch_x <= 480 and 0 <= touch_y <= 320:
    # 坐标有效
    pass
```

#### 问题3: 串口通信异常

**症状**:
- 无数据发送
- 接收端收到乱码
- 通信中断

**解决方案**:
```python
# 1. 检查引脚配置
fpioa = FPIOA()
fpioa.set_function(11, FPIOA.UART2_TXD)
fpioa.set_function(12, FPIOA.UART2_RXD)

# 2. 验证波特率
uart = UART(UART.UART2, 115200)

# 3. 测试发送
uart.write("@0000000000!")  # 测试数据
```

### 🖥️ 软件相关问题

#### 问题4: 程序启动失败

**症状**:
- 程序崩溃退出
- 初始化错误
- 内存不足

**解决方案**:
```python
try:
    # 检查每个初始化步骤
    print("初始化硬件...")
    sensor = Sensor(width=480, height=320)
    print("摄像头初始化完成")

    Display.init(Display.ST7701, width=800, height=480, to_ide=True)
    print("显示器初始化完成")

    MediaManager.init()
    print("媒体管理器初始化完成")

except Exception as e:
    print(f"初始化失败: {e}")
```

#### 问题5: 矩形检测失效

**症状**:
- 无法检测到A4纸
- 检测精度低
- 误检测其他物体

**解决方案**:

1. **调整检测参数**:
```python
# 降低边缘检测阈值
canny_thresh1 = 30  # 原值40
canny_thresh2 = 100 # 原值120

# 调整面积范围
MIN_AREA = 3000     # 原值1250
MAX_AREA = 200000   # 原值153600
```

2. **改善环境条件**:
- 确保充足均匀光照
- 避免强烈阴影
- 保持A4纸张平整
- 提供对比度背景

3. **检查图像质量**:
```python
# 保存调试图像
gray_img = img.to_grayscale()
# 检查图像是否清晰
```

#### 问题6: 模式切换失效

**症状**:
- 长按无法切换模式
- 模式指示错误
- 功能混乱

**解决方案**:
```python
# 检查长按逻辑
print(f"触摸状态: {touch_data[2]}")
print(f"长按时间: {current_time - touch_start_time}")
print(f"当前模式: {mode}")

# 确保阈值合理
long_press_threshold = 3000  # 3秒
```

### 📊 性能相关问题

#### 问题7: 帧率过低

**症状**:
- FPS显示很低(<10)
- 图像更新卡顿
- 响应延迟

**解决方案**:

1. **优化图像处理**:
```python
# 减少不必要的绘图操作
if best_corners:  # 只在检测到目标时绘制
    # 绘制矩形和中心点
    pass

# 降低分辨率
sensor = Sensor(width=320, height=240)  # 更低分辨率
```

2. **优化算法参数**:
```python
# 提高面积阈值减少候选矩形
MIN_AREA = 8000  # 增大最小面积

# 简化多边形拟合
approx_epsilon = 0.05  # 增大拟合精度阈值
```

#### 问题8: 内存不足

**症状**:
- 程序运行一段时间后崩溃
- 内存分配失败
- 性能逐渐下降

**解决方案**:
```python
# 定期清理对象
import gc
gc.collect()  # 手动垃圾回收

# 避免大量图像缓存
# 及时释放临时图像对象
```

### 🎯 精度相关问题

#### 问题9: 定位精度不足

**症状**:
- 中心点计算偏差大
- 激光定位不准确
- 控制系统响应异常

**解决方案**:

1. **校准激光位置**:
```python
# 使用校准模式精确设置激光坐标
# 确保激光点在摄像头视野内
# 定期重新校准
```

2. **调整死区参数**:
```python
# 根据实际需求调整死区
dead_zone = 3  # 减小死区提高精度
# 或者
dead_zone = 8  # 增大死区减少抖动
```

3. **改进算法**:
```python
# 使用加权平均计算中心
def calculate_weighted_center(corners):
    # 实现加权中心计算
    pass
```

#### 问题10: 误差积累

**症状**:
- 长时间运行精度下降
- 系统漂移
- 需要频繁重启

**解决方案**:
```python
# 定期重置参考点
reset_counter = 0
if reset_counter > 1000:  # 每1000帧重置一次
    # 重新校准或重置参数
    reset_counter = 0
reset_counter += 1
```

## 调试工具和方法

### 日志调试

```python
import time

def debug_log(message, level="INFO"):
    timestamp = time.strftime("%H:%M:%S")
    print(f"[{timestamp}][{level}] {message}")

# 使用示例
debug_log("开始检测矩形", "DEBUG")
debug_log(f"检测到{len(rects)}个矩形", "INFO")
debug_log("未找到有效目标", "WARNING")
```

### 参数监控

```python
# 实时显示关键参数
img.draw_string_advanced(10, 90, 12, f"检测数量: {len(rects)}", (255,255,255))
img.draw_string_advanced(10, 110, 12, f"最佳面积: {max_area}", (255,255,255))
img.draw_string_advanced(10, 130, 12, f"激光位置: ({laser_x:.1f},{laser_y:.1f})", (255,255,255))
```

### 数据导出

```python
# 保存调试数据
debug_data = {
    'timestamp': time.time(),
    'rects_count': len(rects),
    'best_area': max_area,
    'laser_pos': (laser_x, laser_y),
    'center_pos': a4_center
}
# 可以保存到文件或通过串口发送
```

## 环境优化建议

### 光照条件
- 使用均匀的LED照明
- 避免直射阳光和强烈阴影
- 保持照明稳定，避免频闪

### 工作环境
- 选择平整稳定的工作台面
- 避免振动和晃动
- 保持环境温度稳定

### A4纸张要求
- 使用标准白色A4纸
- 确保纸张平整无折痕
- 避免污渍和标记影响检测

## 维护建议

### 定期检查
- 每周检查硬件连接
- 清洁摄像头镜头
- 检查电源稳定性

### 软件更新
- 定期备份配置参数
- 记录最佳参数设置
- 监控系统性能指标

### 预防措施
- 建立系统监控机制
- 设置报警阈值
- 准备备用硬件组件

## 紧急恢复

### 系统无响应
1. 断电重启
2. 检查SD卡是否损坏
3. 重新烧录系统镜像

### 配置丢失
1. 恢复默认配置
2. 重新进行校准
3. 逐步调整参数

### 硬件故障
1. 替换故障组件
2. 检查连接线路
3. 联系技术支持

---

**如果以上方法都无法解决问题，请：**
1. 记录详细的错误信息
2. 保存相关日志文件
3. 联系项目维护者获取支持