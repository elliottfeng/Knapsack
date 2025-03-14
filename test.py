import pulp
import streamlit as st
import pandas as pd

# Streamlit 页面标题
st.title("商品组合优化器")
st.write("输入商品信息和初始资金，计算最优组合以最小化余额。")

# 输入初始资金
initial_funds = st.number_input("初始资金", min_value=0, value=50000)

# 输入商品信息
st.header("商品信息录入")
num_items = st.number_input("商品数量", min_value=1, value=5)

# 使用列布局归拢商品信息输入框
items = []
cols = st.columns(2)  # 每行显示 2 个商品信息
for i in range(num_items):
    with cols[i % 2]:  # 交替分配到两列
        st.subheader(f"商品 {i+1}")
        name = st.text_input(f"商品 {i+1} 名称", value=f"商品 {i+1}", key=f"name_{i}")
        price = st.number_input(f"商品 {i+1} 初始单价", min_value=0, value=1000, key=f"price_{i}")
        items.append({"name": name, "initial_price": price})

# 展示商品信息
if items:
    st.header("商品信息表")
    df = pd.DataFrame(items)
    st.write("以下是输入的商品信息：")
    st.dataframe(df)

# 选择交易日
st.header("选择交易日")
trade_day = st.selectbox("选择交易日", range(1, 101), index=0)

# 计算每日涨幅后的商品单价
if trade_day >= 1:
    for item in items:
        item["adjusted_price"] = round(item["initial_price"] * (1.035) ** (trade_day - 1), 2)  # 保留两位小数
    st.write(f"以下是第 {trade_day} 个交易日的商品单价（每日涨幅 3.5%）：")
    df_adjusted = pd.DataFrame(items)
    # 格式化展示调整后的单价
    st.dataframe(df_adjusted[["name", "adjusted_price"]].style.format({"adjusted_price": "{:.2f}"}))

# 计算最优解
if st.button("计算最优解"):
    if not items:
        st.error("请先输入商品信息。")
    else:
        # 计算最小商品单价
        min_price = min(item["adjusted_price"] for item in items)

        # 定义问题
        prob = pulp.LpProblem("Minimize_Balance", pulp.LpMinimize)

        # 定义变量：每种商品的数量（整数）
        quantities = [pulp.LpVariable(f"x{i}", lowBound=0, cat="Integer") for i in range(len(items))]

        # 定义目标函数：最小化余额
        prob += initial_funds - pulp.lpSum([items[i]["adjusted_price"] * quantities[i] for i in range(len(items))])

        # 定义约束条件：总金额不超过初始资金
        prob += pulp.lpSum([items[i]["adjusted_price"] * quantities[i] for i in range(len(items))]) <= initial_funds

        # 设置求解器参数
        solver = pulp.PULP_CBC_CMD(
            gapRel=0.01,  # 相对容差 1%
            timeLimit=60,  # 最大运行时间 60 秒
            msg=True  # 显示求解器日志
        )

        # 求解
        prob.solve(solver)

        # 输出结果
        st.header("优化结果")
        st.write(f"**状态:** {pulp.LpStatus[prob.status]}")

        if pulp.LpStatus[prob.status] == "Optimal":
            st.write("**最佳组合:**")
            result = []
            for i in range(len(items)):
                result.append({
                    "商品名称": items[i]["name"],
                    "调整后单价": items[i]["adjusted_price"],
                    "数量": int(quantities[i].varValue)
                })
            result_df = pd.DataFrame(result)
            # 格式化展示调整后的单价
            st.dataframe(result_df.style.format({"调整后单价": "{:.2f}"}))

            total_amount = sum(items[i]["adjusted_price"] * int(quantities[i].varValue) for i in range(len(items)))
            balance = initial_funds - total_amount
            st.write(f"**总金额:** {total_amount:.2f}")
            st.write(f"**余额:** {balance:.2f}")

            # 检查余额是否小于最小商品单价
            if balance < min_price:
                st.write(f"余额 {balance:.2f} 已小于最小商品单价 {min_price:.2f}，停止运算。")
        else:
            st.error("未找到最优解。请检查输入数据。")