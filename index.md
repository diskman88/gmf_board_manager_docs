# ESP Board Manager 技术文档

---

## 1. 组件架构概述

### 1.1 系统定位

```
┌─────────────────────────────────────────────────────────┐
│                    Application Layer                      │
│                   (用户应用程序)                          │
└─────────────────────────────────────────────────────────┘
                            │
                            ▼
┌─────────────────────────────────────────────────────────┐
│                  ESP Board Manager                       │
│  ┌─────────────────────────────────────────────────┐    │
│  │        esp_board_manager.h (顶层API)            │    │
│  └─────────────────────────────────────────────────┘    │
│                            │                             │
│        ┌───────────────────┴───────────────────┐        │
│        ▼                                       ▼        │
│  ┌─────────────────┐               ┌─────────────────┐ │
│  │ esp_board_device.h │             │esp_board_periph.h│ │
│  │   (设备管理层)    │               │  (外设管理层)    │ │
│  └────────┬────────┘               └────────┬────────┘ │
│           │                                  │          │
└───────────┼──────────────────────────────────┼──────────┘
            │                                  │
            ▼                                  ▼
┌─────────────────────────┐    ┌─────────────────────────┐
│   Devices (设备层)       │    │   Peripherals (外设层)  │
│  - dev_audio_codec      │    │  - periph_i2c           │
│  - dev_display_lcd      │    │  - periph_i2s           │
│  - dev_camera           │    │  - periph_spi           │
│  - dev_fs_fat          │    │  - periph_gpio          │
│  - dev_button          │    │  - periph_ledc          │
└─────────────────────────┘    └─────────────────────────┘
            │                                  │
            ▼                                  ▼
┌─────────────────────────────────────────────────────────┐
│              ESP-IDF Driver Layer                       │
│         (driver/gpio, driver/i2c, driver/spi...)        │
└─────────────────────────────────────────────────────────┘
```

### 1.2 核心设计理念

**设备 (Device) vs 外设 (Peripheral) 的分离**

- **外设 (Peripheral)**：总线型基础资源，如 I2C、I2S、SPI、GPIO 等
  - 具有类型 (type) 和角色 (role)
  - 可以被多个设备共享复用
  - 例如：`i2c_master`、`i2s_audio_out`、`gpio_pa_control`

- **设备 (Device)**：具体功能模块，如音频编解码器、LCD 显示屏、摄像头等
  - 依赖一个或多个外设
  - 通常包含特定芯片 (chip) 的驱动配置
  - 例如：`audio_dac` (ES8311)、`display_lcd` (EK79007)

### 1.3 配置驱动的生成流程

```
┌──────────────────────────────────────────────────────────────┐
│                      开发板配置阶段                           │
│                                                              │
│  boards/<board_name>/                                       │
│  ├── board_info.yaml        (板级基本信息)                   │
│  ├── board_peripherals.yaml (外设配置)                       │
│  ├── board_devices.yaml    (设备配置)                       │
│  └── setup_device.c        (可选的自定义初始化代码)          │
└──────────────────────────────────────────────────────────────┘
                              │
                              ▼ (cmake 阶段调用生成器)
┌──────────────────────────────────────────────────────────────┐
│                      代码生成阶段                            │
│                                                              │
│  generators/                   gen_bmgr_config_codes.py     │
│  ├── device_parser.py         └── 解析 YAML 配置             │
│  ├── peripheral_parser.py     └── 生成 C 结构体              │
│  └── config_generator.py     └── 输出头文件                 │
└──────────────────────────────────────────────────────────────┘
                              │
                              ▼
┌──────────────────────────────────────────────────────────────┐
│                      编译阶段                                │
│                                                              │
│  生成文件：                                                 │
│  ├── gen_board_device_handles.c  (设备注册表)               │
│  ├── gen_board_periph_handles.c  (外设注册表)               │
│  └── board_info.c               (板级信息)                  │
└──────────────────────────────────────────────────────────────┘
```

---

## 2. 核心数据结构

### 2.1 设备相关结构体

```c
// 设备描述符 (定义阶段，由生成器产生)
typedef struct esp_board_device_desc {
    const struct esp_board_device_desc *next;    // 链表 next 指针
    const char *name;                           // 设备名称 (如 "audio_dac")
    const char *chip;                           // 芯片型号 (如 "es8311")
    const char *type;                           // 设备类型 (如 "audio_codec")
    const char *sub_type;                       // 子类型 (如 "dsi", "spi")
    const void *cfg;                            // 配置数据指针
    uint16_t cfg_size;                          // 配置数据大小
    uint8_t init_skip : 1;                      // 跳过自动初始化标志
    const char *power_ctrl_device;               // 电源控制设备名
} esp_board_device_desc_t;

// 设备句柄 (运行时管理)
typedef struct esp_board_device_handle {
    struct esp_board_device_handle *next;        // 链表 next 指针
    const char *name;                           // 设备名称
    const char *chip;                           // 芯片型号
    const char *type;                          // 设备类型
    void *device_handle;                        // 设备-specific 句柄
    uint8_t ref_count;                         // 引用计数 (用于管理初始化/去初始化)
    esp_board_device_init_func init;            // 初始化函数指针
    esp_board_device_deinit_func deinit;        // 去初始化函数指针
} esp_board_device_handle_t;
```

### 2.2 外设相关结构体

```c
// 外设描述符 (定义阶段)
typedef struct esp_board_periph_desc {
    const struct esp_board_periph_desc *next;   // 链表 next 指针
    const char *name;                           // 外设名称 (如 "i2c_master")
    const char *type;                           // 外设类型 (如 "i2c")
    esp_board_periph_role_t role;               // 角色 (如 MASTER/SLAVE)
    const char *format;                         // 数据格式 (如 "std-out")
    const void *cfg;                            // 配置数据指针
    int cfg_size;                               // 配置数据大小
    int id;                                     // ID (从名称中提取，如 gpio48 -> 48)
} esp_board_periph_desc_t;

// 外设条目 (运行时管理)
typedef struct esp_board_periph_entry {
    struct esp_board_periph_entry *next;        // 链表 next 指针
    const char *type;                           // 外设类型
    esp_board_periph_role_t role;               // 角色
    esp_board_periph_init_func init;            // 初始化函数
    esp_board_periph_deinit_func deinit;        // 去初始化函数
} esp_board_periph_entry_t;

// 外设列表节点 (运行时实例)
typedef struct esp_board_periph_list {
    struct esp_board_periph_list *next;         // 链表 next 指针
    const char *name;                           // 外设名称
    const char *type;                           // 外设类型
    esp_board_periph_role_t role;               // 角色
    void *periph_handle;                        // 外设-specific 句柄
    uint8_t ref_count;                          // 引用计数
} esp_board_periph_list_t;
```

### 2.3 板级信息结构体

```c
// 板级信息 (定义在 board_info.yaml)
typedef struct esp_board_info {
    const char *name;           // 板子名称 (如 "esp32_p4_function_ev")
    const char *chip;           // 芯片型号 (如 "esp32p4")
    const char *version;        // 版本号 (如 "1.0.0")
    const char *description;    // 描述
    const char *manufacturer;   // 制造商
} esp_board_info_t;
```

### 2.4 初始化函数类型定义

```c
// 设备初始化函数类型
typedef int (*esp_board_device_init_func)(void *cfg, int cfg_size, void **device_handle);

// 设备去初始化函数类型
typedef int (*esp_board_device_deinit_func)(void *device_handle);

// 外设初始化函数类型
typedef esp_err_t (*esp_board_periph_init_func)(void *cfg, int cfg_size, void **periph_handle);

// 外设去初始化函数类型
typedef esp_err_t (*esp_board_periph_deinit_func)(void *periph_handle);
```

---

## 3. 顶层API管理机制

### 3.1 主要API函数

```c
// ============================================
// 初始化与去初始化
// ============================================

/**
 * @brief 初始化整个板级管理器
 *
 * 初始化顺序：
 * 1. 先初始化所有外设 (按 board_peripherals.yaml 顺序)
 * 2. 再初始化所有设备 (按 board_devices.yaml 顺序)
 *
 * @return ESP_OK 成功
 *         ESP_BOARD_ERR_MANAGER_ALREADY_INIT 已初始化
 */
esp_err_t esp_board_manager_init(void);

/**
 * @brief 去初始化整个板级管理器
 *
 * 去初始化顺序：
 * 1. 先去初始化所有设备
 * 2. 再去初始化所有外设
 */
esp_err_t esp_board_manager_deinit(void);


// ============================================
// 句柄获取
// ============================================

/**
 * @brief 获取外设句柄
 * @param periph_name 外设名称 (如 "i2c_master")
 * @param periph_handle 输出：外设句柄指针
 */
esp_err_t esp_board_manager_get_periph_handle(const char *periph_name, void **periph_handle);

/**
 * @brief 获取设备句柄
 * @param dev_name 设备名称 (如 "audio_dac")
 * @param device_handle 输出：设备句柄指针
 */
esp_err_t esp_board_manager_get_device_handle(const char *dev_name, void **device_handle);


// ============================================
// 配置获取
// ============================================

/**
 * @brief 获取设备配置
 * @param dev_name 设备名称
 * @param config 输出：配置指针
 */
esp_err_t esp_board_manager_get_device_config(const char *dev_name, void **config);

/**
 * @brief 获取外设配置
 * @param periph_name 外设名称
 * @param config 输出：配置指针
 */
esp_err_t esp_board_manager_get_periph_config(const char *periph_name, void **config);


// ============================================
// 单设备/外设操作
// ============================================

/**
 * @brief 初始化指定设备
 * @param dev_name 设备名称
 */
esp_err_t esp_board_manager_init_device_by_name(const char *dev_name);

/**
 * @brief 去初始化指定设备
 * @param dev_name 设备名称
 */
esp_err_t esp_board_manager_deinit_device_by_name(const char *dev_name);


// ============================================
// 注册与调试
// ============================================

/**
 * @brief 注册用户自定义设备句柄
 * @param reg_handle 设备句柄指针
 */
esp_err_t esp_board_manager_register_device_handle(esp_board_device_handle_t *reg_handle);

/**
 * @brief 打印所有设备和外设状态
 */
esp_err_t esp_board_manager_print(void);

/**
 * @brief 打印板级信息
 */
esp_err_t esp_board_manager_print_board_info(void);
```

### 3.2 API调用流程图

```
┌─────────────────────────────────────────────────────────────────┐
│                   esp_board_manager_init()                      │
└─────────────────────────────────────────────────────────────────┘
                            │
                            ▼
┌─────────────────────────────────────────────────────────────────┐
│              esp_board_periph_init_all()                        │
│                                                                 │
│  遍历 g_esp_board_peripherals[] (生成器产生)                    │
│  对每个外设调用 esp_board_periph_init(name)                      │
│                                                                 │
│  内部流程：                                                     │
│  1. 查找外设描述符 (通过 name 在链表中查找)                      │
│  2. 查找外设条目 (通过 type+role 匹配 init 函数)                │
│  3. 调用 init(cfg, cfg_size, &handle)                           │
│  4. 创建外设列表节点，加入链表                                   │
│  5. ref_count++                                                 │
└─────────────────────────────────────────────────────────────────┘
                            │
                            ▼
┌─────────────────────────────────────────────────────────────────┐
│              esp_board_device_init_all()                        │
│                                                                 │
│  遍历 g_esp_board_devices[] (生成器产生)                        │
│  对每个设备调用 esp_board_device_init(name)                      │
│                                                                 │
│  内部流程：                                                     │
│  1. 查找设备描述符 (通过 name 在链表中查找)                      │
│  2. 检查电源依赖 (power_ctrl_device)                             │
│  3. 调用 init(cfg, cfg_size, &handle)                           │
│  4. 创建设备列表节点，加入链表                                   │
│  5. ref_count++                                                 │
└─────────────────────────────────────────────────────────────────┘
                            │
                            ▼
┌─────────────────────────────────────────────────────────────────┐
│                    初始化完成                                    │
│                                                                 │
│  用户可通过以下方式获取句柄：                                   │
│  - esp_board_manager_get_device_handle("audio_dac", &handle)    │
│  - esp_board_manager_get_periph_handle("i2c_master", &handle)  │
└─────────────────────────────────────────────────────────────────┘
```

---

## 4. 设备和外设的配置初始化

### 4.1 YAML配置文件结构

#### board_info.yaml (板级信息)

```yaml
board: esp32_p4_function_ev    # 板子标识名
chip: esp32p4                   # 芯片型号
version: 1.0.0                  # 配置版本
description: "ESP32-P4 Function-EV Board"  # 描述
manufacturer: "ESPRESSIF"        # 制造商
```

#### board_peripherals.yaml (外设配置)

```yaml
peripherals:
  - name: i2c_master            # 外设名称 (必须以 type 开头)
    type: i2c                   # 外设类型
    role: master                # 角色
    config:                     # 外设专属配置
      port: 0                   # I2C 端口号
      pins:                     # 引脚配置
        sda: 7                  # [IO] SDA 引脚
        scl: 8                  # [IO] SCL 引脚

  - name: i2s_audio_out         # I2S 输出 (播放)
    type: i2s
    format: "std-out"          # 数据格式 (标准输出)
    role: master
    config:
      port: 0
      sample_rate_hz: 48000
      data_bit_width: 16
      slot_mode: "I2S_SLOT_MODE_STEREO"
      slot_mask: "I2S_STD_SLOT_BOTH"
      pins:
        mclk: 13
        bclk: 12
        ws: 10
        dout: 9
        din: 11

  - name: dsi_display           # DSI 显示接口
    type: dsi
    config:
      bus_id: 0
      data_lanes: 2
      lane_bit_rate_mbps: 1000
```

#### board_devices.yaml (设备配置)

```yaml
devices:
  - name: audio_dac             # 音频 DAC 设备
    chip: es8311               # 芯片型号
    type: audio_codec          # 设备类型
    config:                     # 设备配置
      dac_enabled: true        # 启用 DAC
      dac_max_channel: 1       # DAC 通道数
      dac_channel_mask: "1"    # 通道掩码
    peripherals:               # 依赖的外设
      - name: gpio_pa_control  # 功放控制 GPIO
        gain: 6
        active_level: 1
      - name: i2s_audio_out    # I2S 输出接口
      - name: i2c_master        # I2C 控制接口
        address: 0x30          # 覆写外设配置中的地址
        frequency: 400000       # 覆写外设配置中的频率

  - name: display_lcd          # LCD 显示设备
    chip: ek79007             # LCD 驱动 IC
    type: display_lcd         # 设备类型
    sub_type: dsi             # 子类型 (DSI 接口)
    dependencies:             # 组件依赖
      espressif/esp_lcd_ek79007: "^1.0.0"
    config:
      reset_gpio_num: 27
      bits_per_pixel: 24
      dpi_config:
        dpi_clock_freq_mhz: 48
        video_timing:
          h_size: 1024
          v_size: 600
      peripherals:
        - name: ldo_mipi       # MIPI 电源
        - name: dsi_display    # DSI 总线
```

### 4.2 初始化时序图

```
┌──────────────────────────────────────────────────────────────┐
│                      初始化时序图                             │
└──────────────────────────────────────────────────────────────┘

时间 ──────────────────────────────────────────────────────────────────▶

esp_board_manager_init()
      │
      ▼
┌─────────────────────────────────────────────────────────────┐
│ Phase 1: 外设初始化                                           │
│                                                              │
│ 外设1: i2c_master                                           │
│   ├─ esp_board_periph_init("i2c_master")                    │
│   ├─ 查找描述符 (name="i2c_master", type="i2c", role=master)
│   ├─ 查找初始化函数 (periph_i2s_init)                        │
│   └─ 调用 init(cfg, cfg_size, &handle)                       │
│                                                              │
│ 外设2: i2s_audio_out                                        │
│   ├─ esp_board_periph_init("i2s_audio_out")                  │
│   ├─ 查找描述符 (name="i2s_audio_out", type="i2s")           │
│   ├─ 查找初始化函数 (periph_i2s_init)                        │
│   └─ 调用 init(cfg, cfg_size, &handle)                       │
│                                                              │
│ 外设3: gpio_pa_control                                       │
│   └─ ...                                                    │
└─────────────────────────────────────────────────────────────┘
      │
      ▼
┌─────────────────────────────────────────────────────────────┐
│ Phase 2: 设备初始化                                           │
│                                                              │
│ 设备1: lcd_brightness (LEDC 背光)                             │
│   ├─ 检查电源依赖 (无)                                        │
│   ├─ esp_board_device_init("lcd_brightness")                 │
│   └─ 调用 dev_ledc_ctrl_init(cfg, cfg_size, &handle)        │
│                                                              │
│ 设备2: display_lcd (DSI LCD)                                 │
│   ├─ 检查电源依赖                                             │
│   ├─ 先初始化 power_ctrl_device (ldo_mipi)                   │
│   ├─ esp_board_device_init("display_lcd")                    │
│   ├─ 查找 sub_type="dsi" 的初始化函数                         │
│   └─ 调用 dev_display_lcd_sub_dsi_init(cfg, cfg_size, &handle)
│                                                              │
│ 设备3: audio_dac                                             │
│   ├─ 检查电源依赖 (无)                                        │
│   ├─ esp_board_device_init("audio_dac")                     │
│   ├─ 查找 type="audio_codec" 的初始化函数                     │
│   └─ 调用 dev_audio_codec_init(cfg, cfg_size, &handle)      │
└─────────────────────────────────────────────────────────────┘
      │
      ▼
┌─────────────────────────────┐
│ 初始化完成                   │
│                             │
│ s_manager_initialized = true │
│ ref_count 引用计数管理      │
└─────────────────────────────┘
```

### 4.3 引用计数机制

```c
// 引用计数工作原理

// 初始化时 (ref_count = 0 -> 1)
esp_board_device_init("audio_dac")
    if (ref_count == 0) {
        // 首次初始化，调用真实的 init 函数
        init(cfg, cfg_size, &device_handle);
    }
    ref_count++;

// 再次初始化 (ref_count = 1 -> 2)
// 通常发生在多个组件需要使用同一设备时
esp_board_device_init("audio_dac")
    // 不需要再次调用 init，直接返回已有句柄
    ref_count++;

// 去初始化时
esp_board_device_deinit("audio_dac")
    ref_count--
    if (ref_count == 0) {
        // 所有使用者都已释放，真正去初始化
        deinit(device_handle);
    }
```

---

## 5. 用户使用设备的方式

### 5.1 典型使用流程

```
┌─────────────────────────────────────────────────────────────────┐
│                     用户使用设备流程                              │
└─────────────────────────────────────────────────────────────────┘

┌─────────────────────────────────────────────────────────────────┐
│ Step 1: 调用 esp_board_manager_init()                           │
│         (在 app_main 开始时调用一次)                             │
└─────────────────────────────────────────────────────────────────┘
                            │
                            ▼
┌─────────────────────────────────────────────────────────────────┐
│ Step 2: 获取设备句柄                                             │
│                                                                 │
│  // 获取 LCD 句柄                                                │
│  dev_display_lcd_handles_t *lcd_handle;                         │
│  esp_board_manager_get_device_handle("display_lcd", &lcd_handle);│
│                                                                 │
│  // 获取音频 codec 句柄                                          │
│  dev_audio_codec_handles_t *audio_handle;                       │
│  esp_board_manager_get_device_handle("audio_dac", &audio_handle);│
└─────────────────────────────────────────────────────────────────┘
                            │
                            ▼
┌─────────────────────────────────────────────────────────────────┐
│ Step 3: 使用设备标准 API                                         │
│                                                                 │
│  // LCD 使用 (通过 esp_lcd_panel_ops.h 接口)                     │
│  esp_lcd_panel_draw_bitmap(lcd_handle->panel_handle, ...);       │
│                                                                 │
│  // 音频使用 (通过 esp_codec_dev.h 接口)                          │
│  esp_codec_dev_open(audio_handle->codec_dev, &fs);               │
│  esp_codec_dev_write(audio_handle->codec_dev, data, size);       │
└─────────────────────────────────────────────────────────────────┘
```

### 5.2 设备句柄结构示例

#### dev_audio_codec_handles_t (音频设备)

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

#### dev_display_lcd_handles_t (LCD 设备)

```c
typedef struct {
    esp_lcd_panel_handle_t panel_handle;  // LCD 面板句柄
    esp_lcd_panel_io_handle_t io_handle; // LCD IO 句柄
    void *priv;                          // 私有数据
} dev_display_lcd_handles_t;
```

### 5.3 设备使用代码示例

#### LCD 显示使用

```c
// 获取 LCD 句柄
dev_display_lcd_handles_t *lcd_handle;
esp_board_manager_get_device_handle("display_lcd", (void **)&lcd_handle);

// 使用标准 esp_lcd API
uint16_t *color_data = /* 颜色数据 */;
esp_lcd_panel_draw_bitmap(lcd_handle->panel_handle,
                          0, 0,        // 起始坐标
                          1024, 600,   // 尺寸
                          color_data); // 颜色数据
```

#### 音频录制使用

```c
// 获取 ADC 句柄
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
esp_codec_dev_read(adc_handle->codec_dev, buffer, sizeof(buffer));
```

---

## 6. 同类型设备的处理机制

### 6.1 设备子类型分发

Board Manager 通过 `sub_type` 字段支持同一设备类型的不同实现：

```c
// dev_display_lcd.c 中的子类型分发逻辑
int dev_display_lcd_init(void *cfg, int cfg_size, void **device_handle)
{
    const dev_display_lcd_config_t *config = (const dev_display_lcd_config_t *)cfg;

    // 通过 sub_type 查找对应的初始化函数
    const esp_board_entry_desc_t *entry_desc = esp_board_entry_find_desc(config->sub_type);

    if (entry_desc == NULL) {
        ESP_LOGE(TAG, "Failed to find sub device: %s", config->sub_type);
        return -1;
    }

    // 调用对应子类型的初始化函数
    return entry_desc->init_func(config, cfg_size, device_handle);
}
```

### 6.2 LCD不同接口类型处理

```
┌─────────────────────────────────────────────────────────────────┐
│                display_lcd 设备子类型分发                        │
└─────────────────────────────────────────────────────────────────┘

                    board_devices.yaml 中定义：
                    sub_type: dsi

                           │
                           ▼
┌─────────────────────────────────────────────────────────────────┐
│  esp_board_entry_find_desc("dsi")                               │
│                                                                 │
│  返回 esp_board_entry_desc_t {                                  │
│      .init_func = dev_display_lcd_sub_dsi_init,                 │
│      .deinit_func = dev_display_lcd_sub_dsi_deinit,             │
│      ...                                                        │
│  }                                                              │
└─────────────────────────────────────────────────────────────────┘
                           │
                           ▼
┌─────────────────────────────────────────────────────────────────┐
│  dev_display_lcd_sub_dsi_init()                                 │
│                                                                 │
│  1. 解析 DSI 特有配置 (bus_id, data_lanes, lane_bit_rate)      │
│  2. 调用 esp_lcd_new_panel_dsi_bus() 创建 DSI 总线              │
│  3. 调用 esp_lcd_new_panel_ek79007() 创建设备 (特定 IC 驱动)     │
│  4. 返回 dev_display_lcd_handles_t 句柄                          │
└─────────────────────────────────────────────────────────────────┘
```

### 6.3 不同驱动IC的处理

Board Manager 支持同一接口类型但不同驱动IC的情况：

```yaml
# board_devices.yaml 中可以定义多个 LCD 设备，使用不同的 chip 字段

devices:
  # DSI 接口 + EK79007 驱动 IC
  - name: display_lcd_ek79007
    chip: ek79007
    type: display_lcd
    sub_type: dsi
    dependencies:
      espressif/esp_lcd_ek79007: "^1.0.0"
    config:
      # EK79007 特有配置

  # DSI 接口 + ST7701 驱动 IC
  - name: display_lcd_st7701
    chip: st7701
    type: display_lcd
    sub_type: dsi
    dependencies:
      espressif/esp_lcd_st7701: "^1.0.0"
    config:
      # ST7701 特有配置
```

### 6.4 外设多实例处理

```yaml
# board_peripherals.yaml

peripherals:
  # I2C 实例 0 - 用于连接 Audio Codec
  - name: i2c_master_audio
    type: i2c
    role: master
    config:
      port: 0
      pins:
        sda: 7
        scl: 8

  # I2C 实例 1 - 用于连接 Touch 芯片
  - name: i2c_master_touch
    type: i2c
    role: master
    config:
      port: 1
      pins:
        sda: 15
        scl: 16

  # I2S 实例 0 - 用于音频输出
  - name: i2s_audio_out
    type: i2s
    format: "std-out"
    role: master
    config:
      port: 0
      # ...

  # I2S 实例 1 - 用于音频输入
  - name: i2s_audio_in
    type: i2s
    format: "std-in"
    role: master
    config:
      port: 1
      # ...
```

### 6.5 设备继承与覆写机制

```yaml
# 设备可以覆写其依赖的外设配置

devices:
  - name: audio_dac
    chip: es8311
    type: audio_codec
    peripherals:
      # 覆写 i2c_master 的地址和频率
      - name: i2c_master
        address: 0x30          # 覆写外设配置
        frequency: 400000       # 覆写外设配置

      # 使用完整外设配置
      - name: i2s_audio_out
```

---

## 7. LCD驱动IC查找与调用

### 7.1 驱动组件位置

**EK79007 驱动组件**：
```
managed_components/espressif__esp_lcd_ek79007/
├── esp_lcd_ek79007.c          # 驱动实现
├── include/esp_lcd_ek79007.h   # 驱动头文件
└── test_apps/                  # 测试程序
```

**核心API**：
```c
esp_err_t esp_lcd_new_panel_ek79007(
    const esp_lcd_panel_io_handle_t io,
    const esp_lcd_panel_dev_config_t *panel_dev_config,
    esp_lcd_panel_handle_t *ret_panel
);
```

### 7.2 驱动调用流程

```
用户应用
    │
    ▼
esp_board_manager_init()
    │
    └─> dev_display_lcd_init()
            │
            │ 根据 sub_type 分发
            ▼
        dev_display_lcd_sub_dsi_init()  [DSI接口]
            │
            │ 调用工厂函数
            ▼
        lcd_dsi_panel_factory_entry_t()
            │
            │ 根据 chip 字段选择驱动
            ▼
        esp_lcd_new_panel_ek79007()  ← 最终调用驱动
```

### 7.3 配置文件中的驱动选择

在 `board_devices.yaml` 中配置：

```yaml
devices:
  - name: display_lcd
    chip: ek79007           # ← 选择驱动IC
    type: display_lcd
    sub_type: dsi           # ← 选择接口类型
    config:
      reset_gpio_num: 27
      bits_per_pixel: 24
      sub_cfg:
        dsi:
          ldo_name: ldo_mipi
          dsi_name: dsi_display
          dpi_config:
            dpi_clock_freq_mhz: 48
            video_timing:
              h_size: 1024
              v_size: 600
```

### 7.4 工厂函数实现

```c
esp_err_t lcd_dsi_panel_factory_entry_t(
    esp_lcd_dsi_bus_handle_t dsi_handle,
    dev_display_lcd_config_t *lcd_cfg,
    dev_display_lcd_handles_t *lcd_handles
)
{
    // 根据 chip 字段选择不同驱动
    if (strcmp(lcd_cfg->chip, "ek79007") == 0) {
        // EK79007 驱动配置
        ek79007_vendor_config_t vendor_config = {
            .mipi_config = {
                .dsi_bus = dsi_handle,
                .dpi_config = &lcd_cfg->sub_cfg.dsi.dpi_config,
            },
        };

        esp_lcd_panel_dev_config_t lcd_dev_config = {
            .reset_gpio_num = lcd_cfg->sub_cfg.dsi.reset_gpio_num,
            .bits_per_pixel = lcd_cfg->bits_per_pixel,
            .vendor_config = &vendor_config,
        };

        return esp_lcd_new_panel_ek79007(
            lcd_handles->io_handle,
            &lcd_dev_config,
            &lcd_handles->panel_handle
        );
    }
    else if (strcmp(lcd_cfg->chip, "st7701") == 0) {
        // ST7701 驱动配置 (需要添加 st7701 驱动组件)
        // st7701_vendor_config_t vendor_config = {...};
        // return esp_lcd_new_panel_st7701(...);
    }

    return ESP_ERR_NOT_SUPPORTED;
}
```

### 7.5 添加新驱动IC的步骤

**步骤 1**：添加驱动组件依赖到 `idf_component.yml`

```yaml
dependencies:
  espressif/esp_lcd_ek79007: "^1.0.0"
  # espressif/esp_lcd_st7701: "^1.0.0"  # 如果需要 ST7701
```

**步骤 2**：在 `setup_device.c` 中添加工厂函数分支

```c
#include "esp_lcd_st7701.h"  // 添加新驱动头文件

esp_err_t lcd_dsi_panel_factory_entry_t(...)
{
    if (strcmp(lcd_cfg->chip, "ek79007") == 0) {
        // EK79007 处理
    }
    else if (strcmp(lcd_cfg->chip, "st7701") == 0) {
        // ST7701 处理
        st7701_vendor_config_t vendor_config = {
            .mipi_config = {
                .dsi_bus = dsi_handle,
                .dpi_config = &lcd_cfg->sub_cfg.dsi.dpi_config,
            },
        };

        esp_lcd_panel_dev_config_t lcd_dev_config = {
            .reset_gpio_num = lcd_cfg->sub_cfg.dsi.reset_gpio_num,
            .bits_per_pixel = lcd_cfg->bits_per_pixel,
            .vendor_config = &vendor_config,
        };

        return esp_lcd_new_panel_st7701(
            lcd_handles->io_handle,
            &lcd_dev_config,
            &lcd_handles->panel_handle
        );
    }
}
```

**步骤 3**：在 `board_devices.yaml` 中配置

```yaml
devices:
  - name: display_lcd
    chip: st7701           # 切换为 ST7701
    type: display_lcd
    sub_type: dsi
    # ... 其他配置
```

### 7.6 直接调用驱动

如果需要直接调用驱动而不通过 board manager：

```c
#include "esp_lcd_ek79007.h"
#include "esp_lcd_mipi_dsi.h"

void app_main(void)
{
    // 1. 创建 DSI 总线
    esp_lcd_dsi_bus_handle_t dsi_bus;
    esp_lcd_dsi_bus_config_t dsi_config = EK79007_PANEL_BUS_DSI_2CH_CONFIG();
    esp_lcd_new_dsi_bus(&dsi_config, &dsi_bus);

    // 2. 创建 DBI IO
    esp_lcd_panel_io_handle_t io_handle;
    esp_lcd_dbi_io_config_t dbi_config = EK79007_PANEL_IO_DBI_CONFIG();
    esp_lcd_new_panel_io_dbi(dsi_bus, &dbi_config, &io_handle);

    // 3. 配置驱动
    ek79007_vendor_config_t vendor_config = {
        .mipi_config = {
            .dsi_bus = dsi_bus,
            .dpi_config = &(esp_lcd_dpi_panel_config_t){
                .dpi_clock_freq_mhz = 52,
                .pixel_format = LCD_PIXEL_FORMAT_RGB888,
                .video_timing = {
                    .h_size = 1024,
                    .v_size = 600,
                },
            },
        },
    };

    esp_lcd_panel_dev_config_t panel_config = {
        .reset_gpio_num = 27,
        .bits_per_pixel = 24,
        .vendor_config = &vendor_config,
    };

    // 4. 创建面板
    esp_lcd_panel_handle_t panel_handle;
    esp_lcd_new_panel_ek79007(io_handle, &panel_config, &panel_handle);

    // 5. 初始化面板
    esp_lcd_panel_init(panel_handle);
    esp_lcd_panel_disp_on_off(panel_handle, true);
}
```

### 7.7 支持的驱动IC列表

| 驱动IC | 组件名称 | 头文件 | 初始化函数 |
|--------|----------|--------|------------|
| EK79007 | `espressif__esp_lcd_ek79007` | `esp_lcd_ek79007.h` | `esp_lcd_new_panel_ek79007()` |
| ST7701 | `espressif__esp_lcd_st7701` | `esp_lcd_st7701.h` | `esp_lcd_new_panel_st7701()` |
| NT35521 | `espressif__esp_lcd_nt35521` | `esp_lcd_nt35521.h` | `esp_lcd_new_panel_nt35521()` |

### 7.8 ESP-LCD 组件层次与调用关系

#### ESP-LCD 组件的 5 层架构：

**Level 4 - 用户应用层**
- 通过 `esp_board_manager_get_device_handle()` 获取句柄
- 直接调用 `esp_lcd_panel_*` API

**Level 3 - Board Manager 设备层**
- `dev_display_lcd_init()` 初始化
- 内部调用 `esp_lcd_panel_reset/init/mirror/disp_on_off`
- 返回 `dev_display_lcd_handles_t` 结构

**Level 2.5 - 具体驱动IC包装层**
- `esp_lcd_new_panel_ek79007()` 核心实现
- **关键机制**：保存原始函数指针 + 重写/包装钩子函数
- `panel_ek79007_init()`: 先发送IC初始化命令，再调用原始DPI init

**Level 2 - ESP-LCD Panel IO 层**
- `esp_lcd_panel_io_tx_param()` 发送IC命令
- `esp_lcd_panel_io_tx_color()` 发送颜色数据

**Level 1 - ESP-LCD 核心 Panel 层**
- `esp_lcd_panel_t` 结构定义完整操作接口
- 统一的 `esp_lcd_panel_*` API

**Level 0 - 硬件驱动层**
- DSI/MIPI、SPI、GPIO 驱动

#### 关键点：Hook 机制（函数包装）

```c
// EK79007 驱动内部实现
esp_lcd_new_panel_ek79007() {
    // 1. 先创建基础 DPI 面板
    esp_lcd_new_panel_dpi(..., ret_panel);

    // 2. 保存原始函数指针
    ek79007->del = (*ret_panel)->del;
    ek79007->init = (*ret_panel)->init;

    // 3. 重写钩子函数（Wrapper）
    (*ret_panel)->del = panel_ek79007_del;   // 覆盖
    (*ret_panel)->init = panel_ek79007_init;  // 覆盖
    (*ret_panel)->user_data = ek79007;        // 私有数据
}
```

#### 用户实际调用时的流向：

| API 调用 | 实际流向 |
|---------|---------|
| `esp_lcd_panel_draw_bitmap()` | 直接调用 core panel 层（未被 EK79007 重写） |
| `esp_lcd_panel_mirror()` | → `panel_ek79007_mirror()` 钩子 → `esp_lcd_panel_io_tx_param()` |
| `esp_lcd_panel_init()` | → `panel_ek79007_init()` 钩子 → 发送 IC 初始化命令 → 原始 DPI init |

---

## 附录：架构图汇总

### A.1 整体架构图

```
┌─────────────────────────────────────────────────────────────────┐
│                      Application Layer                          │
│                 (您的应用程序 / examples)                        │
└─────────────────────────────────────────────────────────────────┘
                            │
                            ▼
┌─────────────────────────────────────────────────────────────────┐
│                  ESP Board Manager Layer                       │
│                                                                 │
│  ┌──────────────┐  ┌──────────────┐  ┌──────────────┐          │
│  │    顶层API    │  │   设备管理层  │  │   外设管理层  │          │
│  │ esp_board_   │  │ esp_board_   │  │ esp_board_   │          │
│  │ manager_*.h  │  │ device_*.h   │  │ periph_*.h   │          │
│  └──────────────┘  └──────────────┘  └──────────────┘          │
│                                                                 │
│  ┌────────────────────────────────────────────────────────────┐ │
│  │                    配置文件 (boards/)                       │ │
│  │  board_info.yaml / board_devices.yaml / board_peripherals │ │
│  └────────────────────────────────────────────────────────────┘ │
└─────────────────────────────────────────────────────────────────┘
                            │
                            ▼
┌─────────────────────────────────────────────────────────────────┐
│                     Device Implementations                      │
│  ┌─────────────┐  ┌─────────────┐  ┌─────────────┐               │
│  │  dev_audio │  │  dev_       │  │   dev_      │               │
│  │  _codec    │  │  display_   │  │   camera    │               │
│  │             │  │  lcd       │  │             │               │
│  └─────────────┘  └─────────────┘  └─────────────┘               │
│  ┌─────────────┐  ┌─────────────┐  ┌─────────────┐               │
│  │  dev_fs_   │  │  dev_       │  │   dev_      │               │
│  │  fat       │  │  button     │  │   gpio_ctrl │               │
│  └─────────────┘  └─────────────┘  └─────────────┘               │
└─────────────────────────────────────────────────────────────────┘
                            │
                            ▼
┌─────────────────────────────────────────────────────────────────┐
│                   Peripheral Implementations                    │
│  ┌─────────────┐  ┌─────────────┐  ┌─────────────┐               │
│  │  periph_   │  │  periph_    │  │  periph_    │               │
│  │  i2c       │  │  i2s        │  │  spi        │               │
│  └─────────────┘  └─────────────┘  └─────────────┘               │
│  ┌─────────────┐  ┌─────────────┐  ┌─────────────┐               │
│  │  periph_   │  │  periph_    │  │  periph_    │               │
│  │  gpio      │  │  ledc       │  │  dsi        │               │
│  └─────────────┘  └─────────────┘  └─────────────┘               │
└─────────────────────────────────────────────────────────────────┘
                            │
                            ▼
┌─────────────────────────────────────────────────────────────────┐
│                      ESP-IDF Drivers                           │
│         driver/gpio.h / driver/i2c.h / driver/spi.h ...        │
└─────────────────────────────────────────────────────────────────┘
```

### A.2 数据流图

```
用户应用
    │
    │ esp_board_manager_init()
    ├──────────────────────────────────────────────────────────────────▶
    │
    │
    │ esp_board_manager_get_device_handle()
    ├──────────────────────────────────────────────────────────────────▶
    │
    │
    │ esp_codec_dev_open()
    ├──────────────────────────────────────────────────────────────────▶
    │
    │
    │ (直接调用设备实现API)
    ├──────────────────────────────────────────────────────────────────▶
    │
```
