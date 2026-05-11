# Production Planning Optimization 生产计划优化

## Table of Contents 目录

- [Overview 概述](#overview-概述)
- [Features 功能特性](#features-功能特性)
- [Mathematical Model 数学模型](#mathematical-model-数学模型)
- [Prerequisites 前置要求](#prerequisites-前置要求)
- [How to Run 运行方式](#how-to-run-运行方式)
- [Example Usage 使用示例](#example-usage-使用示例)
- [Rush Order Handling 临时插单处理](#rush-order-handling-临时插单处理)
- [Project Structure 项目结构](#project-structure-项目结构)
- [Future Enhancements 未来改进](#future-enhancements-未来改进)
- [License 许可证](#license-许可证)

## Overview 概述

The **Production Optimizer** is a web-based application designed to optimize production scheduling in manufacturing environments using Integer Linear Programming (ILP). Built with Python, Streamlit, PuLP, and Pandas, this tool helps production engineers maximize profits by determining the optimal production schedule while considering machine availability, product demands, and production constraints.

**生产计划优化器**是一个基于 Web 的应用程序，使用整数线性规划（ILP）优化制造环境中的生产调度。该工具使用 Python、Streamlit、PuLP 和 Pandas 构建，帮助生产工程师在考虑机器可用性、产品需求和生产约束的同时最大化利润。

## Features 功能特性

1. **Input Flexibility 输入灵活性**:
   - Support for custom number of products and machines via comma-separated inputs
   - Customizable parameters for products (profit, setup time, min/max batch sizes, demand, penalties, priority)
   - Machine-specific production rates for each product
   - 支持通过逗号分隔输入自定义数量的产品和机器
   - 可自定义产品参数（利润、设置时间、最小/最大批量、需求、惩罚成本、优先级）
   - 支持为每个产品定义特定机器的生产速率

2. **Optimization Model 优化模型**:
   - Utilizes PuLP to formulate and solve an ILP model that maximizes profit
   - Decision variables include batch counts and machine assignments
   - Accounts for unmet demand with penalty costs
   - Supports product priorities and rush orders
   - 使用 PuLP 构建并求解最大化利润的 ILP 模型
   - 决策变量包括批量数量和机器分配
   - 考虑未满足需求的惩罚成本
   - 支持产品优先级和临时插单

3. **Rush Order Support 临时插单支持**:
   - Dynamic rush order handling with configurable priority multiplier
   - Visual indication of rush order impact on original orders
   - Automatic capacity reallocation to prioritize rush orders
   - 动态插单处理，支持可配置的优先级倍数
   - 可视化显示插单对原订单的影响
   - 自动重新分配产能以优先满足插单需求

4. **Interactive UI 交互式界面**:
   - Built with Streamlit for a clean, responsive web interface
   - Dynamic data tables for inputting parameters
   - Bilingual (Chinese/English) interface support
   - 使用 Streamlit 构建简洁响应式的 Web 界面
   - 动态数据表用于输入参数
   - 支持中英文双语界面

5. **Visualization 可视化**:
   - Machine utilization bar charts
   - Production vs demand comparison charts
   - Stacked charts showing original demand vs rush orders
   - Clear result presentation with summaries
   - 机器利用率柱状图
   - 产量对比需求图表
   - 堆叠图表展示原订单与插单对比
   - 清晰的结果展示和摘要

6. **Data Persistence 数据持久化**:
   - Save and load configurations
   - Example data for quick testing
   - 保存和加载配置
   - 示例数据用于快速测试

7. **Input Validation 输入验证**:
   - Comprehensive validation for all input parameters
   - Real-time error feedback
   - 全面的输入参数验证
   - 实时错误反馈

## Mathematical Model 数学模型

### Decision Variables 决策变量

- $x_{p,m,b}$: Number of batches of product $p$ on machine $m$ with batch type $b$
- $y_{p,m,b}$: Binary variable (1 if product $p$ is assigned to machine $m$ with batch type $b$)
- $u_p$: Unmet demand for product $p$
- $u^r_p$: Unmet rush order for product $p$

### Objective Function 目标函数

Maximize total profit with priority and rush order support:

$\max Z = \sum_{p \in P} \left[ \text{Priority}_p \cdot \text{Profit}_p \cdot \sum_{m \in M} \sum_{b \in B} x_{p,m,b} \cdot \text{BatchSize}_{p,b} - \text{Penalty}_p \cdot u_p - \text{Penalty}_p \cdot \text{RushMultiplier} \cdot u^r_p \right] - \sum_{m \in M} \sum_{p \in P} \sum_{b \in B} \text{Maintenance}_m \cdot y_{p,m,b}$

### Constraints 约束条件

1. **Machine Assignment**: Each machine can produce at most one product per day
2. **Machine Time**: Total time (production + setup) ≤ available hours
3. **Batch Type Exclusivity**: At most one batch type per product-machine pair
4. **Demand Satisfaction**: Production + unmet demand = total demand (original + rush)
5. **Rush Order Priority**: Production ≥ rush order quantity (when rush orders exist)

## Prerequisites 前置要求

- **Python**: Version 3.8 or higher
- **Required Libraries**:
  - `streamlit`: Web interface
  - `pulp`: ILP solver
  - `pandas`: Data handling
  - `plotly`: Visualization

Install dependencies:
```bash
pip install -r requirements.txt
```

## How to Run 运行方式

1. **Clone the Repository 克隆仓库**:
   ```bash
   git clone https://github.com/skytodmoon/Production-Planning-Optimization.git
   cd Production-Planning-Optimization
   ```

2. **Install Dependencies 安装依赖**:
   ```bash
   pip install -r requirements.txt
   ```

3. **Run the Application 运行应用**:
   ```bash
   streamlit run app.py
   ```

4. **Using the Application 使用应用**:
   - **Step 1**: Enter machine and product names
   - **Step 2**: Input product parameters (including priority)
   - **Step 3**: Define machine parameters
   - **Step 4**: Set production rates
   - **Step 5**: Enable rush orders (optional) and set quantities
   - **Step 6**: Click "Optimize Production"
   - **步骤1**: 输入机器和产品名称
   - **步骤2**: 输入产品参数（包括优先级）
   - **步骤3**: 定义机器参数
   - **步骤4**: 设置生产速率
   - **步骤5**: 启用插单功能（可选）并设置数量
   - **步骤6**: 点击"优化生产计划"

## Example Usage 使用示例

### Scenario 1: Normal Operations 正常运营场景

**Input 输入**:
- Machines: `W, X, Y, Z`
- Products: `A, B, C`

**Product Parameters 产品参数**:
| Product | Profit | Setup Time | Min Batch | Max Batch | Demand | Penalty | Priority |
|---------|--------|------------|-----------|-----------|--------|---------|----------|
| A | $100 | 30 min | 5 | 20 | 150 | $50 | 1.0 |
| B | $80 | 20 min | 8 | 30 | 330 | $40 | 1.0 |
| C | $120 | 25 min | 4 | 15 | 150 | $60 | 1.0 |

**Machine Parameters 机器参数**:
| Machine | Available Hours | Maintenance Cost |
|---------|-----------------|------------------|
| W | 8 | $100 |
| X | 12 | $150 |
| Y | 10 | $120 |
| Z | 9 | $110 |

**Output 输出**:
- Status: Optimal
- Total Profit: $43,820

### Quick Start 快速开始

Click **"Load Example Data"** button to load pre-configured example data and test the optimization immediately.

点击 **"加载示例数据"** 按钮加载预设的示例数据，立即测试优化功能。

## Rush Order Handling 临时插单处理

### How It Works 工作原理

When rush orders are enabled, the system:
1. Adds rush order quantities to the total demand
2. Applies a configurable priority multiplier to rush orders
3. Prioritizes rush orders over regular orders
4. Shows the impact on original orders

启用插单功能时，系统会：
1. 将插单数量添加到总需求中
2. 对插单应用可配置的优先级倍数
3. 优先满足插单需求
4. 显示对原订单的影响

### Example: Handling Rush Orders 插单示例

**Scenario**: After planning production for Products A, B, C, a rush order for 50 units of Product A arrives.

**场景**: 在为产品 A、B、C 制定生产计划后，收到产品 A 的紧急插单 50 单位。

**Steps 步骤**:
1. Enable "Rush Orders" checkbox
2. Set "Rush Priority Multiplier" to 2.0
3. Enter 50 in the "Rush Quantity" field for Product A
4. Click "Optimize Production"

**Expected Results 预期结果**:
- The system will prioritize the 50-unit rush order for Product A
- The original demand may be partially unmet if capacity is limited
- The results will show:
  - Rush order satisfaction status
  - Impact on original orders
  - Updated production schedule

### Priority Multiplier 优先级倍数

The rush priority multiplier determines how much priority rush orders get:
- **1.0**: No priority boost (same as regular orders)
- **2.0**: Double priority (rush orders are twice as important)
- **5.0**: Maximum priority boost

插单优先级倍数决定插单获得的优先程度：
- **1.0**: 无优先级提升（与普通订单相同）
- **2.0**: 双倍优先级（插单重要性是普通订单的两倍）
- **5.0**: 最大优先级提升

## Project Structure 项目结构

```
Production-Planning-Optimization/
├── app.py              # Frontend Streamlit application with rush order UI
├── Backend.py          # ILP model solver with priority and rush order support
├── requirements.txt    # Required Python libraries
├── Logo.png            # Application logo
└── README.markdown     # Project documentation
```

## Future Enhancements 未来改进

- [ ] Advanced constraints (labor, storage limits)
- [ ] Gantt chart visualization for production schedules
- [ ] API integration for real-time data input
- [ ] Multi-period planning support
- [ ] What-if scenario comparison
- [ ] 高级约束（劳动力、存储限制）
- [ ] 生产调度甘特图可视化
- [ ] API 集成支持实时数据输入
- [ ] 多周期规划支持
- [ ] 场景对比分析

## License 许可证

This project is licensed under the MIT License. See the LICENSE file for details.