# ESP Board Manager 技术文档

## 目录

### 技术文档

- [1. 组件架构概述](board_manager.md#1-组件架构概述)
  - [1.1 系统定位](board_manager.md#11-系统定位)
  - [1.2 核心设计理念](board_manager.md#12-核心设计理念)
  - [1.3 配置驱动的生成流程](board_manager.md#13-配置驱动的生成流程)

- [2. 核心数据结构](board_manager.md#2-核心数据结构)
  - [2.1 设备相关结构体](board_manager.md#21-设备相关结构体)
  - [2.2 外设相关结构体](board_manager.md#22-外设相关结构体)
  - [2.3 板级信息结构体](board_manager.md#23-板级信息结构体)
  - [2.4 初始化函数类型定义](board_manager.md#24-初始化函数类型定义)

- [3. 顶层API管理机制](board_manager.md#3-顶层api管理机制)
  - [3.1 主要API函数](board_manager.md#31-主要api函数)
  - [3.2 API调用流程图](board_manager.md#32-api调用流程图)

- [4. 设备和外设的配置初始化](board_manager.md#4-设备和外设的配置初始化)
  - [4.1 YAML配置文件结构](board_manager.md#41-yaml配置文件结构)
  - [4.2 初始化时序图](board_manager.md#42-初始化时序图)
  - [4.3 引用计数机制](board_manager.md#43-引用计数机制)

- [5. 用户使用设备的方式](board_manager.md#5-用户使用设备的方式)
  - [5.1 典型使用流程](board_manager.md#51-典型使用流程)
  - [5.2 设备句柄结构示例](board_manager.md#52-设备句柄结构示例)
  - [5.3 设备使用代码示例](board_manager.md#53-设备使用代码示例)

- [6. 同类型设备的处理机制](board_manager.md#6-同类型设备的处理机制)
  - [6.1 设备子类型分发](board_manager.md#61-设备子类型分发)
  - [6.2 LCD不同接口类型处理](board_manager.md#62-lcd不同接口类型处理)
  - [6.3 不同驱动IC的处理](board_manager.md#63-不同驱动ic的处理)
  - [6.4 外设多实例处理](board_manager.md#64-外设多实例处理)
  - [6.5 设备继承与覆写机制](board_manager.md#65-设备继承与覆写机制)

- [7. LCD驱动IC查找与调用](board_manager.md#7-lcd驱动ic查找与调用)
  - [7.1 驱动组件位置](board_manager.md#71-驱动组件位置)
  - [7.2 驱动调用流程](board_manager.md#72-驱动调用流程)
  - [7.3 配置文件中的驱动选择](board_manager.md#73-配置文件中的驱动选择)
  - [7.4 工厂函数实现](board_manager.md#74-工厂函数实现)
  - [7.5 添加新驱动IC的步骤](board_manager.md#75-添加新驱动ic的步骤)
  - [7.6 直接调用驱动](board_manager.md#76-直接调用驱动)
  - [7.7 支持的驱动IC列表](board_manager.md#77-支持的驱动ic列表)
  - [7.8 ESP-LCD 组件层次与调用关系](board_manager.md#78-esp-lcd-组件层次与调用关系)

- [8. LCD初始化完整流程](board_manager.md#8-lcd初始化完整流程)
  - [8.1 整体调用流程图](board_manager.md#81-整体调用流程图)
  - [8.2 阶段详细分析](board_manager.md#82-阶段详细分析)
  - [8.3 完整数据结构流转图](board_manager.md#83-完整数据结构流转图)
  - [8.4 关键API功能汇总](board_manager.md#84-关键api功能汇总)
  - [8.5 设计亮点总结](board_manager.md#85-设计亮点总结)

- [附录：架构图汇总](board_manager.md#附录架构图汇总)
  - [A.1 整体架构图](board_manager.md#a1-整体架构图)
  - [A.2 数据流图](board_manager.md#a2-数据流图)

---

### LCD 专项文档

- [LCD 初始化流程与 EK79007 驱动使用指南](ek79007初始化.md) - 详细介绍从板级初始化到 EK79007 驱动的完整流程

---

### 官方中文文档

- [README_CN.md](official_docs/README_CN.md) - 组件中文介绍文档
- [快速入门指南](official_docs/ESP_Board_Manager_Quick_Start_CN_v1.1.pdf) - PDF 格式快速入门
- [板级配置模板](official_docs/board_config_template_cn.md) - 详细的中文配置指南
- [设备和外设配置规则](official_docs/device_and_peripheral_rules_cn.md) - 配置规则详解
- [自定义开发板指南](official_docs/how_to_customize_board_cn.md) - 自定义开发板指南

---

### 示例项目文档

- [播放SD卡音乐](examples/play_sdcard_music.md) - play_sdcard_music 示例
- [录制到SD卡](examples/record_to_sdcard.md) - record_to_sdcard 示例
- [播放嵌入音乐](examples/play_embed_music.md) - play_embed_music 示例
- [录音播放](examples/record_and_play.md) - record_and_play 示例
