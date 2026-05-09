# 设备使用指南

## 概述

设备初始化完成后，用户应用程序通过以下三步使用设备：

1. **获取设备句柄** - 通过 `esp_board_manager_get_device_handle()` 获取
2. **访问底层接口** - 句柄结构包含标准 ESP-IDF 驱动接口
3. **调用标准 API** - 使用对应组件的标准 ESP-IDF API

---

## 1. LCD 显示设备使用

### 1.1 获取设备句柄

```c
#include "dev_display_lcd.h"

dev_display_lcd_handles_t *lcd_handle;
esp_board_manager_get_device_handle("display_lcd", (void **)&lcd_handle);
```

### 1.2 句柄结构

```c
typedef struct {
    esp_lcd_panel_handle_t panel_handle;  // LCD 面板句柄
    esp_lcd_panel_io_handle_t io_handle;  // LCD IO 句柄
    void *priv;                           // 私有数据
} dev_display_lcd_handles_t;
```

### 1.3 常用操作

```c
// 初始化面板
esp_lcd_panel_init(lcd_handle->panel_handle);

// 开启显示
esp_lcd_panel_disp_on_off(lcd_handle->panel_handle, true);

// 绘制位图
uint16_t *frame_buffer = /* 颜色数据 */;
esp_lcd_panel_draw_bitmap(lcd_handle->panel_handle,
                          0, 0,           // 起始坐标 (x, y)
                          1024, 600,      // 宽度、高度
                          frame_buffer);   // 像素数据

// 设置镜像
esp_lcd_panel_mirror(lcd_handle->panel_handle, true, false);

// 设置对比度
esp_lcd_panel_set_contrast(lcd_handle->panel_handle, 128);
```

### 1.4 关键 API 汇总

| API | 功能 | 头文件 |
|-----|------|--------|
| `esp_lcd_panel_init()` | 初始化面板 | `esp_lcd_panel_ops.h` |
| `esp_lcd_panel_disp_on_off()` | 开关显示 | `esp_lcd_panel_ops.h` |
| `esp_lcd_panel_draw_bitmap()` | 绘制位图 | `esp_lcd_panel_ops.h` |
| `esp_lcd_panel_mirror()` | 设置镜像 | `esp_lcd_panel_ops.h` |
| `esp_lcd_panel_set_contrast()` | 设置对比度 | `esp_lcd_panel_ops.h` |

---

## 2. 音频编解码器使用

### 2.1 获取设备句柄

```c
#include "dev_audio_codec.h"

dev_audio_codec_handles_t *audio_handle;
esp_board_manager_get_device_handle("audio_dac", (void **)&audio_handle);
```

### 2.2 句柄结构

```c
typedef struct {
    esp_codec_dev_handle_t       codec_dev;      // Codec 设备句柄
    const audio_codec_data_if_t *data_if;        // 数据接口 (I2S)
    const audio_codec_ctrl_if_t *ctrl_if;        // 控制接口 (I2C)
    const audio_codec_gpio_if_t *gpio_if;        // GPIO 接口 (PA 控制)
    const audio_codec_if_t      *codec_if;       // Codec 接口
    int16_t                      tx_aux_out_io;  // 辅助输出 IO
} dev_audio_codec_handles_t;
```

### 2.3 音频播放示例

```c
#include "esp_codec_dev.h"

// 配置采样参数
esp_codec_dev_sample_info_t fs = {
    .sample_rate = 48000,
    .channel = 2,
    .bits_per_sample = 16,
};

// 打开设备
esp_codec_dev_open(audio_handle->codec_dev, &fs);

// 写入音频数据
uint8_t audio_buffer[4096];
size_t bytes_written;
esp_codec_dev_write(audio_handle->codec_dev, audio_buffer, sizeof(audio_buffer), &bytes_written);

// 关闭设备
esp_codec_dev_close(audio_handle->codec_dev);
```

### 2.4 音频录制示例

```c
// 获取 ADC 设备句柄
dev_audio_codec_handles_t *adc_handle;
esp_board_manager_get_device_handle("audio_adc", (void **)&adc_handle);

// 配置采样参数
esp_codec_dev_sample_info_t fs = {
    .sample_rate = 16000,
    .channel = 2,
    .bits_per_sample = 16,
};

// 打开设备
esp_codec_dev_open(adc_handle->codec_dev, &fs);

// 读取音频数据
uint8_t buffer[4096];
size_t bytes_read;
esp_codec_dev_read(adc_handle->codec_dev, buffer, sizeof(buffer), &bytes_read);

// 关闭设备
esp_codec_dev_close(adc_handle->codec_dev);
```

### 2.5 关键 API 汇总

| API | 功能 | 头文件 |
|-----|------|--------|
| `esp_codec_dev_open()` | 打开音频设备 | `esp_codec_dev.h` |
| `esp_codec_dev_write()` | 写入音频数据 | `esp_codec_dev.h` |
| `esp_codec_dev_read()` | 读取音频数据 | `esp_codec_dev.h` |
| `esp_codec_dev_close()` | 关闭音频设备 | `esp_codec_dev.h` |
| `esp_codec_dev_set_vol()` | 设置音量 | `esp_codec_dev.h` |

---

## 3. 摄像头设备使用

### 3.1 获取设备句柄

```c
#include "dev_camera.h"

dev_camera_handle_t *camera_handle;
esp_board_manager_get_device_handle("camera", (void **)&camera_handle);
```

### 3.2 句柄结构

```c
typedef struct {
    const char *dev_path;     // 摄像头设备路径
    const char *meta_path;    // 元数据路径（CSI摄像头）
} dev_camera_handle_t;
```

### 3.3 摄像头使用示例

```c
#include "esp_video.h"

// 打开视频流
video_stream_handle_t stream;
esp_video_stream_open(camera_handle->dev_path, &stream);

// 配置视频参数
video_stream_params_t params = {
    .width = 640,
    .height = 480,
    .format = VIDEO_PIX_FMT_RGB565,
    .fps = 15,
};
esp_video_stream_set_params(stream, &params);

// 循环读取帧
while (1) {
    video_frame_t frame;
    esp_err_t ret = esp_video_stream_read_frame(stream, &frame);
    if (ret == ESP_OK) {
        // 处理图像数据
        process_image(frame.data, frame.size);
        
        // 释放帧
        esp_video_stream_release_frame(stream, &frame);
    }
    vTaskDelay(pdMS_TO_TICKS(100));
}

// 关闭流
esp_video_stream_close(stream);
```

### 3.4 获取 ISP 元数据（CSI摄像头）

```c
if (camera_handle->meta_path) {
    video_stream_handle_t isp_stream;
    esp_video_stream_open(camera_handle->meta_path, &isp_stream);
    
    video_frame_t meta_frame;
    esp_video_stream_read_frame(isp_stream, &meta_frame);
    
    // 解析元数据（曝光、白平衡等）
    parse_isp_metadata(meta_frame.data);
    
    esp_video_stream_release_frame(isp_stream, &meta_frame);
    esp_video_stream_close(isp_stream);
}
```

### 3.5 关键 API 汇总

| API | 功能 | 头文件 |
|-----|------|--------|
| `esp_video_stream_open()` | 打开视频流 | `esp_video.h` |
| `esp_video_stream_set_params()` | 配置视频参数 | `esp_video.h` |
| `esp_video_stream_read_frame()` | 读取帧数据 | `esp_video.h` |
| `esp_video_stream_release_frame()` | 释放帧 | `esp_video.h` |
| `esp_video_stream_close()` | 关闭视频流 | `esp_video.h` |

---

## 4. 存储设备使用

### 4.1 获取设备句柄

```c
#include "dev_fs_fat.h"

dev_fs_fat_handle_t *fs_handle;
esp_board_manager_get_device_handle("sdcard", (void **)&fs_handle);
```

### 4.2 文件操作示例

```c
#include "ff.h"

FATFS fs;
FIL file;
FRESULT res;

// 挂载文件系统
res = f_mount(&fs, fs_handle->base_path, 1);
if (res != FR_OK) {
    ESP_LOGE(TAG, "Failed to mount filesystem");
    return;
}

// 打开文件
res = f_open(&file, "/sdcard/test.txt", FA_WRITE | FA_CREATE_ALWAYS);
if (res != FR_OK) {
    ESP_LOGE(TAG, "Failed to open file");
    return;
}

// 写入数据
const char *data = "Hello, ESP32!";
UINT bytes_written;
res = f_write(&file, data, strlen(data), &bytes_written);

// 关闭文件
f_close(&file);

// 卸载文件系统
f_mount(NULL, fs_handle->base_path, 0);
```

### 4.3 关键 API 汇总

| API | 功能 | 头文件 |
|-----|------|--------|
| `f_mount()` | 挂载文件系统 | `ff.h` |
| `f_open()` | 打开文件 | `ff.h` |
| `f_write()` | 写入文件 | `ff.h` |
| `f_read()` | 读取文件 | `ff.h` |
| `f_close()` | 关闭文件 | `ff.h` |

---

## 5. GPIO 控制设备使用

### 5.1 获取设备句柄

```c
#include "dev_gpio_ctrl.h"

dev_gpio_ctrl_handles_t *gpio_handle;
esp_board_manager_get_device_handle("gpio_led", (void **)&gpio_handle);
```

### 5.2 GPIO 操作示例

```c
// 设置 GPIO 输出电平
gpio_set_level(gpio_handle->gpio_num, 1);  // 高电平

// 读取 GPIO 输入电平
int level = gpio_get_level(gpio_handle->gpio_num);

// 设置 GPIO 方向
gpio_set_direction(gpio_handle->gpio_num, GPIO_MODE_OUTPUT);
```

---

## 6. 外设直接使用

### 6.1 I2C 外设

```c
#include "driver/i2c.h"

// 获取 I2C 外设句柄
i2c_master_bus_handle_t i2c_handle;
esp_board_manager_get_periph_handle("i2c_master", (void **)&i2c_handle);

// I2C 写操作
uint8_t data[2] = {0x00, 0x10};
i2c_master_transmit(i2c_handle, 0x30, data, sizeof(data), pdMS_TO_TICKS(100));

// I2C 读操作
uint8_t recv_data[4];
i2c_master_receive(i2c_handle, 0x30, recv_data, sizeof(recv_data), pdMS_TO_TICKS(100));
```

### 6.2 I2S 外设

```c
#include "driver/i2s_std.h"

// 获取 I2S 外设句柄
i2s_chan_handle_t i2s_handle;
esp_board_manager_get_periph_handle("i2s_audio_out", (void **)&i2s_handle);

// I2S 写入数据
uint8_t i2s_buffer[512];
size_t bytes_written;
i2s_channel_write(i2s_handle, i2s_buffer, sizeof(i2s_buffer), &bytes_written, portMAX_DELAY);
```

### 6.3 SPI 外设

```c
#include "driver/spi_master.h"

// 获取 SPI 外设句柄
spi_device_handle_t spi_handle;
esp_board_manager_get_periph_handle("spi_master", (void **)&spi_handle);

// SPI 传输
spi_transaction_t t = {
    .length = 8 * 4,  // 4 bytes
    .tx_buffer = tx_data,
    .rx_buffer = rx_data,
};
spi_device_transmit(spi_handle, &t);
```

---

## 7. 完整使用流程图

```mermaid
flowchart TD
    A[应用程序启动] --> B[esp_board_manager_init]
    
    B --> C{设备类型}
    
    C -->|LCD| D1[获取 display_lcd 句柄]
    D1 --> D2[esp_lcd_panel_draw_bitmap]
    
    C -->|音频| E1[获取 audio_dac 句柄]
    E1 --> E2[esp_codec_dev_write]
    
    C -->|摄像头| F1[获取 camera 句柄]
    F1 --> F2[esp_video_stream_read_frame]
    
    C -->|存储| G1[获取 sdcard 句柄]
    G1 --> G2[f_write / f_read]
    
    C -->|GPIO| H1[获取 gpio_ctrl 句柄]
    H1 --> H2[gpio_set_level]
    
    C -->|外设| I1[获取 i2c/i2s/spi 句柄]
    I1 --> I2[直接调用驱动 API]
```

---

## 8. 设备生命周期管理

### 8.1 引用计数机制

Board Manager 使用引用计数管理设备生命周期：

```c
// 首次初始化 (ref_count = 0 -> 1)
esp_board_manager_init_device_by_name("display_lcd");

// 再次获取 (ref_count = 1 -> 2)
// 不重复初始化，返回已有句柄
esp_board_manager_get_device_handle("display_lcd", &handle);

// 去初始化 (ref_count = 2 -> 1)
esp_board_manager_deinit_device_by_name("display_lcd");

// 最终去初始化 (ref_count = 1 -> 0)
// 真正释放资源
esp_board_manager_deinit_device_by_name("display_lcd");
```

### 8.2 最佳实践

1. **单次初始化**：在 `app_main()` 开始时调用 `esp_board_manager_init()`
2. **按需获取**：在需要使用设备时获取句柄
3. **及时释放**：不再使用设备时调用去初始化
4. **错误处理**：检查所有 API 返回值

---

## 附录：设备类型与 API 映射表

| 设备类型 | 句柄结构 | 核心 API | 头文件 |
|---------|---------|---------|--------|
| display_lcd | `dev_display_lcd_handles_t` | `esp_lcd_panel_*` | `dev_display_lcd.h` |
| audio_dac | `dev_audio_codec_handles_t` | `esp_codec_dev_*` | `dev_audio_codec.h` |
| camera | `dev_camera_handle_t` | `esp_video_*` | `dev_camera.h` |
| fs_fat | `dev_fs_fat_handle_t` | `f_*` | `dev_fs_fat.h` |
| gpio_ctrl | `dev_gpio_ctrl_handles_t` | `gpio_*` | `dev_gpio_ctrl.h` |
| i2c_master | `i2c_master_bus_handle_t` | `i2c_master_*` | `driver/i2c.h` |
| i2s_audio | `i2s_chan_handle_t` | `i2s_channel_*` | `driver/i2s_std.h` |
| spi_master | `spi_device_handle_t` | `spi_device_*` | `driver/spi_master.h` |
