import pandas as pd
import matplotlib.pyplot as plt

# Load the data
df = pd.read_csv('wrench_data.csv')

# Inspect the data
print(df.head())
print(df.info())

# Calculate relative time in seconds
df['time'] = (df['timestamp_sec'] - df['timestamp_sec'].iloc[0]) + (df['timestamp_nanosec'] - df['timestamp_nanosec'].iloc[0]) / 1e9

# Create the plot
fig, (ax1, ax2) = plt.subplots(2, 1, sharex=True, figsize=(10, 8))

# Plot Forces
ax1.plot(df['time'], df['force_x'], label='$F_x$')
ax1.plot(df['time'], df['force_y'], label='$F_y$')
ax1.plot(df['time'], df['force_z'], label='$F_z$')
ax1.set_ylabel('Force (N)')
ax1.set_title('Wrench Data: Force Components')
ax1.legend()
ax1.grid(True)

# Plot Torques
ax2.plot(df['time'], df['torque_x'], label='$T_x$')
ax2.plot(df['time'], df['torque_y'], label='$T_y$')
ax2.plot(df['time'], df['torque_z'], label='$T_z$')
ax2.set_xlabel('Time (s)')
ax2.set_ylabel('Torque (N·m)')
ax2.set_title('Wrench Data: Torque Components')
ax2.legend()
ax2.grid(True)

plt.tight_layout()
plt.savefig('wrench_plot.png')