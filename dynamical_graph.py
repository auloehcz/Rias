import numpy as np
import graph_tool.all as gt
import sparse

MAX_HISTORY_SIZE = 50

class DynamicalGraph:

    # Constructors ------------------------------------------------------------

    def __init__(self, graph, space_kernel_funcs, time_kernel_funcs, dt=1):
        self.G = graph
        self.num_v = self.G.num_vertices()
        self.out_degrees = self.G.get_out_degrees(np.arange(self.num_v))
        self.timestep = 0
        self.t = 0
        self.dt = dt

        # dictionary of dictionaries of functions
        self.space_kernels_func = space_kernel_funcs
        self.time_kernel_funcs = time_kernel_funcs

        # dictionary of 1 dimensional state vectors
        self.X = {key: value for key, value in self.G.vp.items()}
        # dictionary of 1 + 1 dimensional History matrices for each state
        self.H = {key: np.array([value.get_array()]) for key, value in self.X.items()}
        # 2 dimensional weighted adjacency matrix
        self.A = gt.adjacency(self.G, self.G.ep["weight"]).toarray()

        # dictionary of dictionaries of 2 + 1 dimensional update matrices
        # {prop0: {prop0: U00, prop1: U01, ..., propN: U0N},
        #  prop1: {prop0: U10, prop1: U11, ..., propN: U1N},
        #  ...
        #  propN: {prop0: UN0, prop1: UN1, ..., propN: UNN}}
        self.U = self.create_update_matrix()

    # Core functions ----------------------------------------------------------

    def update_graph(self):
        for target, H in self.H.items():
            new_state = np.zeros(self.num_v)
            for U in self.U[target].values():
                for time_lookback, x in enumerate(H):
                    new_state += U[time_lookback].dot(x)
            self.X[target] = new_state
            self.H[target] = np.vstack((new_state, self.H[target]))
            if len(self.H[target]) >= self.MAX_HISTORY_SIZE:
                self.H[target] = np.delete(self.H[target], (self.MAX_HISTORY_SIZE), axis=0)

        self.t += self.dt
        self.timestep += 1

    def create_update_matrices(self):
        def create_update_matrix(space_kernel, time_kernel):
            D = np.eye(self.num_v) * space_kernel(0)
            sk = np.vectorize(lambda r: space_kernel(r) if r != 0 else 0)
            U = np.zeros((MAX_HISTORY_SIZE, self.num_v, self.num_v))
            for i in range(len(MAX_HISTORY_SIZE)):
                U[i] += (D + sk(self.A)) * time_kernel(i)
            return sparse.COO.from_numpy(U)

        U = {}
        for target in self.X.keys():
            U[target] = {}
            for source in self.X.keys():
                space_kernel = self.space_kernel_funcs[target][source]
                time_kernel = self.time_kernel_funcs[target][source]
                U[target][source] = create_update_matrix(space_kernel, time_kernel)
        return U


    # Getters -----------------------------------------------------------------
    def get_timestep(self):
        return self.timestep

    def get_current_state(self, prop):
        return self.X[prop].toarray()

    # Setters -----------------------------------------------------------------
    def set_graph(self, graph):
        self.G = graph
        return self.G

    def set_space_kernel(self, target, source, func):
        self.space_kernel_funcs[target][source] = func
        return self.space_kernel_funcs[target][source]

    def set_time_kernel(self, target, source, func):
        self.time_kernel_funcs[target][source] = func
        return self.time_kernel_funcs[target][source]









