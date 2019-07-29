import numpy as np
import graph_tool.all as gt
import sparse as sp
import random

class QuantumGraph:

    # Constructors ------------------------------------------------------------

    def __init__(self, graph, update_rules, dt=1, alpha=1):
        self.G = graph
        self.num_v = self.G.num_vertices()
        self.out_degrees = self.G.get_out_degrees(np.arange(self.num_v))
        self.update_rules = update_rules

        self.timestep = 0
        self.t = 0
        self.dt = dt # only use numbers 1 / k where k is a natural number
        self.time_dilation = 1 / self.dt
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
    def init_lattice_2d_4n(cls, vp_dict, update_rules, dt=1, alpha=1, periodic=True):
        length = len(vp_dict[next(iter(vp_dict))])
        width = len(vp_dict[next(iter(vp_dict))][0])
        g = gt.lattice([length, width], periodic=periodic)
        g.ep["weight"] = g.new_ep("double", val=1)
        for prop_name, prop in vp_dict.items():
            vals = [l for lst in prop for l in lst]
            g.vp[prop_name] = g.new_vp("double", vals=vals)
        return cls(g, update_rules, dt, alpha)

    @classmethod
    def init_lattice_2d_8n(cls, lattice, periodic=True):
        length = len(lattice)
        width = len(lattice[0])
        g = gt.lattice([length, width], periodic=periodic)
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
    def init_lattice_1d(cls, vp_dict, update_rules, dt=1, alpha=1, periodic=True):
        length = len(vp_dict[next(iter(vp_dict))])
        g = gt.lattice([length], periodic=periodic)
        g.set_directed(False)
        for prop, vals in vp_dict.items():
            g.vp[prop] = g.new_vp("double", vals=vals)
        g.ep["weight"] = g.new_ep("double", val=1)
        #g.ep["weight"] = g.new_ep("double", vals=[1 if i < 400 else 2 for i in range(1000)])
        if not periodic:
            g.self_loops = True
            g.add_edge_list([(0, 0), (length-1, length-1)])
        return cls(g, update_rules, dt, alpha)



    # Core functions -------------------------------------------------------

    def update_graph(self):
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

                #self.X[first_property].a -= constant * deltas * self.alpha / 20

            #for i in range(n_antiderivatives+1):
            self.H[first_property] = np.vstack((self.H[first_property],
                                                self.X[first_property].a))
            self.H[second_property] = np.vstack((self.H[second_property],
                                                self.X[second_property].a))

            if len(self.H[first_property]) > self.max_size_history:
                self.H[first_property] = np.delete(self.H[first_property], (0), axis=0)
            if len(self.H[second_property]) > self.max_size_history:
                self.H[second_property]= np.delete(self.H[second_property], (0), axis=0)



        self.t += self.dt
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
            # Fix this
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

    def set_alpha(self, value):
        self.alpha = value
        return self.alpha

    def get_timestep(self):
        return self.timestep

    def get_current_state(self, prop):
        return self.X[prop].a
