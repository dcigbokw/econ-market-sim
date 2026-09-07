import streamlit as st
import plotly.graph_objects as go
import pandas as pd
import numpy as np
from data_pipeline import get_macro_data, get_micro_data
from math_engine import fit_curves, calculate_surplus, apply_tax_shock

# 1. Page Configuration (Must be the very first Streamlit command!)
st.set_page_config(page_title="Economic Shock Simulator", layout="wide")

st.title("📊 Market Equilibrium & Shock Simulator")
st.markdown("Adjust the controls to see how taxes or subsidies impact Consumer Surplus, Producer Surplus, and Deadweight Loss.")

# 2. Sidebar Controls
st.sidebar.header("Market Configuration")
mode = st.sidebar.radio("Select Data Route", ["Macro (FRED - GDP/CPI)", "Micro (yfinance - AAPL)"])
ticker = st.sidebar.text_input("Stock Ticker (Micro Mode only)", "AAPL")

st.sidebar.header("Policy Shocks")
tax = st.sidebar.slider("Per-Unit Tax ($)", 0.0, 50.0, 0.0)
subsidy = st.sidebar.slider("Per-Unit Subsidy ($)", 0.0, 50.0, 0.0)

# 3. Data Ingestion
if mode == "Macro (FRED - GDP/CPI)":
    data = get_macro_data()
else:
    data = get_micro_data(ticker)

# 4. Engine Processing & Curve Fitting
# Unpack all 4 values properly from fit_curves
a, b, c, d = fit_curves(data)

# Reorganize into dictionaries to make the rest of the code clean
demand_params = {'a': a, 'b': b}
supply_params = {'c': c, 'd': d}

# Apply net shocks (Tax minus Subsidy)
net_shock = tax - subsidy
taxed_c, taxed_d = apply_tax_shock(supply_params['c'], supply_params['d'], net_shock)
taxed_supply = {'c': taxed_c, 'd': taxed_d}

# Calculate Equilibrium functions
def get_eq(d_dict, s_dict):
    q_star = (d_dict['a'] - s_dict['c']) / (s_dict['d'] + d_dict['b'])
    p_star = d_dict['a'] - d_dict['b'] * q_star
    return max(0.0, q_star), max(0.0, p_star)

q_star, p_star = get_eq(demand_params, supply_params)
q_shock, p_shock = get_eq(demand_params, taxed_supply)

# 5. Visualization (Plotly)
fig = go.Figure()

# Create safe range for plotting
max_q = max(q_star * 1.5, 10.0)
q_range = np.linspace(0, max_q, 100)

# Plot Demand
fig.add_trace(go.Scatter(x=q_range, y=demand_params['a'] - demand_params['b']*q_range, name="Demand"))

# Plot Supply (Original & Shocked)
fig.add_trace(go.Scatter(x=q_range, y=supply_params['c'] + supply_params['d']*q_range, name="Supply", line=dict(dash='dash')))
fig.add_trace(go.Scatter(x=q_range, y=taxed_supply['c'] + taxed_supply['d']*q_range, name="Supply (Shocked)"))

fig.update_layout(xaxis_title="Quantity", yaxis_title="Price", template="plotly_white")
st.plotly_chart(fig, use_container_width=True)

# 6. Metrics Display
col1, col2, col3 = st.columns(3)

# Calculate surplus using your original 4-argument function signature
cs, ps = calculate_surplus(a, b, c, d, q_star, p_star)

# Placeholder estimation for DWL based on quantity restriction from the tax shock
dwl = 0.5 * abs(net_shock) * abs(q_star - q_shock) if net_shock != 0 else 0.0

col1.metric("Consumer Surplus", f"${cs:,.2f}")
col2.metric("Producer Surplus", f"${ps:,.2f}")
col3.metric("Deadweight Loss", f"${dwl:,.2f}")