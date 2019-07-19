import numpy as np
np.set_printoptions(threshold=np.inf)
import graph_tool.all as gt
import scipy as sp
import random
import matplotlib.pyplot as plt
from mpl_toolkits.mplot3d import Axes3D
import tkinter as tk


MAX_SIZE_HISTORY = 100


class Rias:


    # Constructors ------------------------------------------------------------

    def __init__(self, graph, dt=1):
        self.g = graph
        self.history = []
        self.history.append(self.g.vp.value.get_array().copy())

        self.timestep = 0
        self.t = 0
        self.dt = dt

        self.adjacency_matrix = gt.adjacency(self.g, g.ep.weight)
        self.weight_dep_matrices = self.split_matrix_by_weight(self.adjacency_matrix)

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
        g.vertex_properties["value"] = g.new_vertex_property("double", vals=vals)
        return cls(g)

    @classmethod
    def init_lattice_2d_8n(cls, lattice, periodic=True):
        length = len(lattice)
        width = len(lattice[0])
        g = gt.Lattice([length, width], periodic=periodic)
        num_vertices = g.num_vertices()
        vals = [l for lst in lattice for l in lst]
        g.vertex_properties["value"] = g.new_vertex_property("double", vals=vals)
        for i in range(length - (0 if periodic else 1)):
            for j in range(width - (0 if periodic else 1)):
                vertex_current = i * length + j
                vertex_se = (vertex_current + length + 1) % num_vertices
                vertex_sw = (vertex_current + length - 1) % num_vertices
                g.add_edge_list([(vertex_current, vertex_se), (vertex_current, vertex_sw)])
        return cls(g)

    @classmethod
    def init_lattice_1d(cls, lattice, periodic=True):
        length = len(lattice)
        g = gt.Lattice([length], periodic=periodic)
        num_vertices = g.num_vertices()
        g.vertex_properties["value"] = g.new_vertex_property("double", vals=lattice)
        return cls(g)



    # Core functions -------------------------------------------------------

    def update_world(self):
        effective_values = self.kernel.dot(self.g.vs['value'])
        for i, e_f in enumerate(effective_values):
            v = self.g.vs[i]['value']
            self.g.vs[i]['value'] = self.combine_func(v, e_f)

        self.t += self.dt
        self.timestep += 1

    def split_matrix_by_weight(self, adjacency_matrix):
        matrices = {}
        f = lambda x, i: 1 if x == i else 0
        for i, row in enumerate(adjacency_matrix):
            for j, item in enumerate(row):
                if item != 0:
                    matrices[item] = matrices.get(item, sp.csr_matrix(adjacency_matrix.shape)
                    matrices[item][i][j] = 1
                else:
                    continue
        return matrices







    # Utility functions -------------------------------------------------------



    # Presets -----------------------------------------------------------------

    @staticmethod
    def kernel_func_heat(distance):
        if distance <= 1:
            return 1
        else:
            return 0




def zipf(N, k, s):
    return 1 / ((k ** s) * sum([1 / n ** s for n in range(1, N + 1)]))



def main():
    kernel_func = Rias.kernel_func_life
    initial_lattice_2d_8n = np.floor(np.random.rand(100, 100) * 10) % 2
    world = Rias.init_lattice_2d_8n(initial_lattice_2d_8n, kernel_func)
    color_dict = {0: (0,0,0), 1: (255,255,255)}
    layout = world.g.layout('grid')
    while True:
        print(world.timestep)
        plot(world.g, layout = layout, vertex_color = [color_dict[v] for v in world.g.vs['value']])
        world.update_world()
#    initial_lattice_1d = np.random.rand(1000)
#    world = Rias.init_lattice_1d(initial_lattice_1d, periodic=False)
#    layout = world.g.layout('circle')



if __name__ == '__main__':
    main()
