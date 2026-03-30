#C:\Users\gigin\AppData\Local\Programs\Python\Python311\python.exe GuiPWM_3Sensor1_2.py
import tkinter as tk
from tkinter import ttk, filedialog, messagebox
import pandas as pd
import serial
import serial.tools.list_ports
import threading
import time
import matplotlib.pyplot as plt
from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg
from collections import deque

# ================= GLOBAL =================
ser_tx = None
ser_rx = None
df = None
running = False
app_running = True
MAX_POINTS = 200

# buffer untuk RX 3 baris
buffer_lines = []

# ================= SERIAL =================
def get_ports():
    return [p.device for p in serial.tools.list_ports.comports()]

def refresh_ports():
    ports = get_ports()
    port_tx['values'] = ports
    port_rx['values'] = ports

def connect_tx():
    global ser_tx
    try:
        ser_tx = serial.Serial(port_tx.get(), int(baud_tx.get()), timeout=1)
        status_tx.config(text="TX Connected", fg="green")
    except Exception as e:
        status_tx.config(text="TX Failed", fg="red")
        print(e)

def disconnect_tx():
    global ser_tx
    if ser_tx and ser_tx.is_open:
        ser_tx.close()
        status_tx.config(text="TX Disconnected", fg="orange")

def connect_rx():
    global ser_rx
    try:
        ser_rx = serial.Serial(port_rx.get(), int(baud_rx.get()), timeout=1)
        status_rx.config(text="RX Connected", fg="green")
    except Exception as e:
        status_rx.config(text="RX Failed", fg="red")
        print(e)

def disconnect_rx():
    global ser_rx
    if ser_rx and ser_rx.is_open:
        ser_rx.close()
        status_rx.config(text="RX Disconnected", fg="orange")

# ================= LOAD EXCEL =================
def load_excel():
    global df
    file_path = filedialog.askopenfilename(filetypes=[("Excel", "*.xlsx")])
    if not file_path:
        return

    try:
        df = pd.read_excel(file_path, header=None)

        if len(df) < 3:
            messagebox.showerror("Error", "Minimal 3 baris (PWM1, PWM2, PWM3)")
            return

        total = min(len(df.iloc[0]), len(df.iloc[1]), len(df.iloc[2]))
        data_label.config(text=f"Data: {total} samples")

    except Exception as e:
        messagebox.showerror("Error", str(e))

# ================= SEND PWM =================
def send_data():
    global running

    if df is None or ser_tx is None:
        messagebox.showwarning("Warning", "Load Excel & Connect TX dulu")
        return

    running = True
    status_tx.config(text="TX Running...", fg="blue")

    row1 = df.iloc[0].fillna(0)
    row2 = df.iloc[1].fillna(0)
    row3 = df.iloc[2].fillna(0)

    total = min(len(row1), len(row2), len(row3))

    try:
        delay = float(delay_entry.get())
    except:
        delay = 0.01

    while running:
        for i in range(total):
            if not running:
                break

            if not ser_tx or not ser_tx.is_open:
                break

            p1 = max(0, min(255, int(row1[i])))
            p2 = max(0, min(255, int(row2[i])))
            p3 = max(0, min(255, int(row3[i])))

            try:
                ser_tx.write(f"{p1} {p2} {p3}\n".encode())
            except:
                break

            time.sleep(delay)

        if not loop_var.get():
            break

    running = False
    status_tx.config(text="TX Stopped", fg="orange")

def start_send():
    threading.Thread(target=send_data, daemon=True).start()

def stop_send():
    global running
    running = False

# ================= MONITOR =================
data1 = deque([0]*MAX_POINTS, maxlen=MAX_POINTS)
data2 = deque([0]*MAX_POINTS, maxlen=MAX_POINTS)
data3 = deque([0]*MAX_POINTS, maxlen=MAX_POINTS)

def update_plot():
    global ser_rx, app_running, buffer_lines

    if not app_running:
        return

    if ser_rx and ser_rx.is_open:
        try:
            while ser_rx.in_waiting:
                line = ser_rx.readline().decode(errors='ignore').strip()
                print("RX:", line)

                if line:
                    buffer_lines.append(line)

                # proses tiap 3 data
                while len(buffer_lines) >= 3:
                    try:
                        s1 = float(buffer_lines.pop(0))
                        s2 = float(buffer_lines.pop(0))
                        s3 = float(buffer_lines.pop(0))

                        label_s1.config(text=f"S1: {s1:.1f}")
                        label_s2.config(text=f"S2: {s2:.1f}")
                        label_s3.config(text=f"S3: {s3:.1f}")

                        data1.append(s1)
                        data2.append(s2)
                        data3.append(s3)

                    except:
                        buffer_lines.clear()

        except Exception as e:
            print("RX Error:", e)

    # ===== UPDATE GRAFIK =====
    x = list(range(len(data1)))

    y1 = list(data1)
    y2 = list(data2)
    y3 = list(data3)

    line1.set_data(x, y1)
    line2.set_data(x, y2)
    line3.set_data(x, y3)

    ax.set_xlim(0, MAX_POINTS)

    if len(y1) > 0:
        ymin = min(y1 + y2 + y3) - 5
        ymax = max(y1 + y2 + y3) + 5
        ax.set_ylim(ymin, ymax)

    canvas.draw()

    root.after(100, update_plot)

# ================= CLOSE =================
def on_closing():
    global app_running, ser_tx, ser_rx

    app_running = False

    if ser_tx and ser_tx.is_open:
        ser_tx.close()

    if ser_rx and ser_rx.is_open:
        ser_rx.close()

    root.destroy()

# ================= GUI =================
root = tk.Tk()
root.title("PWM + Pressure Monitor (2 Serial) - hello gigin")
root.geometry("1100x650")

root.protocol("WM_DELETE_WINDOW", on_closing)

# ===== TOP =====
top = tk.Frame(root)
top.pack(pady=5)

tk.Label(top, text="PWM TX").grid(row=0, column=0)
port_tx = ttk.Combobox(top, width=10)
port_tx.grid(row=0, column=1)

baud_tx = ttk.Combobox(top, values=["9600","115200"], width=8)
baud_tx.set("115200")
baud_tx.grid(row=0, column=2)

tk.Button(top, text="Connect TX", command=connect_tx).grid(row=0, column=3)
tk.Button(top, text="Disconnect TX", command=disconnect_tx).grid(row=0, column=4)

status_tx = tk.Label(top, text="TX Off", fg="red")
status_tx.grid(row=0, column=5)

tk.Label(top, text="Sensor RX").grid(row=1, column=0)
port_rx = ttk.Combobox(top, width=10)
port_rx.grid(row=1, column=1)

baud_rx = ttk.Combobox(top, values=["9600","115200"], width=8)
baud_rx.set("115200")
baud_rx.grid(row=1, column=2)

tk.Button(top, text="Connect RX", command=connect_rx).grid(row=1, column=3)
tk.Button(top, text="Disconnect RX", command=disconnect_rx).grid(row=1, column=4)

status_rx = tk.Label(top, text="RX Off", fg="red")
status_rx.grid(row=1, column=5)

tk.Button(top, text="Refresh COM", command=refresh_ports, bg="yellow").grid(row=0, column=6, rowspan=2, padx=10)

# ===== MAIN =====
main = tk.Frame(root)
main.pack(fill="both", expand=True)

# LEFT
left = tk.Frame(main)
left.pack(side=tk.LEFT, fill=tk.Y, padx=10)

tk.Label(left, text="PWM SENDER", font=("Arial", 12, "bold")).pack(pady=5)

tk.Button(left, text="Load Excel", command=load_excel).pack(pady=5)
data_label = tk.Label(left, text="No Data")
data_label.pack()

tk.Label(left, text="Delay (s)").pack()
delay_entry = tk.Entry(left, width=6)
delay_entry.insert(0, "0.01")
delay_entry.pack()

loop_var = tk.BooleanVar()
tk.Checkbutton(left, text="Loop", variable=loop_var).pack()

tk.Button(left, text="Start", bg="green", fg="white", command=start_send).pack(pady=5)
tk.Button(left, text="Stop", bg="red", fg="white", command=stop_send).pack(pady=5)

# RIGHT
right = tk.Frame(main)
right.pack(side=tk.RIGHT, fill=tk.BOTH, expand=True)

tk.Label(right, text="PRESSURE MONITOR", font=("Arial", 12, "bold")).pack()

label_s1 = tk.Label(right, text="S1: 0", font=("Arial", 12))
label_s1.pack()

label_s2 = tk.Label(right, text="S2: 0", font=("Arial", 12))
label_s2.pack()

label_s3 = tk.Label(right, text="S3: 0", font=("Arial", 12))
label_s3.pack()

fig, ax = plt.subplots()
line1, = ax.plot([], [], label="S1")
line2, = ax.plot([], [], label="S2")
line3, = ax.plot([], [], label="S3")

ax.legend()

canvas = FigureCanvasTkAgg(fig, master=right)
canvas.get_tk_widget().pack(fill=tk.BOTH, expand=True)

# INIT
refresh_ports()
update_plot()

root.mainloop()