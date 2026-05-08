#!/usr/bin/env python3
import re

def convert_charts(input_file, output_file):
    with open(input_file, 'r') as f:
        content = f.read()
    
    # 分割成代码块和非代码块
    parts = re.split(r'(```.*?```)', content, flags=re.DOTALL)
    
    result = []
    for part in parts:
        if part.startswith('```') and part.endswith('```'):
            # 这是一个代码块
            inner = part[3:-3].strip()
            if inner.startswith('┌'):
                # 这是一个ASCII图表，需要转换
                result.append(convert_ascii_to_mermaid(inner))
            else:
                # 不是ASCII图表，保持原样
                result.append(part)
        else:
            # 不是代码块，保持原样
            result.append(part)
    
    with open(output_file, 'w') as f:
        f.write(''.join(result))
    
    print(f"Conversion completed!")

def convert_ascii_to_mermaid(ascii_chart):
    lines = ascii_chart.split('\n')
    
    # 分析图表类型
    if 'Application Layer' in ascii_chart and 'ESP Board Manager' in ascii_chart:
        # 系统架构图
        return convert_system_architecture(ascii_chart)
    elif '开发板配置阶段' in ascii_chart and '代码生成阶段' in ascii_chart:
        # 配置驱动生成流程图
        return convert_config_flow(ascii_chart)
    elif 'esp_board_manager_init' in ascii_chart and 'esp_board_periph_init_all' in ascii_chart:
        # API调用流程图
        return convert_api_flow(ascii_chart)
    elif 'Phase 1: 外设初始化' in ascii_chart and 'Phase 2: 设备初始化' in ascii_chart:
        # 初始化时序图
        return convert_init_sequence(ascii_chart)
    elif '用户使用设备流程' in ascii_chart:
        # 用户使用设备流程图
        return convert_user_flow(ascii_chart)
    elif 'display_lcd 设备子类型分发' in ascii_chart:
        # LCD子类型分发图
        return convert_lcd_subtype(ascii_chart)
    elif '用户应用' in ascii_chart and 'esp_board_manager_init' in ascii_chart:
        # 驱动调用流程图
        return convert_driver_flow(ascii_chart)
    elif '整体架构图' in ascii_chart:
        # 整体架构图
        return convert_overall_architecture(ascii_chart)
    elif '数据流图' in ascii_chart:
        # 数据流图
        return convert_dataflow(ascii_chart)
    else:
        # 默认返回原样
        return f"```\n{ascii_chart}\n```"

def convert_system_architecture(chart):
    return '''```mermaid
graph TD
    A[Application Layer\\n用户应用程序] --> B[ESP Board Manager]
    B --> B1[esp_board_manager.h\\n顶层API]
    B1 --> C[设备管理层\\nesp_board_device.h]
    B1 --> D[外设管理层\\nesp_board_periph.h]
    C --> E[Devices 设备层]
    D --> F[Peripherals 外设层]
    E --> E1[dev_audio_codec]
    E --> E2[dev_display_lcd]
    E --> E3[dev_camera]
    E --> E4[dev_fs_fat]
    E --> E5[dev_button]
    F --> F1[periph_i2c]
    F --> F2[periph_i2s]
    F --> F3[periph_spi]
    F --> F4[periph_gpio]
    F --> F5[periph_ledc]
    E --> G[ESP-IDF Driver Layer]
    F --> G
    G --> G1[driver/gpio]
    G --> G2[driver/i2c]
    G --> G3[driver/spi]
```'''

def convert_config_flow(chart):
    return '''```mermaid
flowchart TD
    A[开发板配置阶段] --> A1[boards/&lt;board_name&gt;/]
    A1 --> A2[board_info.yaml\\n板级基本信息]
    A1 --> A3[board_peripherals.yaml\\n外设配置]
    A1 --> A4[board_devices.yaml\\n设备配置]
    A1 --> A5[setup_device.c\\n可选自定义初始化代码]
    
    A -->|cmake阶段调用生成器| B[代码生成阶段]
    B --> B1[generators/]
    B1 --> B2[device_parser.py]
    B1 --> B3[peripheral_parser.py]
    B1 --> B4[config_generator.py]
    B1 --> B5[gen_bmgr_config_codes.py]
    B5 --> B6[解析YAML配置]
    B5 --> B7[生成C结构体]
    B5 --> B8[输出头文件]
    
    B --> C[编译阶段]
    C --> C1[gen_board_device_handles.c\\n设备注册表]
    C --> C2[gen_board_periph_handles.c\\n外设注册表]
    C --> C3[board_info.c\\n板级信息]
```'''

def convert_api_flow(chart):
    return '''```mermaid
flowchart TD
    A[esp_board_manager_init] --> B[esp_board_periph_init_all]
    B --> B1[遍历 g_esp_board_peripherals]
    B1 --> B2[esp_board_periph_init name]
    B2 --> B3[查找外设描述符\\n通过name在链表中查找]
    B3 --> B4[查找外设条目\\n通过type+role匹配init函数]
    B4 --> B5[调用 init cfg cfg_size handle]
    B5 --> B6[创建外设列表节点，加入链表]
    B6 --> B7[ref_count++]
    
    B7 --> C[esp_board_device_init_all]
    C --> C1[遍历 g_esp_board_devices]
    C1 --> C2[esp_board_device_init name]
    C2 --> C3[查找设备描述符\\n通过name在链表中查找]
    C3 --> C4[检查电源依赖\\npower_ctrl_device]
    C4 --> C5[调用 init cfg cfg_size handle]
    C5 --> C6[创建设备列表节点，加入链表]
    C6 --> C7[ref_count++]
    
    C7 --> D[初始化完成]
    D --> D1[用户获取句柄]
    D1 --> D2[esp_board_manager_get_device_handle\\naudio_dac handle]
    D1 --> D3[esp_board_manager_get_periph_handle\\ni2c_master handle]
```'''

def convert_init_sequence(chart):
    return '''```mermaid
sequenceDiagram
    participant BM as esp_board_manager
    participant PI as esp_board_periph_init_all
    participant DI as esp_board_device_init_all

    BM->>PI: Phase 1: 外设初始化
    Note over PI: 外设1: i2c_master
    PI->>PI: esp_board_periph_init("i2c_master")
    PI->>PI: 查找描述符 (name, type, role)
    PI->>PI: 查找初始化函数 (periph_i2c_init)
    PI->>PI: 调用 init(cfg, cfg_size, handle)
    
    Note over PI: 外设2: i2s_audio_out
    PI->>PI: esp_board_periph_init("i2s_audio_out")
    PI->>PI: 查找描述符 (name, type)
    PI->>PI: 查找初始化函数 (periph_i2s_init)
    PI->>PI: 调用 init(cfg, cfg_size, handle)
    
    Note over PI: 外设3: gpio_pa_control
    PI->>PI: ...
    
    BM->>DI: Phase 2: 设备初始化
    Note over DI: 设备1: lcd_brightness
    DI->>DI: 检查电源依赖 (无)
    DI->>DI: esp_board_device_init("lcd_brightness")
    DI->>DI: 调用 dev_ledc_ctrl_init(cfg, cfg_size, handle)
    
    Note over DI: 设备2: display_lcd
    DI->>DI: 检查电源依赖
    DI->>DI: 先初始化 power_ctrl_device (ldo_mipi)
    DI->>DI: esp_board_device_init("display_lcd")
    DI->>DI: 查找 sub_type="dsi" 的初始化函数
    DI->>DI: 调用 dev_display_lcd_sub_dsi_init(cfg, cfg_size, handle)
    
    Note over DI: 设备3: audio_dac
    DI->>DI: 检查电源依赖 (无)
    DI->>DI: esp_board_device_init("audio_dac")
    DI->>DI: 查找 type="audio_codec" 的初始化函数
    DI->>DI: 调用 dev_audio_codec_init(cfg, cfg_size, handle)
    
    BM->>BM: s_manager_initialized = true
    BM->>BM: ref_count 引用计数管理
```'''

def convert_user_flow(chart):
    return '''```mermaid
flowchart TD
    A[Step 1: 调用 esp_board_manager_init]
    A --> A1[在 app_main 开始时调用一次]
    
    A --> B[Step 2: 获取设备句柄]
    B --> B1[获取 LCD 句柄]
    B1 --> B2[dev_display_lcd_handles_t *lcd_handle]
    B2 --> B3[esp_board_manager_get_device_handle\\ndisplay_lcd lcd_handle]
    B --> B4[获取音频 codec 句柄]
    B4 --> B5[dev_audio_codec_handles_t *audio_handle]
    B5 --> B6[esp_board_manager_get_device_handle\\naudio_dac audio_handle]
    
    B --> C[Step 3: 使用设备标准 API]
    C --> C1[LCD 使用]
    C1 --> C2[esp_lcd_panel_draw_bitmap\\nlcd_handle-panel_handle ...]
    C --> C3[音频使用]
    C3 --> C4[esp_codec_dev_open\\naudio_handle-codec_dev fs]
    C3 --> C5[esp_codec_dev_write\\naudio_handle-codec_dev data size]
```'''

def convert_lcd_subtype(chart):
    return '''```mermaid
flowchart TD
    A[board_devices.yaml] --> A1[sub_type: dsi]
    A1 --> B[esp_board_entry_find_desc dsi]
    B --> B1[返回 esp_board_entry_desc_t]
    B1 --> B2[init_func = dev_display_lcd_sub_dsi_init]
    B1 --> B3[deinit_func = dev_display_lcd_sub_dsi_deinit]
    
    B1 --> C[dev_display_lcd_sub_dsi_init]
    C --> C1[解析 DSI 特有配置\\nbus_id data_lanes lane_bit_rate]
    C1 --> C2[调用 esp_lcd_new_panel_dsi_bus\\n创建 DSI 总线]
    C2 --> C3[调用 esp_lcd_new_panel_ek79007\\n创建设备 特定IC驱动]
    C3 --> C4[返回 dev_display_lcd_handles_t 句柄]
```'''

def convert_driver_flow(chart):
    return '''```mermaid
flowchart TD
    A[用户应用] --> B[esp_board_manager_init]
    B --> C[dev_display_lcd_init]
    C -->|根据 sub_type 分发| D[dev_display_lcd_sub_dsi_init]
    D -->|调用工厂函数| E[lcd_dsi_panel_factory_entry_t]
    E -->|根据 chip 字段选择驱动| F[esp_lcd_new_panel_ek79007]
```'''

def convert_overall_architecture(chart):
    return '''```mermaid
graph TD
    A[Application Layer\\n您的应用程序 / examples] --> B[ESP Board Manager Layer]
    
    B --> B1[顶层API\\nesp_board_manager_*.h]
    B --> B2[设备管理层\\nesp_board_device_*.h]
    B --> B3[外设管理层\\nesp_board_periph_*.h]
    B --> B4[配置文件 boards/\\nboard_info.yaml\\nboard_devices.yaml\\nboard_peripherals.yaml]
    
    B --> C[Device Implementations]
    C --> C1[dev_audio_codec]
    C --> C2[dev_display_lcd]
    C --> C3[dev_camera]
    C --> C4[dev_fs_fat]
    C --> C5[dev_button]
    C --> C6[dev_gpio_ctrl]
    
    B --> D[Peripheral Implementations]
    D --> D1[periph_i2c]
    D --> D2[periph_i2s]
    D --> D3[periph_spi]
    D --> D4[periph_gpio]
    D --> D5[periph_ledc]
    D --> D6[periph_dsi]
    
    C --> E[ESP-IDF Drivers]
    D --> E
    E --> E1[driver/gpio.h]
    E --> E2[driver/i2c.h]
    E --> E3[driver/spi.h]
```'''

def convert_dataflow(chart):
    return '''```mermaid
sequenceDiagram
    participant UserApp as 用户应用
    participant BoardMgr as Board Manager
    participant DeviceImpl as 设备实现

    UserApp->>BoardMgr: esp_board_manager_init()
    BoardMgr->>BoardMgr: 初始化外设和设备

    UserApp->>BoardMgr: esp_board_manager_get_device_handle()
    BoardMgr-->>UserApp: 返回设备句柄

    UserApp->>DeviceImpl: esp_codec_dev_open()
    DeviceImpl->>DeviceImpl: 打开音频设备

    UserApp->>DeviceImpl: 直接调用设备实现API
    DeviceImpl->>DeviceImpl: 执行设备操作
```'''

# 处理 index.md
convert_charts('index.md', 'index.md')

# 处理 lcd_ek79007_guide.md
convert_charts('lcd_ek79007_guide.md', 'lcd_ek79007_guide.md')
