# Main Functions
import numpy as np
import graph_tool.all as gt
import sparse as sp
import random

# GUI and visualization
from gi.repository import Gtk, Gdk, GdkPixbuf, GObject, GLib
from matplotlib import pyplot as plt
plt.use("TkAgg")
from matplotlib.backends.backend_tkagg import FigureCanvasTk, NavigationToolbar2Tk
from matplotlib.figure import Figure
import mpl_toolkits.mplot3d.axes3d as p3
import tikinter as tk
from tkinter import ttk

import sys

class Rias:


    # Constructors ------------------------------------------------------------

    def __init__(self, graph, update_rules, dt=1, alpha=1):
        self.G = graph
        self.num_v = self.G.num_vertices()
        self.out_degrees = self.G.get_out_degrees(np.arange(self.num_v))
        self.update_rules = update_rules

        self.timestep = 0
        self.t = 0
        self.delta_time = dt # only use numbers 1 / k where k is a natural number
        self.time_dilation = 1 / self.delta_time
        self.alpha = alpha

        # dictionary of 1 dimensional state vectors
        self.X = {key: value for key, value in self.G.vp.items()}
        # dictionary of 1 + 1 dimensional History matrices for each state
        self.H = {key: np.array([value.get_array()]) for key, value in self.X.items()}
        # 2 dimensional Adjacency matrix
        self.A = gt.adjacency(self.G, self.G.ep["weight"]).toarray()
        self.max_size_history= int(np.amax(self.A) * self.time_dilation)
        # 2 + 1 dimensional Laplacian matrix
        self.L = self.create_laplacian()

        #self.win = self.create_window()



    @classmethod
    def init_random(cls, num_attributes, min_vertices, max_vertices, min_attribute, max_attribute, min_edges, max_edges):
        g = gt.Graph()

        num_vertices = random.randint(min_vertices, max_vertices)
        for _ in range(num_vertices):
            g.add_vertices(random.uniform(min_attribute, max_attribute))

        edges = []
        num_edges = random.randint(min_edges, max_edges)
        for _ in range(num_edges):
            edges.append((random.randint(0, num_vertices), random.randint(0, num_vertices)))
        g.add_edges(edges)

        return cls(g)

    @classmethod
    def init_lattice_2d_4n(cls, lattice, periodic=True):
        length = len(lattice)
        width = len(lattice[0])
        g = gt.Lattice([length, width], periodic=periodic)
        num_vertices = g.num_vertices()
        vals = [l for lst in lattice for l in lst]
        g.vp["state"] = g.new_vp("double", vals=vals)
        return cls(g)

    @classmethod
    def init_lattice_2d_8n(cls, lattice, periodic=True):
        length = len(lattice)
        width = len(lattice[0])
        g = gt.Lattice([length, width], periodic=periodic)
        num_vertices = g.num_vertices()
        vals = [l for lst in lattice for l in lst]
        g.vp["state"] = g.new_vp("double", vals=vals)
        for i in range(length - (0 if periodic else 1)):
            for j in range(width - (0 if periodic else 1)):
                vertex_current = i * length + j
                vertex_se = (vertex_current + length + 1) % num_vertices
                vertex_sw = (vertex_current + length - 1) % num_vertices
                g.add_edge_list([(vertex_current, vertex_se), (vertex_current, vertex_sw)])
        return cls(g)

    @classmethod
    def init_lattice_1d(cls, N, vp_dict, update_rules, dt=1, alpha=1, periodic=True):
        g = gt.lattice([N], periodic=periodic)
        g.set_directed(False)
        for prop, vals in vp_dict.items():
            g.vp[prop] = g.new_vp("double", vals=vals)
        g.ep["weight"] = g.new_ep("double", val=2)
        #g.ep["weight"] = g.new_ep("double", vals=[1 if i < 400 else 2 for i in range(1000)])
        if not periodic:
            g.self_loops = True
            g.add_edge_list([(0, 0), (N-1, N-1)])
        return cls(g, update_rules, dt, alpha)



    # Core functions -------------------------------------------------------

    def update_reality(self):
        """Updates self in accordance to given update rules.
        """

        for rule in self.update_rules:
            first_property = rule[0] # target to update
            second_property = rule[1] # source to take the second derivative of
            n_antiderivatives = rule[2] # how many antiderivatives first_property has
            constant = rule[3] # how many antiderivatives first_property has

            # find delta to update first_property's first derivative wrt time
            # using second_property's second derivative (??) wrt space
            current_state = self.X[second_property].a

            # Setting the endpoints
            #self.X[first_property][0] = 0.0
            #self.X[first_property][self.num_v-1] = 0.0
            #self.X[second_property][0] =400
            #self.X[second_property][self.num_v-1] = 600

            deltas = np.zeros(self.num_v)
            for i, state in enumerate(reversed(self.H[second_property])):
                deltas += self.L[i].dot(state)
            #deltas -= current_state

            # Adjust velocities using data from positions
            self.X[first_property].a += constant * deltas * self.alpha

            # FIX!!-
            # update second property's antiderivatives using updated first_property
            for i in range(n_antiderivatives):
                self.X[second_property].a += self.X[first_property].a

                #self.X[first_property].a -= constant * deltas * self.alpha / 2

            #for i in range(n_antiderivatives+1):
            self.H[first_property] = np.vstack((self.H[first_property],
                                                self.X[first_property].a))
            self.H[second_property] = np.vstack((self.H[second_property],
                                                self.X[second_property].a))

            if len(self.H[first_property]) > self.max_size_history:
                self.H[first_property] = np.delete(self.H[first_property], (0), axis=0)
            if len(self.H[second_property]) > self.max_size_history:
                self.H[second_property]= np.delete(self.H[second_property], (0), axis=0)



        self.t += self.delta_time
        self.timestep += 1

    def create_laplacian(self):
        coordinates = []
        data = []
        for i, row in enumerate(self.A):
            for j, edge_length in enumerate(row):
                if edge_length:
                    coordinates.append((edge_length * self.time_dilation - 1, i, j))
                    data.append(-1)# / self.out_degrees[j])# / self.time_dilation)

        # diagonal values denoting in-degree of weight w
        for w in range(int(self.max_size_history // self.time_dilation)):
            degrees = self.G.get_total_degrees(np.arange(self.num_v))
            self.G.ep[str(w)] = self.G.new_ep("bool", [1 if i == w + 1 else 0 for w in self.G.ep["weight"]])
            self.G.set_edge_filter(self.G.ep[str(w)])
            for i, d in enumerate(degrees):
                coordinates.append((w * self.time_dilation, i, i))
                data.append(d)
        self.G.set_edge_filter(None)

        coordinates = list(zip(*coordinates))
        U = sp.COO(coordinates, data, shape=(self.max_size_history, self.num_v, self.num_v))
        return U


    # Visualization -----------------------------------------------------------

    def create_window(self):
        pos = gt.planar_layout(self.G)
        win = gt.GraphWindow(self.G, pos, geometry=(500, 100),
                             vertex_fill_color=self.G.vp["position"])

        return win

    def update_window(self):
        self.update_reality()
        self.win.graph.regenerate_surface()
        self.win.graph.queue_draw()
        return True

    def animate_graph(self):
        # Bind the function above as an 'idle' callback.
        cid = GLib.idle_add(self.update_window)

        # We will give the user the ability to stop the program by closing the window.
        self.win.connect("delete_event", Gtk.main_quit)

        # Actually show the window, and start the main loop.
        self.win.show_all()
        Gtk.main()#



class Visualization(tk.Tk):
    def __init__(self, *args, **kwargs):
        tk.Tk.__init__(self, *args, **kwargs)

        tk.Tk.iconbitmap(self)#, default="idk.jpg")
        tk.Tk.wm_title(self, "RIAS")

        container = tk.Frame(self)
        container.pack(side="top", fill="both", expand=True)
        container.grid_rowconfigure(0, weight=1)
        container.grid_colconfigure(0, weight=1)

        self.frames = {}

class StartPage(tk.Frame):
    def __init__(self, parent, controller):
        tk.Frame.__init(self, parent)
        label = tk.Label(self, text="RIAS")
        label.pack(pady=10, padx=10)

        button = ttk.Button(self, text="Go to 1st page",
                            command=lambda:controller.show_frame(FirstPage))
        button.pack()


class FirstPage(tk.Frame):
    def __init__(self, parent, controller):
        pause = False

        tk.Frame.__init__(self, parent)
        label = tk.Label(self, text="RIAS")
        label.pack(pady=10, padx=10)

        button1 = ttk.Button(self, text="Back to Home",
                             command=lambda: controller.show_fram(StartPage))
        button1.pack()



        fig = plt.figure()
        fig.canvas.mpl_connect('button_press_event', self.onClick)
        ax = plt.axes(xlim=(0, self.num_v), ylim=(-1000, 1000))
        line, = ax.plot([], [], lw=1)

        anim = animation.FuncAnimation(fig, self.animate, init_func=self.init_line,
                                    frames=200, interval=20, blit=True)
        plt.show()


    # initialization function: plot the background of each frame
    def init_line(self):
        line.set_data([], [])
        return line,

    def onClick(self, event):
        global pause
        pause = True
#
    # animation function.  This is called sequentially
    def animate(self, i):
        if not pause:
            self.update_reality()
            ax.annotate('timestep = ' + str(self.timestep), (100, 100))
            x = np.linspace(0, self.num_v, self.num_v)
            y = self.X['position'].a
            line.set_data(x, y)
        return line,



def main():
    if len(sys.argv) != 2:
        raise Exception('Only one argument, please!')
    arg = sys.argv[1]

    if arg == 'wave':


        #initial_states = {'position': (np.random.rand(1000) - 0.5) * 1000,
        #                  'velocity': np.concatenate(((np.random.rand(500) - 0.5) * 5, np.zeros((500))))}
        #initial_states = {'position': np.fromfunction(lambda x: 500*np.sin(np.pi*x/500 + 1000), (1000,)),
        #                    'velocity':np.fromfunction(lambda x: np.cos(np.pi*x/50), (1000,))}
        initial_states = {'position': np.concatenate([np.zeros(100) + 100, [200 - i for i in range(200)], np.zeros(700)+500]),
                            'velocity':np.zeros(1000)}
        #initial_states = {'position': np.fromfunction(lambda x: 10*np.sin(np.pi*x/5) + 10, (10,)),
        #                    'velocity':np.fromfunction(lambda x: 10*np.cos(np.pi*x/5), (10,))}
        #initial_states = {'position': np.concatenate([np.zeros(100), np.fromfunction(lambda x: 100*np.sin(np.pi*x/100), (100,))]),
        #                'velocity':np.zeros(1000)}
        reality = Rias.init_lattice_1d(1000, initial_states, [('velocity', 'position', 1, -1)],
                                   dt = 1, alpha = 1/5, periodic=True)
        reality.animate_plt()
    elif arg == 'heat':
        initial_states = {'position': (np.random.rand(500) - 0.5) * 500 + 500}
        reality = Rias.init_lattice_1d(1000, initial_states, [('position', 'position', 0, -1)],
                                    dt = 1, alpha = 1/10, periodic=True)
        reality.animate_plt()
    elif arg == '3d':
        pass

def main():







if __name__ == '__main__':
    main()
