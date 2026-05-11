# Core Technical Principles 核心技术原理

## Table of Contents 目录

- [Overview 概述](#overview-概述)
- [Mathematical Model 数学模型](#mathematical-model-数学模型)
- [Technical Implementation 技术实现](#technical-implementation-技术实现)
- [Algorithm Flow 算法流程](#algorithm-flow-算法流程)
- [Key Advantages 核心优势](#key-advantages-核心优势)
- [Application Scenarios 应用场景](#application-scenarios-应用场景)
- [Technology Stack 技术栈](#technology-stack-技术栈)

---

## Overview 概述

This project uses **Integer Linear Programming (ILP)** to solve optimal production scheduling problems. ILP is a mathematical optimization method that maximizes (or minimizes) a linear objective function subject to a set of linear constraints.

本项目使用 **整数线性规划（ILP）** 来求解最优生产调度方案。ILP 是一种数学优化方法，在满足一系列线性约束条件下，最大化（或最小化）一个线性目标函数。

---

## Mathematical Model 数学模型

### 1. Decision Variables 决策变量

| Variable 变量 | Type 类型 | Description 含义 |
|---------------|-----------|-------------------|
| $x_{p,m,b}$ | Integer 整数 | Number of batches of product $p$ on machine $m$ with batch type $b$ <br> 产品p在机器m上使用批量类型b的批次数 |
| $y_{p,m,b}$ | Binary 二进制 | 1 if product $p$ is assigned to machine $m$ with batch type $b$, 0 otherwise <br> 是否将产品p分配给机器m使用批量类型b |
| $u_p$ | Integer 整数 | Unmet demand for product $p$ <br> 产品p的未满足需求 |
| $u^r_p$ | Integer 整数 | Unmet rush order for product $p$ (extended feature) <br> 产品p的未满足插单需求（扩展功能） |

### 2. Objective Function 目标函数

Maximize total profit with priority and rush order support:

最大化总利润，支持优先级和插单：

$$\max Z = \sum_{p \in P} \left[ \text{Priority}_p \cdot \text{Profit}_p \cdot \sum_{m \in M} \sum_{b \in B} x_{p,m,b} \cdot \text{BatchSize}_{p,b} - \text{Penalty}_p \cdot u_p - \text{Penalty}_p \cdot \text{RushMultiplier} \cdot u^r_p \right] - \sum_{m \in M} \sum_{p \in P} \sum_{b \in B} \text{Maintenance}_m \cdot y_{p,m,b}$$

**Components 组成部分**:

| Component 组件 | Description 描述 |
|----------------|------------------|
| $\text{Priority}_p \cdot \text{Profit}_p \cdot \text{Production}$ | Revenue with priority weight <br> 带优先级权重的收入 |
| $-\text{Penalty}_p \cdot u_p$ | Penalty for unmet regular demand <br> 未满足常规需求的惩罚 |
| $-\text{Penalty}_p \cdot \text{RushMultiplier} \cdot u^r_p$ | Penalty for unmet rush orders (higher priority) <br> 未满足插单的惩罚（更高优先级） |
| $-\text{Maintenance}_m \cdot y_{p,m,b}$ | Machine maintenance cost <br> 机器维护成本 |

### 3. Constraints 约束条件

#### 3.1 Machine Assignment Constraint 机器分配约束

Each machine can produce at most one product per day:

每台机器每天最多生产一种产品：

$$\sum_{p \in P} \sum_{b \in B} y_{p,m,b} \leq 1 \quad \forall m \in M$$

#### 3.2 Machine Time Constraint 机器时间约束

Total time (production + setup) must not exceed available hours:

总时间（生产 + 设置）不能超过可用时间：

$$\sum_{p \in P} \sum_{b \in B} \left( \frac{x_{p,m,b} \cdot \text{BatchSize}_{p,b}}{\text{Rate}_{p,m}} + \text{SetupTime}_p \cdot y_{p,m,b} \right) \leq \text{AvailableHours}_m \quad \forall m \in M$$

#### 3.3 Batch Type Exclusivity Constraint 批量类型排他约束

For each product-machine pair, at most one batch type can be used:

每个产品-机器组合只能使用一种批量类型：

$$y_{p,m,\text{min}} + y_{p,m,\text{max}} \leq 1 \quad \forall (p,m) \in \text{Rates}$$

#### 3.4 Batch Activation Constraint 批量激活约束

Batches are only produced if the corresponding $y$ variable is 1:

只有当 $y$ 变量为1时才生产批量：

$$x_{p,m,b} \leq \text{MAX\_BATCHES} \cdot y_{p,m,b} \quad \forall p \in P, m \in M, b \in B$$

#### 3.5 Demand Satisfaction Constraint 需求满足约束

Production plus unmet demand equals total demand:

生产加上未满足需求等于总需求：

$$\sum_{m \in M} \sum_{b \in B} x_{p,m,b} \cdot \text{BatchSize}_{p,b} + u_p = \text{Demand}_p + \text{RushOrder}_p \quad \forall p \in P$$

#### 3.6 Rush Order Priority Constraint 插单优先约束

Production must satisfy rush orders first (when rush orders exist):

生产必须优先满足插单（当存在插单时）：

$$\sum_{m \in M} \sum_{b \in B} x_{p,m,b} \cdot \text{BatchSize}_{p,b} + u^r_p \geq \text{RushOrder}_p \quad \forall p \in P \text{ with rush orders}$$

---

## Technical Implementation 技术实现

### 1. Solver: PuLP 求解器：PuLP

The project uses **PuLP** library to construct and solve the ILP model:

项目使用 **PuLP** 库构建和求解 ILP 模型：

```python
import pulp

# Create maximization problem 创建最大化问题
model = pulp.LpProblem("Optimal_Production_Schedule", pulp.LpMaximize)

# Define decision variables 定义决策变量
x = pulp.LpVariable.dicts(
    "Num_Of_Batches",
    [(p, m, b) for p in products for m in machines for b in batch_types],
    lowBound=0,
    cat="Integer",
)

y = pulp.LpVariable.dicts(
    "Min_Max_Assign",
    [(p, m, b) for p in products for m in machines for b in batch_types],
    cat="Binary",
)

# Define objective function 定义目标函数
model += (objective_expression, "Objective_Function")

# Add constraints 添加约束
model += (constraint_expression, "Constraint_Name")

# Solve 求解
model.solve()

# Get status and objective value 获取状态和目标值
status = pulp.LpStatus[model.status]
objective_value = pulp.value(model.objective)
```

### 2. Key Technical Points 关键技术点

#### 2.1 Batch Production Optimization 批量生产优化

- **Two batch types 两种批量类型**: min batch (quick response) and max batch (cost optimization) <br> 最小批量（快速响应）和最大批量（成本优化）
- **Binary variable control 二进制变量控制**: $y$ variable controls whether to use a batch type <br> $y$ 变量控制是否使用某批量类型
- **Variable linking 变量关联**: Constraint $x_{p,m,b} \leq MAX\_BATCHES \times y_{p,m,b}$ links batch variables <br> 约束关联批量变量

#### 2.2 Rush Order Priority Mechanism 插单优先级机制

- **Priority Multiplier 优先级倍数**: Rush order penalty multiplied by priority multiplier (default 2.0) <br> 插单惩罚成本乘以优先级倍数（默认2.0）
- **Constraint Strengthening 约束强化**: Add rush order priority satisfaction constraint <br> 添加插单优先满足约束
- **Impact Analysis 影响分析**: Calculate impact on original orders <br> 计算插单对原订单的影响

#### 2.3 Input Validation 输入验证

```python
def validate_inputs(machines, products, demand, ...):
    errors = []
    
    # Check empty lists 检查空列表
    if not machines:
        errors.append("Machine list cannot be empty")
    
    # Check non-negative constraints 检查非负约束
    for p in products:
        if profit.get(p, 0) < 0:
            errors.append(f"Profit for {p} cannot be negative")
    
    # Check valid rates 检查有效速率
    for (p, m), rate in rates.items():
        if rate <= 0:
            errors.append(f"Production rate for {p} on {m} must be > 0")
    
    return errors
```

---

## Algorithm Flow 算法流程

```
┌─────────────────────────────────────────────────────────────┐
│              INPUT PARAMETERS 输入参数                      │
│  Product params: profit, setup time, batch sizes, demand   │
│  产品参数：利润、设置时间、批量大小、需求                    │
│  Machine params: available hours, maintenance cost          │
│  机器参数：可用时间、维护成本                                │
│  Production rates: units per hour for each product-machine  │
│  生产速率：各产品在各机器上的生产速度                        │
│  Rush orders (optional): quantity, priority multiplier      │
│  插单参数（可选）：插单数量、优先级倍数                      │
└─────────────────────────────────────────────────────────────┘
                            │
                            ▼
┌─────────────────────────────────────────────────────────────┐
│              PARAMETER VALIDATION 参数校验                  │
│  Check all inputs are valid (non-negative, reasonable)     │
│  检查所有输入是否合法（非负、合理范围等）                    │
└─────────────────────────────────────────────────────────────┘
                            │
                            ▼
┌─────────────────────────────────────────────────────────────┐
│              BUILD ILP MODEL 构建 ILP 模型                  │
│  1. Define decision variables (x, y, u, u^r)               │
│     定义决策变量                                            │
│  2. Define objective function (maximize profit)            │
│     定义目标函数                                            │
│  3. Add constraints (machine assignment, time, demand)     │
│     添加约束条件                                            │
└─────────────────────────────────────────────────────────────┘
                            │
                            ▼
┌─────────────────────────────────────────────────────────────┐
│              SOLVE MODEL 求解模型                           │
│  Use PuLP's CBC solver to find optimal solution            │
│  使用 PuLP 的 CBC 求解器求解最优解                          │
└─────────────────────────────────────────────────────────────┘
                            │
                            ▼
┌─────────────────────────────────────────────────────────────┐
│              RESULT ANALYSIS 结果分析                       │
│  1. Extract variable values (batch counts, assignments)    │
│     提取变量值（批量数量、机器分配）                         │
│  2. Calculate production totals, unmet demand              │
│     计算生产总量、未满足需求                                 │
│  3. Calculate machine utilization                          │
│     计算机器利用率                                          │
│  4. Analyze rush order impact (if applicable)             │
│     分析插单影响（如适用）                                   │
└─────────────────────────────────────────────────────────────┘
                            │
                            ▼
┌─────────────────────────────────────────────────────────────┐
│              RESULT DISPLAY 结果展示                        │
│  Visualization: machine utilization charts, demand vs prod │
│  可视化图表：机器利用率、产量对比需求                        │
│  Text summary: production plan, unmet demand, rush results │
│  文字摘要：生产计划、未满足需求、插单处理结果                │
└─────────────────────────────────────────────────────────────┘
```

---

## Key Advantages 核心优势

### 1. Global Optimality 全局最优性

ILP solvers guarantee finding the global optimal solution (not local optimal):

ILP 求解器保证找到全局最优解（而非局部最优）：

| Problem Type 问题类型 | Solution Quality 解质量 |
|----------------------|------------------------|
| Linear Programming 线性规划 | Global optimal guaranteed 全局最优保证 |
| Integer Linear Programming 整数线性规划 | Global optimal guaranteed 全局最优保证 |
| Heuristic Methods 启发式方法 | May find local optimal 可能找到局部最优 |

### 2. Flexibility 灵活性

- **Scalable 可扩展**: Support any number of products and machines <br> 支持任意数量的产品和机器
- **Customizable 可定制**: All parameters can be adjusted <br> 所有参数可自定义
- **Dynamic Priority 动态优先级**: Support real-time priority adjustment <br> 支持实时优先级调整

### 3. Real-time Response 实时响应

Solving time for small-scale problems:

小规模问题的求解时间：

| Scale 规模 | Products 产品 | Machines 机器 | Solve Time 求解时间 |
|-----------|--------------|---------------|---------------------|
| Small 小型 | < 5 | < 5 | < 0.1s |
| Medium 中型 | 5-10 | 5-10 | < 1s |
| Large 大型 | 10-50 | 10-20 | 1-30s |

### 4. Extensibility 可扩展性

Easy to add new constraints:

易于添加新约束：

- **Labor constraints 劳动力约束**: Add labor hour limits <br> 添加劳动力时间限制
- **Storage constraints 存储约束**: Add inventory capacity limits <br> 添加库存容量限制
- **Multi-period planning 多周期规划**: Extend to multiple time periods <br> 扩展到多个时间段

---

## Application Scenarios 应用场景

| Scenario 场景 | Application Method 应用方式 |
|--------------|----------------------------|
| **Daily Production Planning** <br> 日常生产计划 | Input product and machine parameters, solve for optimal schedule <br> 输入产品、机器参数，求解最优调度 |
| **Machine Failure Response** <br> 机器故障应对 | Set failed machine's available hours to 0, re-optimize <br> 设置故障机器可用时间为0，重新优化 |
| **Demand Fluctuation** <br> 需求波动处理 | Modify demand parameters, assess if capacity is sufficient <br> 修改需求参数，评估产能是否足够 |
| **Rush Orders** <br> 紧急插单 | Enable rush order feature, set high priority multiplier <br> 启用插单功能，设置高优先级倍数 |
| **Cost Analysis** <br> 成本分析 | Adjust maintenance costs, penalty costs, analyze profit changes <br> 调整维护成本、惩罚成本，分析利润变化 |

---

## Technology Stack 技术栈

| Component 组件 | Technology 技术 | Purpose 作用 |
|---------------|-----------------|--------------|
| **Frontend Framework** <br> 前端框架 | Streamlit | Build interactive web interface <br> 构建交互式 Web 界面 |
| **Optimization Engine** <br> 优化引擎 | PuLP (CBC solver) | ILP model construction and solving <br> ILP 模型构建与求解 |
| **Data Processing** <br> 数据处理 | Pandas | Table data handling and input validation <br> 表格数据处理和输入验证 |
| **Visualization** <br> 可视化 | Plotly | Chart display (bar charts, comparison charts) <br> 图表展示（柱状图、对比图） |
| **Programming Language** <br> 编程语言 | Python 3.8+ | Core implementation <br> 核心实现 |

---

## References 参考资料

### Academic Papers 学术论文

1. Wolsey, L. A. (2020). *Integer Programming*. John Wiley & Sons.
2. Schrijver, A. (1998). *Theory of Linear and Integer Programming*. John Wiley & Sons.

### Documentation 文档

- [PuLP Documentation](https://coin-or.github.io/pulp/)
- [Streamlit Documentation](https://docs.streamlit.io/)
- [Plotly Python Documentation](https://plotly.com/python/)

---

## Conclusion 总结

This project demonstrates how to apply operations research theory (ILP) to real-world production scheduling problems. Through mathematical modeling and optimization algorithms, it achieves intelligent production decision-making.

这个项目展示了如何将运筹学理论（ILP）应用于实际生产调度问题，通过数学建模和优化算法实现智能化生产决策。

**Key Takeaways 关键要点**:

1. ILP provides guaranteed optimal solutions for production scheduling <br> ILP 为生产调度提供保证最优的解决方案
2. Flexible constraint modeling enables real-world applicability <br> 灵活的约束建模使实际应用成为可能
3. Priority mechanisms handle urgent orders effectively <br> 优先级机制有效处理紧急订单
4. Visualization aids decision-making process <br> 可视化辅助决策过程