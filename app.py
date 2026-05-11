import streamlit as st
import pulp
import pandas as pd
import json
import os
import plotly.express as px
import Backend

st.set_page_config(
    page_title="Production Optimizer", page_icon="📦", layout="centered"
)

st.markdown(
    """
    <style>
    .stApp {
        background-color: #f4f9ff;
        font-family: 'Helvetica', sans-serif;
        color: #0089CF;
    }

    .block-container {
        padding-top: 2rem;
    }

    h1 {
        color: #0072ce;
    }

    p {
        color: #333;
    }

    .stButton > button {
        background-color: #0089CF !important;
        color: white !important;
        border: none;
        padding: 0.6em 1.2em;
        border-radius: 4px;
        font-weight: bold;
    }

    .stButton > button:hover {
        background-color: #0072ce !important;
        color: white !important;
    }

    .stAlert {
        padding: 1rem;
        border-radius: 4px;
    }

    .rush-highlight {
        background-color: #fff3cd;
        border-left: 4px solid #ffc107;
        padding: 0.5rem;
        margin: 0.5rem 0;
    }
    </style>
    """,
    unsafe_allow_html=True,
)


def load_example_data():
    products = ["A", "B", "C"]
    machines = ["W", "X", "Y", "Z"]
    
    product_df = pd.DataFrame({
        "Product": products,
        "Profit per Unit": [100, 80, 120],
        "Setup Time (min)": [30, 20, 25],
        "Min Batch Size": [5, 8, 4],
        "Max Batch Size": [20, 30, 15],
        "Demand (units)": [150, 330, 150],
        "Penalty Cost (per unit)": [50, 40, 60],
        "Priority": [1.0, 1.0, 1.0],
    })
    
    machine_df = pd.DataFrame({
        "Machine": machines,
        "Available Hours": [8.0, 12.0, 10.0, 9.0],
        "Maintenance Cost": [100.0, 150.0, 120.0, 110.0],
    })
    
    rate_entries = []
    rates_dict = {
        ("A", "W"): 20, ("A", "X"): 25, ("A", "Y"): 18, ("A", "Z"): 22,
        ("B", "W"): 30, ("B", "X"): 35, ("B", "Y"): 28, ("B", "Z"): 32,
        ("C", "W"): 15, ("C", "X"): 18, ("C", "Y"): 14, ("C", "Z"): 16,
    }
    
    for p in products:
        for m in machines:
            rate_entries.append({
                "Product": p,
                "Machine": m,
                "Rate (units/hr)": rates_dict.get((p, m), "")
            })
    
    rate_df = pd.DataFrame(rate_entries)
    return products, machines, product_df, machine_df, rate_df


def save_config(products, machines, product_df, machine_df, rate_df, filename="production_config.json"):
    config = {
        "products": products,
        "machines": machines,
        "product_params": product_df.to_dict("records"),
        "machine_params": machine_df.to_dict("records"),
        "rate_params": rate_df.to_dict("records"),
        "saved_at": pd.Timestamp.now().isoformat()
    }
    
    with open(filename, "w", encoding="utf-8") as f:
        json.dump(config, f, ensure_ascii=False, indent=2)
    
    return filename


def load_config(filename="production_config.json"):
    if not os.path.exists(filename):
        return None
    
    with open(filename, "r", encoding="utf-8") as f:
        config = json.load(f)
    
    products = config["products"]
    machines = config["machines"]
    product_df = pd.DataFrame(config["product_params"])
    machine_df = pd.DataFrame(config["machine_params"])
    rate_df = pd.DataFrame(config["rate_params"])
    
    if "Priority" not in product_df.columns:
        product_df["Priority"] = 1.0
    
    return products, machines, product_df, machine_df, rate_df


def validate_input_tables(product_df, machine_df, rate_df, rush_df=None):
    errors = []
    
    for _, row in product_df.iterrows():
        p = row["Product"]
        if pd.isna(row["Profit per Unit"]) or row["Profit per Unit"] <= 0:
            errors.append(f"产品 {p}: 利润必须大于0 (Profit must be > 0)")
        if pd.isna(row["Demand (units)"]) or row["Demand (units)"] < 0:
            errors.append(f"产品 {p}: 需求不能为负数 (Demand cannot be negative)")
        if pd.isna(row["Min Batch Size"]) or row["Min Batch Size"] <= 0:
            errors.append(f"产品 {p}: 最小批量必须大于0 (Min batch size must be > 0)")
        if pd.isna(row["Max Batch Size"]) or row["Max Batch Size"] <= 0:
            errors.append(f"产品 {p}: 最大批量必须大于0 (Max batch size must be > 0)")
        if not pd.isna(row["Min Batch Size"]) and not pd.isna(row["Max Batch Size"]):
            if row["Min Batch Size"] > row["Max Batch Size"]:
                errors.append(f"产品 {p}: 最小批量不能大于最大批量 (Min batch > Max batch)")
        if "Priority" in product_df.columns:
            if pd.isna(row["Priority"]) or row["Priority"] <= 0:
                errors.append(f"产品 {p}: 优先级必须大于0 (Priority must be > 0)")
    
    for _, row in machine_df.iterrows():
        m = row["Machine"]
        if pd.isna(row["Available Hours"]) or row["Available Hours"] < 0:
            errors.append(f"机器 {m}: 可用时间不能为负数 (Available hours cannot be negative)")
    
    for _, row in rate_df.iterrows():
        p = row["Product"]
        m = row["Machine"]
        rate = row["Rate (units/hr)"]
        if pd.notna(rate) and (isinstance(rate, (int, float)) and rate <= 0):
            errors.append(f"产品 {p} 在机器 {m}: 生产速率必须大于0 (Rate must be > 0)")
    
    if rush_df is not None:
        for _, row in rush_df.iterrows():
            p = row["Product"]
            rush_qty = row["Rush Quantity"]
            if pd.isna(rush_qty) or rush_qty <= 0:
                errors.append(f"产品 {p}: 插单数量必须大于0 (Rush quantity must be > 0)")
    
    return errors


st.image("Logo.png", width=200)
st.title("Production Optimization 生产计划优化")
st.markdown("使用整数线性规划优化生产调度，支持临时插单优先级处理 | Optimize production scheduling using Integer Linear Programming with rush order support")

col1, col2, col3 = st.columns(3)
with col1:
    if st.button("📥 Load Example Data\n加载示例数据"):
        products, machines, product_df, machine_df, rate_df = load_example_data()
        st.session_state["products"] = products
        st.session_state["machines"] = machines
        st.session_state["product_df"] = product_df
        st.session_state["machine_df"] = machine_df
        st.session_state["rate_df"] = rate_df
        st.rerun()

with col2:
    if st.button("💾 Save Configuration\n保存配置"):
        if "product_df" in st.session_state and "machine_df" in st.session_state:
            filename = save_config(
                st.session_state.get("products", []),
                st.session_state.get("machines", []),
                st.session_state["product_df"],
                st.session_state["machine_df"],
                st.session_state.get("rate_df", pd.DataFrame())
            )
            st.success(f"配置已保存到 {filename}")
        else:
            st.warning("请先输入数据再保存配置")

with col3:
    if st.button("📂 Load Configuration\n加载配置"):
        config = load_config()
        if config:
            products, machines, product_df, machine_df, rate_df = config
            st.session_state["products"] = products
            st.session_state["machines"] = machines
            st.session_state["product_df"] = product_df
            st.session_state["machine_df"] = machine_df
            st.session_state["rate_df"] = rate_df
            st.rerun()
        else:
            st.warning("未找到配置文件")

st.markdown("---")
st.markdown("### Step 1: Define Machines and Products\n步骤1: 定义机器和产品")

products_input = st.text_input(
    "Enter product names (comma-separated) | 输入产品名称（逗号分隔）",
    value=", ".join(st.session_state.get("products", [])) if "products" in st.session_state else ""
)
machines_input = st.text_input(
    "Enter machine names (comma-separated) | 输入机器名称（逗号分隔）",
    value=", ".join(st.session_state.get("machines", [])) if "machines" in st.session_state else ""
)

if machines_input and products_input:
    machines = [m.strip() for m in machines_input.split(",") if m.strip()]
    products = [p.strip() for p in products_input.split(",") if p.strip()]
    batch_types = ["min", "max"]

    st.markdown("### Step 2: Enter Product Parameters\n步骤2: 输入产品参数")
    
    if "product_df" in st.session_state and set(st.session_state["product_df"]["Product"]) == set(products):
        product_df = st.session_state["product_df"]
    else:
        product_df = pd.DataFrame({
            "Product": products,
            "Profit per Unit": [0] * len(products),
            "Setup Time (min)": [0] * len(products),
            "Min Batch Size": [1] * len(products),
            "Max Batch Size": [1] * len(products),
            "Demand (units)": [1] * len(products),
            "Penalty Cost (per unit)": [0] * len(products),
            "Priority": [1.0] * len(products),
        })

    product_df = st.data_editor(product_df, num_rows="dynamic", key="product_params")

    profit = {row["Product"]: row["Profit per Unit"] for _, row in product_df.iterrows()}
    setup_time = {row["Product"]: row["Setup Time (min)"] / 60 for _, row in product_df.iterrows()}
    batch_sizes = {}
    for _, row in product_df.iterrows():
        batch_sizes[(row["Product"], "min")] = row["Min Batch Size"]
        batch_sizes[(row["Product"], "max")] = row["Max Batch Size"]
    demand = {row["Product"]: row["Demand (units)"] for _, row in product_df.iterrows()}
    penalty_cost = {row["Product"]: row["Penalty Cost (per unit)"] for _, row in product_df.iterrows()}
    priority = {row["Product"]: row.get("Priority", 1.0) for _, row in product_df.iterrows()}

    st.markdown("### Step 3: Define Machine Parameters\n步骤3: 定义机器参数")
    
    if "machine_df" in st.session_state and set(st.session_state["machine_df"]["Machine"]) == set(machines):
        machine_df = st.session_state["machine_df"]
    else:
        machine_df = pd.DataFrame({
            "Machine": machines,
            "Available Hours": [0.0] * len(machines),
            "Maintenance Cost": [0.0] * len(machines),
        })

    machine_df = st.data_editor(machine_df, num_rows="dynamic", key="machine_params")

    available_hours = {row["Machine"]: row["Available Hours"] for _, row in machine_df.iterrows()}
    maintenance_cost = {row["Machine"]: row["Maintenance Cost"] for _, row in machine_df.iterrows()}

    st.markdown("### Step 4: Define Production Rates\n步骤4: 定义生产速率")
    
    if "rate_df" in st.session_state:
        existing_rates = {(r["Product"], r["Machine"]): r["Rate (units/hr)"] 
                         for _, r in st.session_state["rate_df"].iterrows()}
    else:
        existing_rates = {}
    
    rate_entries = []
    for p in products:
        for m in machines:
            rate_entries.append({
                "Product": p,
                "Machine": m,
                "Rate (units/hr)": existing_rates.get((p, m), "")
            })

    rate_df = pd.DataFrame(rate_entries)
    rate_df = st.data_editor(rate_df, key="rate_table")

    rates = {}
    for _, row in rate_df.iterrows():
        try:
            rate = float(row["Rate (units/hr)"])
            if rate > 0:
                rates[(row["Product"], row["Machine"])] = rate
        except:
            pass

    st.markdown("### Step 5: Rush Orders (Optional)\n步骤5: 临时插单（可选）")
    st.markdown("<div class='rush-highlight'>临时插单会获得更高优先级，系统将优先满足插单需求。插单优先级倍数可自定义。</div>", unsafe_allow_html=True)
    
    rush_enabled = st.checkbox("Enable Rush Orders | 启用插单功能", value=False)
    
    if rush_enabled:
        rush_multiplier = st.slider(
            "Rush Priority Multiplier | 插单优先级倍数",
            min_value=1.1, max_value=5.0, value=2.0, step=0.1,
            help="插单产品的优先级将乘以此倍数"
        )
        
        rush_entries = []
        for p in products:
            rush_entries.append({"Product": p, "Rush Quantity": 0})
        
        rush_df = pd.DataFrame(rush_entries)
        rush_df = st.data_editor(rush_df, key="rush_orders")
        
        rush_orders = {row["Product"]: row["Rush Quantity"] 
                      for _, row in rush_df.iterrows() 
                      if row["Rush Quantity"] > 0}
    else:
        rush_orders = {}
        rush_multiplier = 2.0

    if st.button("🚀 Optimize Production\n优化生产计划"):
        validation_errors = validate_input_tables(product_df, machine_df, rate_df, rush_df if rush_enabled else None)
        
        if validation_errors:
            st.error("输入验证失败 | Input Validation Failed:\n" + "\n".join(validation_errors))
        elif not rates:
            st.error("请至少输入一个生产速率 | Please enter at least one production rate")
        else:
            with st.spinner("正在优化... | Optimizing..."):
                [x, y, unmet, Status, Model_Objective, rush_satisfied, original_unmet] = Backend.Model_Solver(
                    machines, products, demand, batch_types, batch_sizes,
                    setup_time, profit, penalty_cost, rates, maintenance_cost, available_hours,
                    priority, rush_orders, rush_multiplier
                )

            if Status.startswith("Invalid Input"):
                st.error(Status)
            else:
                [Prod_Totals_Msg, Unmet_Summary, Machine_Hours, Machine_Utilization, prod_totals, machine_hours_dict, rush_summary] = Backend.Results_Calculating(
                    x, y, unmet, products, machines, rates, batch_types,
                    batch_sizes, setup_time, demand, available_hours,
                    rush_orders, rush_satisfied
                )

                st.markdown("---")
                st.markdown("### Results 结果")
                st.write(f"**Status | 状态:** {Status}")
                st.write(f"**Total Profit | 总利润:** ${Model_Objective:,.2f}")

                if rush_orders:
                    st.markdown("### Rush Order Results | 插单处理结果")
                    for msg in rush_summary:
                        st.write(msg)

                st.markdown("### Production Summary | 生产摘要")
                for msg in Prod_Totals_Msg:
                    st.write(msg)

                st.markdown("### Unmet Demand | 未满足需求")
                for summary in Unmet_Summary:
                    st.write(summary)

                if rush_orders and original_unmet:
                    st.markdown("### Impact on Original Orders | 对原订单的影响")
                    for p in products:
                        if original_unmet.get(p, 0) > 0:
                            st.warning(f"产品 {p}: 原订单未满足 {original_unmet[p]} 单位（因插单占用产能）")

                st.markdown("### Machine Utilization | 机器利用率")
                utilization_data = pd.DataFrame({
                    "Machine": machines,
                    "Hours Used": [machine_hours_dict.get(m, 0) for m in machines],
                    "Hours Available": [available_hours.get(m, 0) for m in machines]
                })
                
                fig = px.bar(
                    utilization_data,
                    x="Machine",
                    y=["Hours Used", "Hours Available"],
                    title="Machine Utilization | 机器使用时间",
                    barmode="group",
                    labels={"value": "Hours | 小时", "variable": "Type | 类型"},
                    color_discrete_map={"Hours Used": "#0089CF", "Hours Available": "#87CEEB"}
                )
                st.plotly_chart(fig)

                for i in range(len(Machine_Hours)):
                    st.write(Machine_Hours[i])
                    st.write(Machine_Utilization[i])

                st.markdown("### Production vs Demand | 产量对比需求")
                total_demand = {p: demand.get(p, 0) + rush_orders.get(p, 0) for p in products}
                prod_demand_df = pd.DataFrame({
                    "Product": products,
                    "Produced": [prod_totals.get(p, 0) for p in products],
                    "Demand": [total_demand.get(p, 0) for p in products],
                    "Original Demand": [demand.get(p, 0) for p in products],
                    "Rush Orders": [rush_orders.get(p, 0) for p in products]
                })
                
                fig2 = px.bar(
                    prod_demand_df,
                    x="Product",
                    y=["Produced", "Original Demand", "Rush Orders"],
                    title="Production vs Demand | 产量对比需求",
                    barmode="group",
                    labels={"value": "Units | 单位", "variable": "Type | 类型"},
                    color_discrete_map={"Produced": "#2ECC71", "Original Demand": "#E74C3C", "Rush Orders": "#FFA500"}
                )
                st.plotly_chart(fig2)

                st.session_state["last_results"] = {
                    "status": Status,
                    "profit": Model_Objective,
                    "prod_totals": prod_totals,
                    "machine_hours": machine_hours_dict,
                    "rush_orders": rush_orders,
                    "rush_satisfied": rush_satisfied
                }

                st.session_state["products"] = products
                st.session_state["machines"] = machines
                st.session_state["product_df"] = product_df
                st.session_state["machine_df"] = machine_df
                st.session_state["rate_df"] = rate_df
else:
    st.info("请输入机器和产品名称开始 | Please enter both machines and products to begin.")

if "last_results" in st.session_state:
    st.sidebar.markdown("### Last Optimization | 上次优化结果")
    st.sidebar.write(f"Status: {st.session_state['last_results']['status']}")
    st.sidebar.write(f"Profit: ${st.session_state['last_results']['profit']:,.2f}")
    if "rush_orders" in st.session_state["last_results"] and st.session_state["last_results"]["rush_orders"]:
        st.sidebar.markdown("**Rush Orders:**")
        for p, qty in st.session_state["last_results"]["rush_orders"].items():
            satisfied = st.session_state["last_results"]["rush_satisfied"].get(p, 0)
            st.sidebar.write(f"- {p}: {satisfied}/{qty}")