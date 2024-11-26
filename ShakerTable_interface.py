

'''
Works for the most part- it should update the graph live, which it only does sometimes instead of all the time

Preconditions to run file:
- Python (v3.8.5 or later)
- Tkinter (v8.6 or later)
- Matplotlib (v3.7.5 or later) 

Required updates:
- adding a feature to read txt or csv files for earthquake simulation instead of randomized waveform
- need to add control loop code for the raspberry pi when we connect
- general debugging
- value restriction (frequency must have a positve value and fall within a specific range, etc.)
- as the frequency increases the graph gets weird, maybe scaling/sizing issue?
- the time is not accurate in the graph or in real time, no clue how to fix this

v1.2

'''

import sys
import matplotlib
matplotlib.use('TkAgg')

import tkinter as tk
from tkinter import ttk, messagebox
import numpy as np
import matplotlib.pyplot as plt
from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg
import threading
import time

class ShakerTableGUI:
    def __init__(self, master):
        self.master = master
        master.title("Shaker Table Control")
        master.geometry("1100x700")

        plt.ioff()

        self.is_running = False
        self.simulation_thread = None

        # we'll add the control loop code here when we connect the raspberry pi
        self.connection_var = tk.StringVar(value="Disconnected")

        self.create_gui()

    def create_gui(self):
        # Connection Status frame
        connection_frame = ttk.LabelFrame(self.master, text="Connection Status")
        connection_frame.pack(padx=10, pady=10, fill='x')

        status_label = ttk.Label(connection_frame, textvariable=self.connection_var)
        status_label.pack(side='left', padx=5)

        connect_btn = ttk.Button(connection_frame, text="Connect to Raspberry Pi", 
                                 command=self.simulate_pi_connection)
        connect_btn.pack(side='left', padx=5)

        # Waveform Controls frame
        controls_frame = ttk.LabelFrame(self.master, text="Waveform Controls")
        controls_frame.pack(padx=10, pady=10, fill='x')

        # Waveform Type
        ttk.Label(controls_frame, text="Waveform Type:").pack(side='left', padx=5)
        self.waveform_type = tk.StringVar(value="sine")
        waveform_combo = ttk.Combobox(controls_frame, textvariable=self.waveform_type, 
                                      values=["sine", "earthquake"])
        waveform_combo.pack(side='left', padx=5)

        # Amplitude
        ttk.Label(controls_frame, text="Amplitude:").pack(side='left', padx=5)
        self.amplitude = tk.DoubleVar(value=100)
        amplitude_entry = ttk.Entry(controls_frame, textvariable=self.amplitude, width=10)
        amplitude_entry.pack(side='left', padx=5)

        # Frequency
        ttk.Label(controls_frame, text="Frequency (Hz):").pack(side='left', padx=5)
        self.frequency = tk.DoubleVar(value=1)
        frequency_entry = ttk.Entry(controls_frame, textvariable=self.frequency, width=10)
        frequency_entry.pack(side='left', padx=5)

        # Duration
        ttk.Label(controls_frame, text="Duration (s):").pack(side='left', padx=5)
        self.duration = tk.DoubleVar(value=5)
        duration_entry = ttk.Entry(controls_frame, textvariable=self.duration, width=10)
        duration_entry.pack(side='left', padx=5)

        # graph style, size
        plt.style.use('seaborn')
        self.fig, self.ax = plt.subplots(figsize=(8, 4), dpi=100)
        
        # initializing canvas
        self.canvas = FigureCanvasTkAgg(self.fig, master=self.master)
        self.canvas_widget = self.canvas.get_tk_widget()
        self.canvas_widget.pack(padx=10, pady=10, fill='both', expand=True)

        # initial canvas drawn
        self.canvas.draw()

        # buttons
        buttons_frame = ttk.Frame(self.master)
        buttons_frame.pack(padx=10, pady=10)

        generate_btn = ttk.Button(buttons_frame, text="Generate Waveform", 
                                  command=self.generate_waveform)
        generate_btn.pack(side='left', padx=5)

        start_btn = ttk.Button(buttons_frame, text="Start", command=self.start_simulation)
        start_btn.pack(side='left', padx=5)

        stop_btn = ttk.Button(buttons_frame, text="Stop", command=self.stop_simulation)
        stop_btn.pack(side='left', padx=5)

    def simulate_pi_connection(self):
        self.connection_var.set("Connected")
        messagebox.showinfo("Connection", "Connected to Raspberry Pi (Simulated)")

    def generate_waveform(self):
        try:
            # clear last plot
            self.ax.clear()

            # generate waveform data
            time_array = np.linspace(0, self.duration.get(), 500)
            
            if self.waveform_type.get() == 'sine':
                waveform = self.amplitude.get() * np.sin(2 * np.pi * self.frequency.get() * time_array)
            else:  # earthquake
                waveform = (self.amplitude.get() * 
                            np.sin(2 * np.pi * self.frequency.get() * time_array) * 
                            np.exp(-0.1 * time_array) * 
                            (1 + 0.2 * np.random.random(time_array.shape))) #randomized waveform for now

            # plot
            self.ax.plot(time_array, waveform)
            self.ax.set_title('Waveform Visualization')
            self.ax.set_xlabel('Time (s)')
            self.ax.set_ylabel('Amplitude')
            
            # draw canvas again
            self.canvas.draw()

            # save waveform for simulation
            self.time_array = time_array
            self.waveform = waveform

        except Exception as e:
            messagebox.showerror("Waveform Generation Error", str(e))

    def start_simulation(self):
        if not hasattr(self, 'time_array') or not hasattr(self, 'waveform'): 
            messagebox.showwarning("Warning", "Please generate a waveform first!")
            return

        if self.is_running:
            return  # nothing, already running

        self.is_running = True
        self.simulation_thread = threading.Thread(target=self.run_simulation, daemon=True)
        self.simulation_thread.start()

    def stop_simulation(self):
        self.is_running = False
        if self.simulation_thread is not None:
            self.simulation_thread.join()  # wait for simulation to stop
        print("Simulation stopped")

    def run_simulation(self): # something here isnt working right
        try:
            # update the waveform plot at each time step
            start_time = time.time()

            for i in range(1, len(self.time_array)):  # we start from 1 (avoid empty plot)
                if not self.is_running:
                    break

                # plot the complete waveform up to the current point
                self.ax.clear()  # clear last plot
                self.ax.plot(self.time_array[:i], self.waveform[:i], color='blue')
                self.ax.set_title('Waveform Visualization')
                self.ax.set_xlabel('Time (s)')
                self.ax.set_ylabel('Amplitude')
                
                # update the canvas
                self.master.after(0, self.update_canvas, i)

                # control speed of simulation
                time.sleep(self.time_array[1] - self.time_array[0])  # time step delay

            self.is_running = False
            print("Simulation finished")
        
        except Exception as e:
            print(f"Simulation error: {e}")
            self.is_running = False

    def update_canvas(self, i):
        # updates canvas
        self.canvas.draw()

if __name__ == "__main__":
    # system info, not necessary but good for checking initial preconditions
    print(f"Python version: {sys.version}")
    print(f"Matplotlib version: {matplotlib.__version__}")
    print(f"Tkinter version: {tk.TkVersion}")

    root = tk.Tk()
    app = ShakerTableGUI(root)
    root.mainloop()
