import numpy as np
np.set_printoptions(threshold=np.inf)
import random
from igraph import *
import matplotlib.pyplot as plt
from mpl_toolkits.mplot3d import Axes3D
import tkinter as tk


MAX_SIZE_HISTORY = 100


class World:


    # Constructors ------------------------------------------------------------

    def __init__(self, graph=Graph, dt=1):
        self.timestep = 0
        self.t = 0
        self.dt = dt
        self.g = graph

    @classmethod
    def init_random(cls, num_attributes, min_vertices, max_vertices, min_attribute, max_attribute, min_edges, max_edges):
        g = Graph()

        num_vertices = random.randint(min_vertices, max_vertices)
        for _ in range(num_vertices):
            g.add_vertices(random.uniform(min_attribute, max_attribute))

        edges = []
        num_edges = random.randint(min_edges, max_edges)
        for _ in range(num_edges):
            edges.append((random.randint(min_edges, max_edges), random.randint(min_edges, max_edges)))
        g.add_edges(edges)

        return cls(g)

    @classmethod
    def init_lattice_2d_4n(cls, lattice, wraparound=True):
        length = len(lattice)
        width = len(lattice[0])
        g = Graph().Lattice([length, width], circular=wraparound)
        num_vertices = len(g.vs)
        g.vs['history'] = [[item] for sublist in lattice for item in sublist]
        return cls(g)

    @classmethod
    def init_lattice_2d_8n(cls, lattice, wraparound=True):
        length = len(lattice)
        width = len(lattice[0])
        g = Graph().Lattice([length, width], circular=wraparound)
        num_vertices = len(g.vs)
        g.vs['history'] = cls.flatten(lattice)
        for i in range(length - (0 if wraparound else 1)):
            for j in range(width - (0 if wraparound else 1)):
                vertex_current = i * length + j
                vertex_se = (vertex_current + length + 1) % num_vertices
                vertex_sw = (vertex_current + length - 1) % num_vertices
                g.add_edges([(vertex_current, vertex_se), (vertex_current, vertex_sw)])
        return cls(g, 1)

    @classmethod
    def init_lattice_1d(cls, lattice, wraparound=True):
        length = len(lattice)
        g = Graph().Lattice([length], circular=wraparound)
        num_vertices = len(g.vs)
        g.vs['history'] = [[item] for item in lattice]
        return cls(g)



    # Core functions -------------------------------------------------------

    def update_world(self, max_radius, combine_func):
        """Updates all vertices synchronously and advances clock.

        Parameters:
        vertex - target vertex to update
        max_radius - max distance to reach from vertex
        combine_func(values_by_radius) - calculates the updated vertex value
        """
        for v in self.g.vs:
            new_value = self.calc_updated_vertex(v, max_radius, combine_func)
            v['history'].append(new_value)
            if len(v['history']) > MAX_SIZE_HISTORY:
                del v['history'][0]
        self.t += self.dt
        self.timestep += 1

    def calc_updated_vertex(self, v, max_radius, combine_func):
        """Returns updated value of vertex at t + dt."""
        vertices_by_radius = self.collect_vertices_by_radius(v, max_radius)
        new_value = combine_func(vertices_by_radius)
        return new_value

    def collect_vertices_by_radius(self, v, max_radius):
        """Returns a list of all vertices within max_radius according to shortest path."""
        shortest_paths = [p for p in self.g.get_shortest_paths(v) if len(p) - 1 <= max_radius]
        vertices_by_radius = [[] for i in range(max_radius + 1)]
        for path in shortest_paths:
            vertices_by_radius[len(path) - 1].append(self.g.vs[path[-1]])
        return vertices_by_radius



    # Utility functions -------------------------------------------------------

    @staticmethod
    def connect_undirected(n0, n1):
        n0.neighbors.append(n1)
        n1.neighbors.append(n0)

    @staticmethod
    def connect_directed(n0, n1):
        n0.neighbors.append(n1)


    # Presets -----------------------------------------------------------------

    def combine_func_life(self, vertices_by_radius):
        num_alive = sum([v['history'][min(self.timestep, MAX_SIZE_HISTORY)] for v in vertices_by_radius[1]])
        if vertices_by_radius[0][0]['history'][self.timestep]:
            if num_alive < 2 or num_alive > 3:
                return 0
            else:
                return 1
        else:
            if num_alive == 3:
                return 1
            else:
                return 0

    def combine_func_heat(self, vertices_by_radius):
        target = vertices_by_radius[0][0]['history'][self.timestep]
        change = ((sum([v['history'][min(self.timestep, MAX_SIZE_HISTORY)] for v in vertices_by_radius[1]]) / 2) - target) / 10
        return target + change

    # ???? --------------------------------------------------------------------

    def graph_to_arrays(g):
        shortest_paths = g.shortest_paths()
        [map(vertices_by_radius)]
    def combine_func(vertices, shortest_paths):
        for i, vertex in enumerate(vertices):
            update_func(vertices[i], shortest_paths[i])
            f(vertices[i])


        [vertex['history'][]]

    def get_value_t_steps_in_past(vertex, t):
        return vertex['history']





# Visualization -----------------------------------------------------------


def hex_to_RGB(hex):
  ''' "#FFFFFF" -> [255,255,255] '''
  # Pass 16 to the integer function for change of base
  return [int(hex[i:i+2], 16) for i in range(1,6,2)]


def RGB_to_hex(RGB):
  ''' [255,255,255] -> "#FFFFFF" '''
  # Components need to be integers for hex to make sense
  RGB = [int(x) for x in RGB]
  return "#"+"".join(["0{0:x}".format(v) if v < 16 else
            "{0:x}".format(v) for v in RGB])

# Value cache
fact_cache = {}
def fact(n):
    ''' Memoized factorial function '''
    try:
        return fact_cache[n]
    except(KeyError):
        if n == 1 or n == 0:
            result = 1
        else:
            result = n*fact(n-1)
            fact_cache[n] = result
        return result


def bernstein(t,n,i):
    ''' Bernstein coefficient '''
    binom = fact(n)/float(fact(i)*fact(n - i))
    return binom*((1-t)**(n-i))*(t**i)


def bezier_gradient(colors, n_out=100):
    ''' Returns a "bezier gradient" dictionary
        using a given list of colors as control
        points. Dictionary also contains control
        colors/points. '''
    # RGB vectors for each color, use as control points
    RGB_list = colors
    n = len(RGB_list) - 1

    def bezier_interp(t):
        ''' Define an interpolation function
            for this specific curve'''
        # List of all summands
        summands = [
        list(map(lambda x: int(bernstein(t,n,i)*x), c))
        for i, c in enumerate(RGB_list)
        ]
        # Output color
        out = [0,0,0]
        # Add components of each summand together
        for vector in summands:
            for c in range(3):
                out[c] += vector[c]

        return out

    gradient = [
        bezier_interp(float(t)/(n_out-1))
        for t in range(n_out)
    ]
    # Return all points requested for gradient
    return {
        "gradient": color_dict(gradient),
        "control": color_dict(RGB_list)
    }

def color_dict(gradient):
  ''' Takes in a list of RGB sub-lists and returns dictionary of
    colors in RGB and hex form for use in a graphing function
    defined later on '''
  return {"hex":[RGB_to_hex(RGB) for RGB in gradient],
      "r":[RGB[0] for RGB in gradient],
      "g":[RGB[1] for RGB in gradient],
      "b":[RGB[2] for RGB in gradient]}





def zipf(N, k, s):
    return 1 / ((k ** s) * sum([1 / n ** s for n in range(1, N + 1)]))



def main():
#    initial_lattice_2d_8n = np.floor(np.random.rand(15,15) * 10) % 2
#    world = World.init_lattice_2d_8n(initial_lattice_2d_8n)
#    color_dict = {0: (0,0,0), 1: (255,255,255)}
#    layout = world.g.layout('grid')
#    while True:
#        print(world.timestep)
#        plot(world.g, layout = layout, vertex_color = [color_dict[hist[min(world.timestep, MAX_SIZE_HISTORY)]] for hist in world.g.vs["history"]])
#        world.update_world(1, world.combine_func_life)
    initial_lattice_1d = np.random.rand(1000)
    world = World.init_lattice_1d(initial_lattice_1d, wraparound=False)
    layout = world.g.layout('circle')
    colormap = bezier_gradient([[0,0,50], [100, 100, 0], [200, 0 , 150]], 100)['gradient']
    print(colormap)
    while True:
        x = min(world.timestep, MAX_SIZE_HISTORY)
        plot(world.g, layout = layout, vertex_color = [(colormap['r'][np.floor(hist[x] * 100).astype(int)] / 255,
                                                        colormap['g'][np.floor(hist[x] * 100).astype(int)] / 255,
                                                        colormap['b'][np.floor(hist[x] * 100).astype(int)] / 255)
                                                       for hist in world.g.vs["history"]])
        world.update_world(1, world.combine_func_heat)


if __name__ == '__main__':
    main()
