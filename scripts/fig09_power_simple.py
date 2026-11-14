# Figure 9 for the interim report: smallest detectable IC vs test length
# MDE = (z_0.975 + z_0.80) / sqrt(N - 1) / sqrt(T)
import numpy as np
import matplotlib.pyplot as plt
from scipy.stats import norm

z = norm.ppf(0.975) + norm.ppf(0.80)

def mde(n, t):
    return z / np.sqrt(n - 1) / np.sqrt(t)

months = np.arange(12, 181)

plt.figure(figsize=(7, 4.2))

# typical real signals
plt.axhspan(0.02, 0.05, color="lightgrey", alpha=0.6)
plt.text(14, 0.027, "typical real signals (0.02 to 0.05)", fontsize=9, va="center")

for n in [12, 18, 30]:
    plt.plot(months, mde(n, months))
    plt.text(182, mde(n, 180), f"{n} counters", fontsize=9, va="center")

# 8 years with 18 counters
v = mde(18, 96)
plt.plot(96, v, "kD", markersize=7)
plt.annotate(f"8 years: {v:.2f}", (96, v), xytext=(105, 0.12),
             arrowprops=dict(arrowstyle="->"))

plt.xlim(10, 200)
plt.ylim(0, 0.32)
plt.xlabel("Months of out-of-sample data")
plt.ylabel("Smallest detectable IC")
plt.grid(alpha=0.3)
plt.tight_layout()
plt.savefig("reports/figures/fig09_power_simple.png", dpi=200)
print("8 years, 18 counters:", round(v, 3))
