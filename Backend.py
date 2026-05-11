import pulp
import pandas as pd
from typing import Dict, List, Tuple, Optional


MAX_BATCHES = 50000
DEFAULT_PRIORITY = 1.0


def validate_inputs(
    machines: List[str],
    products: List[str],
    demand: Dict[str, int],
    batch_sizes: Dict[Tuple[str, str], int],
    setup_time: Dict[str, float],
    profit: Dict[str, float],
    penalty_cost: Dict[str, float],
    rates: Dict[Tuple[str, str], float],
    maintenance_cost: Dict[str, float],
    available_hours: Dict[str, float],
    priority: Optional[Dict[str, float]] = None,
) -> List[str]:
    errors = []
    
    if not machines:
        errors.append("机器列表不能为空 (Machine list cannot be empty)")
    if not products:
        errors.append("产品列表不能为空 (Product list cannot be empty)")
    
    for p in products:
        if profit.get(p, 0) < 0:
            errors.append(f"产品 {p} 的利润不能为负数 (Profit for {p} cannot be negative)")
        if demand.get(p, 0) < 0:
            errors.append(f"产品 {p} 的需求不能为负数 (Demand for {p} cannot be negative)")
        if penalty_cost.get(p, 0) < 0:
            errors.append(f"产品 {p} 的惩罚成本不能为负数 (Penalty cost for {p} cannot be negative)")
        if setup_time.get(p, 0) < 0:
            errors.append(f"产品 {p} 的设置时间不能为负数 (Setup time for {p} cannot be negative)")
        if priority and priority.get(p, DEFAULT_PRIORITY) < 0:
            errors.append(f"产品 {p} 的优先级不能为负数 (Priority for {p} cannot be negative)")
    
    for m in machines:
        if available_hours.get(m, 0) < 0:
            errors.append(f"机器 {m} 的可用时间不能为负数 (Available hours for {m} cannot be negative)")
        if maintenance_cost.get(m, 0) < 0:
            errors.append(f"机器 {m} 的维护成本不能为负数 (Maintenance cost for {m} cannot be negative)")
    
    for (p, m), rate in rates.items():
        if rate <= 0:
            errors.append(f"产品 {p} 在机器 {m} 上的生产速率必须大于0 (Production rate for {p} on {m} must be > 0)")
    
    for (p, b), size in batch_sizes.items():
        if size <= 0:
            errors.append(f"产品 {p} 的{b}批量大小必须大于0 (Batch size {b} for {p} must be > 0)")
    
    return errors


def Model_Solver(
    machines: List[str],
    products: List[str],
    demand: Dict[str, int],
    batch_types: List[str],
    batch_sizes: Dict[Tuple[str, str], int],
    setup_time: Dict[str, float],
    profit: Dict[str, float],
    penalty_cost: Dict[str, float],
    rates: Dict[Tuple[str, str], float],
    maintenance_cost: Dict[str, float],
    available_hours: Dict[str, float],
    priority: Optional[Dict[str, float]] = None,
    rush_orders: Optional[Dict[str, int]] = None,
    rush_priority_multiplier: float = 2.0,
) -> Tuple[Dict, Dict, Dict, str, Optional[float], Dict[str, int], Dict[str, int]]:
    """Optimize the production schedule using linear programming with rush order support.
    
    Args:
        machines: List of machine names.
        products: List of product names.
        demand: Dictionary mapping products to their demand.
        batch_types: List of batch types (e.g., "min", "max").
        batch_sizes: Dictionary mapping (product, batch_type) to batch size.
        setup_time: Dictionary mapping products to setup time in hours.
        profit: Dictionary mapping products to profit per unit.
        penalty_cost: Dictionary mapping products to penalty cost per unmet unit.
        rates: Dictionary mapping (product, machine) to production rate (units per hour).
        maintenance_cost: Dictionary mapping machines to their maintenance cost.
        available_hours: Dictionary mapping machines to their available hours per day.
        priority: Dictionary mapping products to priority multipliers (default 1.0).
        rush_orders: Dictionary mapping products to rush order quantities.
        rush_priority_multiplier: Priority multiplier for rush orders.
    
    Returns:
        Tuple containing:
        - x: Number of batches variables
        - y: Binary assignment variables
        - unmet: Unmet demand variables
        - Status: Optimization status
        - Model_Objective: Objective value (None if infeasible)
        - rush_satisfied: Amount of rush orders satisfied
        - original_unmet: Unmet demand without rush orders
    """
    if priority is None:
        priority = {p: DEFAULT_PRIORITY for p in products}
    
    if rush_orders is None:
        rush_orders = {}
    
    total_demand = {p: demand.get(p, 0) + rush_orders.get(p, 0) for p in products}
    
    validation_errors = validate_inputs(
        machines, products, total_demand, batch_sizes, setup_time,
        profit, penalty_cost, rates, maintenance_cost, available_hours, priority
    )
    
    if validation_errors:
        return {}, {}, {}, "Invalid Input: " + "; ".join(validation_errors), None, {}, {}
    
    model = pulp.LpProblem("Optimal_Production_Schedule", pulp.LpMaximize)
    
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
    
    unmet = pulp.LpVariable.dicts(
        "Unmet_Demand", products, lowBound=0, cat="Integer"
    )
    
    unmet_rush = pulp.LpVariable.dicts(
        "Unmet_Rush", products, lowBound=0, cat="Integer"
    )
    
    production = {}
    for p in products:
        production[p] = pulp.lpSum(
            [x[(p, m, b)] * batch_sizes[(p, b)]
             for m in machines
             for b in batch_types
             if (p, m) in rates
            ]
        )
    
    objective_terms = []
    
    for p in products:
        base_profit = profit[p] * priority[p] * production[p]
        
        rush_term = 0
        if rush_orders.get(p, 0) > 0:
            rush_production = pulp.lpSum([
                x[(p, m, b)] * batch_sizes[(p, b)]
                for m in machines
                for b in batch_types
                if (p, m) in rates
            ])
            rush_satisfied = rush_production - pulp.lpSum([
                x[(p, m, b)] * batch_sizes[(p, b)]
                for m in machines
                for b in batch_types
                if (p, m) in rates
                if production[p] > rush_orders[p]
            ])
            rush_term = profit[p] * (rush_priority_multiplier - 1) * rush_orders.get(p, 0)
        
        penalty_term = penalty_cost[p] * unmet[p]
        if rush_orders.get(p, 0) > 0:
            penalty_term += penalty_cost[p] * rush_priority_multiplier * unmet_rush[p]
        
        objective_terms.append(base_profit + rush_term - penalty_term)
    
    maintenance_terms = pulp.lpSum([
        maintenance_cost[m] * y[(p, m, b)]
        for p in products
        for m in machines
        for b in batch_types
        if (p, m) in rates
    ])
    
    model += (pulp.lpSum(objective_terms) - maintenance_terms, "Objective_Function")
    
    for m in machines:
        model += (
            pulp.lpSum([
                y[(p, m, b)]
                for p in products
                for b in batch_types
                if (p, m) in rates
            ]) <= 1
        )
        
        model += (
            pulp.lpSum([
                (x[(p, m, b)] * batch_sizes[(p, b)] / rates[(p, m)]
                 + setup_time[p] * y[(p, m, b)])
                for p in products
                for b in batch_types
                if (p, m) in rates
            ]) <= available_hours[m]
        )
    
    for p, m in rates:
        model += y[(p, m, "min")] + y[(p, m, "max")] <= 1
        for b in batch_types:
            model += x[(p, m, b)] <= MAX_BATCHES * y[(p, m, b)]
    
    for p in products:
        model += (
            production[p] + unmet[p] == total_demand[p],
            f"Meet_Total_Demand_{p}",
        )
        
        if rush_orders.get(p, 0) > 0:
            model += (
                production[p] + unmet_rush[p] >= rush_orders[p],
                f"Rush_Min_{p}",
            )
    
    model.solve()
    Status = pulp.LpStatus[model.status]
    Model_Objective = pulp.value(model.objective)
    
    rush_satisfied = {}
    original_unmet = {}
    for p in products:
        prod = sum([
            x[(p, m, b)].varValue * batch_sizes[(p, b)]
            for m in machines
            for b in batch_types
            if (p, m) in rates and x[(p, m, b)].varValue > 0
        ]) if x else 0
        
        rush_satisfied[p] = min(prod, rush_orders.get(p, 0))
        original_demand = demand.get(p, 0)
        original_unmet[p] = max(0, original_demand - (prod - rush_satisfied[p]))
    
    return x, y, unmet, Status, Model_Objective, rush_satisfied, original_unmet


def Results_Calculating(
    x: Dict,
    y: Dict,
    unmet: Dict,
    products: List[str],
    machines: List[str],
    rates: Dict[Tuple[str, str], float],
    batch_types: List[str],
    batch_sizes: Dict[Tuple[str, str], int],
    setup_time: Dict[str, float],
    demand: Dict[str, int],
    available_hours: Dict[str, float],
    rush_orders: Optional[Dict[str, int]] = None,
    rush_satisfied: Optional[Dict[str, int]] = None,
) -> Tuple[List[str], List[str], List[str], List[str], Dict[str, float], Dict[str, float], List[str]]:
    """Calculate and format results from the optimization model.
    
    Returns:
        Tuple containing:
        - Prod_Totals_Msg: Production summary messages
        - Unmet_Summary: Unmet demand summary
        - Machine_Hours: Machine usage hours
        - Machine_Utilization: Machine utilization percentages
        - prod_totals: Production totals dict
        - machine_hours_dict: Machine hours dict
        - rush_summary: Rush order summary
    """
    if rush_orders is None:
        rush_orders = {}
    if rush_satisfied is None:
        rush_satisfied = {}
    
    Prod_Totals_Msg = []
    prod_totals = {p: 0 for p in products}
    
    for p, m in rates:
        for b in batch_types:
            if x[(p, m, b)].varValue > 0:
                batch_units = x[(p, m, b)].varValue * batch_sizes[(p, b)]
                Prod_Totals_Msg.append(
                    f"产品 {p} 在机器 {m} 上使用{b}批量({batch_sizes[(p, b)]}) → 批次数: {x[(p, m, b)].varValue} → 总数量: {batch_units}"
                )
                prod_totals[p] += batch_units
    
    Unmet_Summary = []
    for p in products:
        if unmet[p].varValue > 0:
            Unmet_Summary.append(f"产品 {p} 未满足需求: {unmet[p].varValue} 单位, 已生产 {prod_totals[p]} / {demand.get(p, 0) + rush_orders.get(p, 0)}")
        else:
            Unmet_Summary.append(f"产品 {p} 需求已全部满足, 总产量: {prod_totals[p]}")
    
    Machine_Hours = []
    Machine_Utilization = []
    machine_hours_dict = {}
    
    for m in machines:
        total_hours = 0
        
        for p, m2 in rates:
            if m2 == m:
                for b in batch_types:
                    if y[(p, m, b)].varValue == 1:
                        total_hours += (
                            x[(p, m, b)].varValue
                            * batch_sizes[(p, b)]
                            / rates[(p, m)]
                            + setup_time[p]
                        )
        
        machine_hours_dict[m] = total_hours
        Utilization = total_hours / available_hours[m] * 100 if available_hours[m] > 0 else 0
        Machine_Hours.append(f"机器 {m}: 使用 {total_hours:.2f} 小时 / 可用 {available_hours[m]} 小时")
        Machine_Utilization.append(f"机器利用率: {Utilization:.2f}%")
    
    rush_summary = []
    if rush_orders:
        rush_summary.append("=== 插单处理结果 ===")
        for p, rush_qty in rush_orders.items():
            satisfied = rush_satisfied.get(p, 0)
            status = "已满足" if satisfied >= rush_qty else f"部分满足 ({satisfied}/{rush_qty})"
            rush_summary.append(f"产品 {p}: 插单数量 {rush_qty} → {status}")
    
    return Prod_Totals_Msg, Unmet_Summary, Machine_Hours, Machine_Utilization, prod_totals, machine_hours_dict, rush_summary