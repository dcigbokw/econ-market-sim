import numpy as np
import pandas as pd
from scipy.optimize import curve_fit
from scipy.integrate import quad
from data_pipeline import get_micro_data  # Importing our Phase 1 work!

# ---------------------------------------------------------
# 1. DEFINE THE SHAPES (Quarter-Phase 2.1.1)
# ---------------------------------------------------------

def demand_func(Q, a, b):
    """Linear Demand Curve: Price = a - b(Quantity)"""
    return a - (b * Q)

def supply_func(Q, c, d):
    """Linear Supply Curve: Price = c + d(Quantity)"""
    return c + (d * Q)

# ---------------------------------------------------------
# 2. FIT THE CURVES (Quarter-Phase 2.1.2)
# ---------------------------------------------------------

def estimate_market_curves(df):
    """Takes real data and returns the exact a, b, c, d parameters."""
    
    Q_data = df['Quantity'].values
    P_data = df['Price'].values
    
    # We need to give SciPy a 'guess' to start its math. 
    # Max price is a good guess for the intercept (a, c).
    max_p = np.max(P_data)
    
    try:
        # Fit Demand (expecting a downward slope)
        # p0 is our initial guess: [intercept, slope]
        popt_demand, _ = curve_fit(demand_func, Q_data, P_data, p0=[max_p, 0.0001])
        
        # Fit Supply (expecting an upward slope)
        popt_supply, _ = curve_fit(supply_func, Q_data, P_data, p0=[0, 0.0001])
        
        a, b = popt_demand
        c, d = popt_supply
        
        return a, b, c, d
        
    except RuntimeError:
        print("SciPy could not find a curve to fit this data.")
        return None, None, None, None

# ---------------------------------------------------------
# 3. SOLVE THE EQUILIBRIUM (Quarter-Phase 2.2.1)
# ---------------------------------------------------------

def find_equilibrium(a, b, c, d):
    """
    Solves for Q* and P* where Supply = Demand.
    a - bQ = c + dQ
    a - c = dQ + bQ
    a - c = Q(d + b)
    Q* = (a - c) / (d + b)
    """
    # Prevent divide by zero errors
    if (d + b) == 0:
        return 0, 0
        
    Q_star = (a - c) / (d + b)
    
    # Plug Q* back into the demand equation to find P*
    P_star = demand_func(Q_star, a, b)
    
    return Q_star, P_star

def fit_curves(df):
    """Takes real API data and returns the optimal a, b, c, d parameters."""
    q = df['Quantity'].values
    p = df['Price'].values
    
    # Fit Demand (a - bQ)
    d_opt, _ = curve_fit(demand_func, q, p)
    # Fit Supply (c + dQ)
    s_opt, _ = curve_fit(supply_func, q, p)
    
    return d_opt[0], d_opt[1], s_opt[0], s_opt[1]

# --- 2. Your Original Surplus Logic ---
def calculate_surplus(a, b, c, d, Q_star, P_star):
    total_revenue = P_star * Q_star
    demand_integral, _ = quad(demand_func, 0, Q_star, args=(a, b))
    supply_integral, _ = quad(supply_func, 0, Q_star, args=(c, d))
    
    consumer_surplus = demand_integral - total_revenue
    producer_surplus = total_revenue - supply_integral
    
    return consumer_surplus, producer_surplus
# ---------------------------------------------------------
# 5. MARKET SHOCK DYNAMICS (Phase 3)
# ---------------------------------------------------------

def apply_tax_shock(a, b, c, d, tax_amount):
    """
    Simulates a per-unit tax on producers.
    Shifts the supply curve UP by the tax amount: P = (c + tax) + dQ
    """
    # 1. Shift the intercept (c) up by the tax
    c_tax = c + tax_amount
    
    # 2. Find the NEW equilibrium
    Q_tax, P_tax = find_equilibrium(a, b, c_tax, d)
    
    # 3. Calculate the new surpluses using the SHIFTED supply curve
    cs_tax, ps_tax = calculate_surplus(a, b, c_tax, d, Q_tax, P_tax)
    
    # 4. Calculate Government Tax Revenue (Tax * New Quantity)
    tax_revenue = tax_amount * Q_tax
    
    # 5. Calculate Deadweight Loss (DWL)
    # DWL is the total welfare lost that wasn't captured by the government
    old_total_welfare = sum(calculate_surplus(a, b, c, d, *find_equilibrium(a, b, c, d)))
    new_total_welfare = cs_tax + ps_tax + tax_revenue
    
    dwl = old_total_welfare - new_total_welfare
    
    return Q_tax, P_tax, cs_tax, ps_tax, tax_revenue, dwl


def apply_subsidy_shock(a, b, c, d, subsidy_amount):
    """
    Simulates a per-unit subsidy on producers.
    Shifts the supply curve DOWN by the subsidy amount: P = (c - subsidy) + dQ
    """
    # 1. Shift the intercept (c) down by the subsidy
    c_subsidy = c - subsidy_amount
    
    # 2. Find the NEW equilibrium
    Q_sub, P_sub = find_equilibrium(a, b, c_subsidy, d)
    
    # 3. Calculate the new surpluses using the SHIFTED supply curve
    cs_sub, ps_sub = calculate_surplus(a, b, c_subsidy, d, Q_sub, P_sub)
    
    # 4. Calculate Government Cost (-subsidy * New Quantity)
    subsidy_cost = subsidy_amount * Q_sub
    
    # 5. Calculate Net Social Benefit
    # The cost to the government is often offset by increases in welfare, 
    # but subsidies usually create their own form of deadweight loss (over-production)
    old_total_welfare = sum(calculate_surplus(a, b, c, d, *find_equilibrium(a, b, c, d)))
    new_total_welfare = cs_sub + ps_sub - subsidy_cost
    
    dwl = old_total_welfare - new_total_welfare
    
    return Q_sub, P_sub, cs_sub, ps_sub, subsidy_cost, dwl

# --- Execution Block ---
if __name__ == "__main__":
    print("Initializing Math Engine...")
    
    # 1. Get the data
    print("Pulling AAPL Micro Data...")
    df = get_micro_data("AAPL")
    
    # 2. Estimate the curves
    a, b, c, d = estimate_market_curves(df)
    
    print("\n--- Curve Parameters ---")
    print(f"Demand: P = {a:.2f} - {b:.6f}Q")
    print(f"Supply: P = {c:.2f} + {d:.6f}Q")
    
    # 3. Find the crossing point
    Q_star, P_star = find_equilibrium(a, b, c, d)
    
    print("\n--- Market Equilibrium ---")
    print(f"Equilibrium Quantity (Q*): {Q_star:,.2f}")
    print(f"Equilibrium Price (P*): ${P_star:,.2f}")
    
    # 4. Calculate the Surpluses
    cs, ps = calculate_surplus(a, b, c, d, Q_star, P_star)
    
    print("\n--- Economic Welfare ---")
    print(f"Consumer Surplus (CS): ${cs:,.2f}")
    print(f"Producer Surplus (PS): ${ps:,.2f}")
    print(f"Total Economic Welfare: ${cs + ps:,.2f}")
    
    # 5. Inject a Market Shock (Tax)
    print("\n==================================")
    print("🧨 INJECTING MARKET SHOCK: $5 TAX")
    print("==================================")
    
    tax = 5.00
    Q_t, P_t, cs_t, ps_t, tax_rev, dwl = apply_tax_shock(a, b, c, d, tax)
    
    print("\n--- New Market Reality ---")
    print(f"New Quantity (Q_t): {Q_t:,.2f} (Down from {Q_star:,.2f})")
    print(f"New Price (P_t): ${P_t:,.2f} (Up from ${P_star:,.2f})")
    
    print("\n--- New Welfare Distribution ---")
    print(f"New Consumer Surplus: ${cs_t:,.2f}")
    print(f"New Producer Surplus: ${ps_t:,.2f}")
    print(f"Government Tax Revenue: ${tax_rev:,.2f}")
    print(f"DEADWEIGHT LOSS (DWL): ${dwl:,.2f}")