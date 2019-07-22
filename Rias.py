import numpy as np
import graph_tool.all as gt
import sparse as sp
import random
from matplotlib import pyplot as plt
from matplotlib import animation
from gi.repository import Gtk, Gdk, GdkPixbuf, GObject, GLib


###############################################################################
# /? [- /\ |_ | ~|~ `/   | _\~ |\| ~|~   /\   _\~ | |\/| |_| |_ /\ ~|~ | () |\|
###############################################################################
# #############################################################################
# #############################################################################
###############################################################################

class Rias:


    # Constructors ------------------------------------------------------------

    def __init__(self, graph, update_rules, dt=1, ds=1):
        self.G = graph
        self.num_v = self.G.num_vertices()
        self.in_degrees = self.G.get_in_degrees(np.arange(self.num_v))
        self.update_rules = update_rules

        self.timestep = 0
        self.t = 0
        self.delta_time = dt # only use numbers 1 / k where k is a natural number
        self.time_dilation = 1 / self.delta_time
        self.delta_space = ds # only use numbers 1 / k where k is a natural number
        self.space_dilation = 1 // self.delta_space

        # dictionary of 1 dimensional state vectors
        self.X = {key: value for key, value in self.G.vp.items()}
        # dictionary of 1 + 1 dimensional History matrices for each state
        self.H = {key: np.array([value.get_array()]) for key, value in self.X.items()}
        # 2 dimensional Adjacency matrix
        self.A = gt.adjacency(self.G, self.G.ep["weight"]).toarray()
        self.max_size_history= int(np.amax(self.A) * self.time_dilation)
        # 2 + 1 dimensional Laplacian matrix
        self.L = self.create_laplacian()

        self.win = self.create_window()



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
    def init_lattice_1d(cls, N, vp_dict, update_rules, dt=1, ds=1, periodic=True):
        g = gt.lattice([N], periodic=periodic)
        for prop, vals in vp_dict.items():
            g.vp[prop] = g.new_vp("double", vals=vals)
        g.ep["weight"] = g.new_ep("double", val=1)
        #g.ep["weight"] = g.new_ep("double", vals=[1 if i < 400 else 2 for i in range(1000)])
        if not periodic:
            g.self_loops = True
            g.add_edge_list([(0, 0), (N-1, N-1)])
        return cls(g, update_rules, dt, ds)



    # Core functions -------------------------------------------------------

    def update_reality(self):
        for rule in self.update_rules:
            first_property = rule[0] # target to update
            second_property = rule[1] # source to take the second derivative of
            n_antiderivatives = rule[2] # how many antiderivatives first_property has

            # find delta to update first_property's first derivative wrt time
            # using second_property's second derivative (??) wrt space
            current_state = self.X[second_property].a

            #self.X[second_property][0] = 0.0
            #self.X[first_property][0] = 0.0
            #self.X[second_property][self.num_v-1] = 0.0
            #self.X[first_property][self.num_v-1] = 0.0

            deltas = np.zeros(self.num_v)
            for i, state in enumerate(reversed(self.H[second_property])):
                deltas += self.L[i].dot(state)
            #deltas -= current_state

            # Adjust velocities using data from positions
            self.X[first_property].a += deltas * self.delta_space

            # FIX!!-
            # update second property's antiderivatives using updated first_property
            for i in range(n_antiderivatives):
                self.X[second_property].a += self.X[first_property].a

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
                coordinates.append((edge_length * self.time_dilation - 1, i, j))
                data.append(-1)# / self.out_degrees[j] / self.time_dilation)

        # diagonal values denoting in-degree of weight w
        for w in range(int(self.max_size_history / self.time_dilation)):
            self.G.ep[str(i)] = self.G.new_ep("bool", [True if i == w + 1 else False for w in self.G.ep["weight"]])
            self.G.set_edge_filter(self.G.ep[str(i)])
            in_degrees = self.G.get_in_degrees(np.arange(self.num_v))
            for i, d in enumerate(in_degrees):
                coordinates.append((w, i, i))
                data.append(w)
        self.G.set_edge_filter(None)

        coordinates = list(zip(*coordinates))
        U = sp.COO(coordinates, data, shape=(self.max_size_history, self.num_v, self.num_v))
        return U


    # Visualization -----------------------------------------------------------

    def create_window(self):
        pos = gt.planar_layout(self.G)
        win = gt.GraphWindow(self.G, pos, geometry=(100, 100),
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
        Gtk.main()

    def animate_plt(self):
        fig = plt.figure()
        ax = plt.axes(xlim=(0, 1000), ylim=(-1000, 1000))
        line, = ax.plot([], [], lw=1)

        pause = False

        def onClick(event):
            global pause
            pause = True
        fig.canvas.mpl_connect('button_press_event', onClick)

        # initialization function: plot the background of each frame
        def init():
            line.set_data([], [])
            return line,

        # animation function.  This is called sequentially
        def animate(i):
            if not pause:
                self.update_reality()
                ax.annotate('timestep = ' + str(self.timestep), (100, 100))
                x = np.linspace(0, 1000, 1000)
                y = self.X['position'].get_array()
                line.set_data(x, y)
            return line,

        # call the animator.  blit=True means only re-draw the parts that have changed.
        anim = animation.FuncAnimation(fig, animate, init_func=init,
                                    frames=200, interval=20, blit=True)
        plt.show()


def main():
    #initial_states = {'position': (np.random.rand(1000) - 0.5) * 10,
    #                  'velocity': np.concatenate(((np.random.rand(500) - 0.5) * 5, np.zeros((500))))}
    #np.concatenate(([0], initial_states['position'], [0]))
    #np.concatenate(([0], initial_states['velocity'], [0]))
    initial_states = {'position': np.fromfunction(lambda x: 10*np.sin(np.pi*x/500) + 1000, (1000,)),
                        'velocity':np.fromfunction(lambda x: 10*np.cos(np.pi*x/500) + 25, (1000,))}

    initial_states = {'position': np.concatenate([np.zeros(100) + 100, [200 - i for i in range(200)], np.zeros(700)+500]),
                        'velocity':np.zeros(1000)}
    reality = Rias.init_lattice_1d(1000, initial_states, [('velocity', 'position', 1)],
                                   dt = 1, ds = 1/100, periodic=False)


    #initial_states = {'position': (np.random.rand(1000) - 0.5) * 500}
    #reality = Rias.init_lattice_1d(1000, initial_states, [('position', 'position', 0, -1)],
    #                               dt = 1/50, ds = 1/50, periodic=True)

    print('asdfafd')
    reality.animate_plt()




if __name__ == '__main__':
    main()
