import quantum_graph as qg
import numpy as np

import tkinter as tk
from tkinter import ttk

import matplotlib
matplotlib.use("TkAgg")
from matplotlib import pyplot as plt
plt.style.use("dark_background")
from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg, NavigationToolbar2Tk
from matplotlib import animation
import mpl_toolkits.mplot3d.axes3d as p3

from gi.repository import Gtk, Gdk, GdkPixbuf, GObject, GLib


class Initializer(tk.Tk):
    def __init__(self, *args, **kwargs):
        tk.Tk.__init__(self, *args, **kwargs)

        tk.Tk.iconbitmap(self)#, default="idk.jpg")
        tk.Tk.wm_title(self, "RIAS")

        container = tk.Frame(self)
        container.pack(side="top", fill="both", expand=True)
        container.grid_rowconfigure(0, weight=1)
        container.grid_columnconfigure(0, weight=1)

        self.frames = {}
        for F in (FirstView,):
            frame = F(container, self)
            self.frames[F] = frame
            frame.grid(row=0, column=0, sticky="nesw")

        self.show_frame(FirstView)

    def show_frame(self, cont):
        frame = self.frames[cont]
        frame.tkraise()


class FirstView(tk.Frame):
    def __init__(self, parent, controller):
        tk.Frame.__init__(self, parent)
        label = tk.Label(self, text="RIAS")
        label.pack(pady=10, padx=10)

        button1 = ttk.Button(self, text="start/stop",
                            command=self.start_stop)
        button1.pack()

        self.textBox=tk.Text(self, height=2, width=10)
        self.textBox.pack()
        buttonCommit=tk.Button(self, height=1, width=10, text="Commit",
                            command=lambda: self.retrieve_input())
        buttonCommit.pack()

        initial_states = {'position': np.concatenate([np.zeros(100) + 100, [200 - i for i in range(200)], np.zeros(700)+500]),
                            'velocity':np.zeros(1000)}
        self.pause = False

        self.qg = qg.QuantumGraph.init_lattice_1d(1000, initial_states, [('velocity', 'position', 1, -1)],
                                dt = 1, alpha = 1/5, periodic=True)



        self.fig = plt.figure()
        self.ax = plt.axes(xlim=(0, self.qg.num_v), ylim=(-1000, 1000))
        self.line, = self.ax.plot([], [], lw=1)
        self.timestamp = self.ax.annotate('timestep = ' + str(self.qg.timestep), xy=(0.1, 0.5), xycoords='figure fraction')
        self.timestamp.set_animated(True)


        canvas = FigureCanvasTkAgg(self.fig, self)
        canvas.draw()
        canvas.get_tk_widget().pack(side=tk.TOP, fill=tk.BOTH, expand=True)

        toolbar = NavigationToolbar2Tk(canvas, self)
        toolbar.update()
        canvas._tkcanvas.pack(side=tk.TOP, fill=tk.BOTH, expand=True)

        anim = animation.FuncAnimation(self.fig, self.animate, init_func=self.init_plot,
                                    frames=200, interval=20, blit=True)


    def retrieve_input(self):
        inputValue=self.textBox.get("1.0","end-1c")

    def start_stop(self):
        self.pause = not self.pause

    # initialization function: plot the background of each frame
    def init_plot(self):
        self.line.set_data([], [])
        return self.line, self.timestamp

    # animation function.  This is called sequentially
    def animate(self, i):
        if not self.pause:
            self.qg.update_graph()
            self.timestamp.set_text('timestep = ' + str(self.qg.timestep))
        x = np.linspace(0, self.qg.num_v, self.qg.num_v)
        y = self.qg.X['position'].a
        self.line.set_data(x, y)
        return self.line, self.timestamp




