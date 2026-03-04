import tkinter as tk
from tkinter import ttk
import serial
import serial.tools.list_ports
import matplotlib.pyplot as plt
from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg
from collections import deque

# ================== CONFIG ==================
MAX_POINTS = 200
ser = None

# ================== TKINTER WINDOW ==================
root = tk.Tk()
root.title("Pressure Monitor - hello gigin")
root.geometry("950x650")

# ================== FUNCTIONS ==================
def get_ports():
    ports = serial.tools.list_ports.comports()
    return [port.device for port in ports]

def connect_serial():
    global ser
    try:
        ser = serial.Serial(port_combo.get(), int(baud_combo.get()), timeout=0)
        status_label.config(text="Connected", fg="green")
    except Exception as e:
        status_label.config(text="Connection Failed", fg="red")
        print(e)

def disconnect_serial():
    global ser
    if ser and ser.is_open:
        ser.close()
        status_label.config(text="Disconnected", fg="orange")

# ================== TOP FRAME ==================
top_frame = tk.Frame(root)
top_frame.pack(pady=10)

port_combo = ttk.Combobox(top_frame, values=get_ports(), width=12)
port_combo.pack(side=tk.LEFT, padx=5)

tk.Button(top_frame, text="Refresh",
          command=lambda: port_combo.config(values=get_ports())
          ).pack(side=tk.LEFT, padx=5)

baud_combo = ttk.Combobox(top_frame,
                          values=["9600", "19200", "38400", "57600", "115200"],
                          width=10)
baud_combo.set("115200")
baud_combo.pack(side=tk.LEFT, padx=5)

tk.Button(top_frame, text="Connect", command=connect_serial).pack(side=tk.LEFT, padx=5)
tk.Button(top_frame, text="Disconnect", command=disconnect_serial).pack(side=tk.LEFT, padx=5)

status_label = tk.Label(root, text="Not Connected", fg="red")
status_label.pack()

# ================== VALUE LABELS ==================
value_frame = tk.Frame(root)
value_frame.pack(pady=5)

label_s1 = tk.Label(value_frame, text="Sensor 1: 0", font=("Arial", 14))
label_s1.pack(side=tk.LEFT, padx=20)

label_s2 = tk.Label(value_frame, text="Sensor 2: 0", font=("Arial", 14))
label_s2.pack(side=tk.LEFT, padx=20)

label_s3 = tk.Label(value_frame, text="Sensor 3: 0", font=("Arial", 14))
label_s3.pack(side=tk.LEFT, padx=20)

# ================== DATA STORAGE ==================
data1 = deque([0]*MAX_POINTS, maxlen=MAX_POINTS)
data2 = deque([0]*MAX_POINTS, maxlen=MAX_POINTS)
data3 = deque([0]*MAX_POINTS, maxlen=MAX_POINTS)

# ================== MATPLOTLIB ==================
fig, ax = plt.subplots()

line1, = ax.plot(data1, label="Sensor 1")
line2, = ax.plot(data2, label="Sensor 2")
line3, = ax.plot(data3, label="Sensor 3")

ax.set_ylim(0, 400)
ax.set_xlim(0, MAX_POINTS)
ax.set_title("Pressure (mmHg)")
ax.legend()

canvas = FigureCanvasTkAgg(fig, master=root)
canvas.get_tk_widget().pack(fill=tk.BOTH, expand=True)

# ================== UPDATE LOOP ==================
def update_plot():
    global ser

    if ser and ser.is_open:
        try:
            if ser.in_waiting:

                # Baca 3 BARIS dari Mega (tanpa ubah Mega)
                s1_raw = ser.readline().decode(errors='ignore').strip()
                s2_raw = ser.readline().decode(errors='ignore').strip()
                s3_raw = ser.readline().decode(errors='ignore').strip()

                if s1_raw and s2_raw and s3_raw:
                    s1 = float(s1_raw)
                    s2 = float(s2_raw)
                    s3 = float(s3_raw)

                    # update label
                    label_s1.config(text=f"Sensor 1: {s1:.3f}")
                    label_s2.config(text=f"Sensor 2: {s2:.3f}")
                    label_s3.config(text=f"Sensor 3: {s3:.3f}")

                    # update grafik
                    data1.append(s1)
                    data2.append(s2)
                    data3.append(s3)

        except Exception as e:
            print("Error:", e)

    line1.set_ydata(data1)
    line2.set_ydata(data2)
    line3.set_ydata(data3)

    canvas.draw_idle()

    root.after(100, update_plot)

# start loop
update_plot()

root.mainloop()