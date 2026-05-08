#!/usr/bin/env python3

with open('index.md', 'r') as f:
    lines = f.readlines()

# 找到 "### 1.3 配置驱动的生成流程" 的位置
start_line = None
end_line = None

for i, line in enumerate(lines):
    if '### 1.3 配置驱动的生成流程' in line:
        start_line = i
    elif start_line is not None and '---' in line and i > start_line:
        end_line = i
        break

if start_line is None or end_line is None:
    print("Section not found")
    exit(1)

# 创建新内容
new_content = []

# 添加标题
new_content.append(lines[start_line])
new_content.append('\n')

# 添加阶段1：开发板配置
new_content.append('#### 阶段1：开发板配置\n')
new_content.append('\n')
new_content.append('```mermaid\n')
new_content.append('flowchart TD\n')
new_content.append('    A[boards/&lt;board_name&gt;/]\n')
new_content.append('    A --> A1[board_info.yaml\\n板级基本信息]\n')
new_content.append('    A --> A2[board_peripherals.yaml\\n外设配置]\n')
new_content.append('    A --> A3[board_devices.yaml\\n设备配置]\n')
new_content.append('    A --> A4[setup_device.c\\n可选自定义初始化代码]\n')
new_content.append('    A -->|输出| B[YAML 配置文件]\n')
new_content.append('```\n')
new_content.append('\n')

# 添加阶段2：代码生成
new_content.append('#### 阶段2：代码生成 (CMake阶段)\n')
new_content.append('\n')
new_content.append('```mermaid\n')
new_content.append('flowchart TD\n')
new_content.append('    A[YAML 配置文件] --> B[gen_bmgr_config_codes.py]\n')
new_content.append('    B --> B1[device_parser.py\\n解析设备配置]\n')
new_content.append('    B --> B2[peripheral_parser.py\\n解析外设配置]\n')
new_content.append('    B --> B3[config_generator.py\\n生成代码]\n')
new_content.append('    B --> C[生成中间产物]\n')
new_content.append('    C --> C1[解析 YAML 配置]\n')
new_content.append('    C --> C2[生成 C 结构体]\n')
new_content.append('    C --> C3[输出头文件]\n')
new_content.append('```\n')
new_content.append('\n')

# 添加阶段3：编译阶段
new_content.append('#### 阶段3：编译阶段\n')
new_content.append('\n')
new_content.append('```mermaid\n')
new_content.append('flowchart TD\n')
new_content.append('    A[生成的头文件] --> B[编译阶段]\n')
new_content.append('    B --> B1[gen_board_device_handles.c\\n设备注册表]\n')
new_content.append('    B --> B2[gen_board_periph_handles.c\\n外设注册表]\n')
new_content.append('    B --> B3[board_info.c\\n板级信息]\n')
new_content.append('    B --> C[最终输出]\n')
new_content.append('    C --> C1[设备句柄数组]\n')
new_content.append('    C --> C2[外设句柄数组]\n')
new_content.append('    C --> C3[板级信息结构体]\n')
new_content.append('```\n')
new_content.append('\n')

# 添加分割线
new_content.append(lines[end_line])
new_content.append('\n')

# 将新内容写回文件
result = lines[:start_line] + new_content + lines[end_line+1:]

with open('index.md', 'w') as f:
    f.writelines(result)

print("Chart split completed!")
