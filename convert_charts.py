#!/usr/bin/env python3
import re

def convert_to_mermaid(content):
    # 模式1: 系统架构图
    pattern1 = r'```\n┌─────────────────────────────────────────────────────────┐\n│                    Application Layer                      │\n│                   \(用户应用程序\)                          │\n└─────────────────────────────────────────────────────────┘\n                            │\n                            ▼\n┌─────────────────────────────────────────────────────────┐\n│                  ESP Board Manager                       │\n│  ┌─────────────────────────────────────────────────┐    │\n│  │        esp_board_manager.h \(顶层API\)            │    │\n│  └─────────────────────────────────────────────────┘    │\n│                            │                             │\n│        ┌───────────────────┴───────────────────┐        │\n│        ▼                                       ▼        │\n│  ┌─────────────────┐               ┌─────────────────┐ │\n│  │ esp_board_device.h │             │esp_board_periph.h│ │\n│  │   \(设备管理层\)    │               │  \(外设管理层\)    │ │\n│  └────────┬────────┘               └────────┬────────┘ │\n│           │                                  │          │\n└───────────┼──────────────────────────────────┼──────────┘\n            │                                  │\n            ▼                                  ▼\n┌─────────────────────────┐    ┌─────────────────────────┐\n│   Devices \(设备层\)       │    │   Peripherals \(外设层\)  │\n│  - dev_audio_codec      │    │  - periph_i2c           │\n│  - dev_display_lcd      │    │  - periph_i2s           │\n│  - dev_camera           │    │  - periph_spi           │\n│  - dev_fs_fat          │    │  - periph_gpio          │\n│  - dev_button          │    │  - periph_ledc          │\n└─────────────────────────┘    └─────────────────────────┘\n            │                                  │\n            ▼                                  ▼\n┌─────────────────────────────────────────────────────────┐\n│              ESP-IDF Driver Layer                       │\n│         \(driver/gpio, driver/i2c, driver/spi...\)        │\n└─────────────────────────────────────────────────────────┘\n```'
    
    replacement1 = '''```mermaid
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
    
    content = content.replace(pattern1, replacement1)
    
    # 模式2: 配置驱动生成流程图
    pattern2 = r'```\n┌──────────────────────────────────────────────────────────────┐\n│                      开发板配置阶段                           │\n│                                                              │\n│  boards/<board_name>/                                       │\n│  ├── board_info.yaml        \(板级基本信息\)                   │\n│  ├── board_peripherals.yaml \(外设配置\)                       │\n│  ├── board_devices.yaml    \(设备配置\)                       │\n│  └── setup_device.c        \(可选的自定义初始化代码\)          │\n└──────────────────────────────────────────────────────────────┘\n                              │\n                              ▼ \(cmake 阶段调用生成器\)\n┌──────────────────────────────────────────────────────────────┐\n│                      代码生成阶段                            │\n│                                                              │\n│  generators/                   gen_bmgr_config_codes.py     │\n│  ├── device_parser.py         └── 解析 YAML 配置             │\n│  ├── peripheral_parser.py     └── 生成 C 结构体              │\n│  └── config_generator.py     └── 输出头文件                 │\n└──────────────────────────────────────────────────────────────┘\n                              │\n                              ▼\n┌──────────────────────────────────────────────────────────────┐\n│                      编译阶段                                │\n│                                                              │\n│  生成文件：                                                 │\n│  ├── gen_board_device_handles.c  \(设备注册表\)               │\n│  ├── gen_board_periph_handles.c  \(外设注册表\)               │\n│  └── board_info.c               \(板级信息\)                  │\n└──────────────────────────────────────────────────────────────┘\n```'
    
    replacement2 = '''```mermaid
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
    
    content = content.replace(pattern2, replacement2)
    
    return content

# 读取文件
with open('index.md', 'r') as f:
    content = f.read()

# 转换
content = convert_to_mermaid(content)

# 写入文件
with open('index.md', 'w') as f:
    f.write(content)

print("Conversion completed!")
