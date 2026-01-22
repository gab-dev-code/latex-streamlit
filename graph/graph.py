import matplotlib.pyplot as plt

# Example structure for your data
voltage = [0, 10, 20, 30, 31, 32, 35, 40, 45, 50]
current_1000 = [4.4, 4.4, 4.4, 4.3, 4.1, 3.5, 3.2, 2.8, 2.4, 2.0]
current_800 = [4.2, 4.2, 4.2, 4.1, 3.9, 3.3, 3.0, 2.6, 2.2, 1.8]

plt.figure(figsize=(10, 5))

# Plotting the Irradiance Graph (Left)
plt.subplot(1, 2, 1)
plt.plot(voltage, current_1000, label='1000 $W/m^2$', color='tab:blue')
plt.plot(voltage, current_800, label='800 $W/m^2$', color='tab:orange')
# ... add other series

plt.xlabel('V(V)')
plt.ylabel('I(A)')
plt.grid(True, alpha=0.3)
plt.legend(loc='lower center', ncol=3, fontsize='small')
plt.xlim(0, 50)
plt.ylim(0, 5)

# Repeat for Temperature Graph (Right)
# plt.subplot(1, 2, 2) ...

plt.tight_layout()
plt.show()