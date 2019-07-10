import numpy as np
import random
import matplotlib.pyplot as plt
from mpl_toolkits.mplot3d import Axes3D
import tkinter as tk


MAX_SIZE_HISTORY = 100


class World:
    timestep = 0
    t = 0
    dt = 1

    class Node:
        def __init__(self, value, neighbors=[]):
            self.history = []
            self.history.append(value)
            self.neighbors = neighbors

    # Constructors -----------------------------------------------------------

    def __init__(self, num_attributes, tagback_window, nodes=set()):
        self.num_attributes = num_attributes
        self.tagback_window = self.tagback_window # How far back to look from a neighbor by radius before a cycle is allowed
        self.nodes = nodes
        self.num_nodes = len(nodes)

    @classmethod
    def init_random(cls, num_attributes, tagback_window, min_nodes, max_nodes, min_attribute, max_attribute, min_connections, max_connections):
        num_nodes = random.randint(min_nodes, max_nodes)
        num_connections = random.randint(min_connections, max_connections)
        nodes = []
        for _ in range(num_nodes):
            nodes.append(cls.Node(random.uniform(min_attribute, max_attribute)))
        for _ in range(num_connections):
            cls.connect_directed(random.sample(nodes, 1), random.sample(nodes, 1))
        return cls(num_attributes, tagback_window, nodes)

    @classmethod
    def init_lattice2d(cls, matrix):
        nodes= []
        length = len(matrix)
        width = len(matrix[0])
        for i in range(length):
            for j in range(width):
                node_current = cls.Node(matrix[i][j])
                node_e = cls.Node(matrix[i][(j+1) % width])
                node_s = cls.Node(matrix[(i+1) % length][j])
                node_se = cls.Node(matrix[(i+1) % length][(j+1) % width])
                node_sw = cls.Node(matrix[(i+1) % length][(j-1) % width])
                cls.connect_undirected(node_current, node_e)
                cls.connect_undirected(node_current, node_s)
                cls.connect_undirected(node_current, node_se)
                cls.connect_undirected(node_current, node_sw)
                nodes.append(node_current)
        return cls(1, 1, nodes)

    def init_lattice1d(cls, matrix):


    # Core functions -------------------------------------------------------

    def update_world(self):
        """Appends updated node values to all nodes' histories"""
        global timestep, t, dt
        for node in self.nodes:
            node.history.append(self.calculate_new_node(node))
            if len(node.history) > MAX_SIZE_HISTORY:
                del node.history[0]
        t += dt
        timestep += 1

    def calculate_new_node(self, node, effective_radius, kernel_func, combine_func):
        """
        Returns the updated value of the node at t + dt.

        Parameters:
        node - target node to update
        effective_radius - max distance to reach from node
        kernel_func(neighbor, neighbor_radius) - calculates an intermediate value
        combine_func(values_by_radius) - calculates the updated node value
                                                            from the result of kernel_func()
        """
        nodes_by_radius = [{node}]                  # The index indicates the radius at which the node(s) reside
        values_by_radius = [[kernel_func(node, 0)]] # The index indicates the radius at which the intermediate value was calculated

        # Starting from node, this loop radiates out by radius using
        # self.tagback_window to build nodes_by_radius to build
        # values_by_radius using kernel_func()
        for r in range(effective_radius):
            nodes_in_radius, values_in_radius = set(), []
            for node in nodes_by_radius[-1]:
                for neighbor in node.neighbors:                                                                 #below clause may be unnecessary#
                    if self.tagback_window == 0 or (neighbor not in any(nodes_by_radius[-self.tagback_window:]) and neighbor not in nodes_in_radius):
                        nodes_in_radius.add(neighbor)
                        values_in_radius.append(kernel_func(neighbor, r+1))
            nodes_by_radius.append(nodes_in_radius)
            values_by_radius.append(values_in_radius)

        return combine_func(values_by_radius)


    # Utility functions -------------------------------------------------------

    @staticmethod
    def connect_undirected(n0, n1):
        n0.neighbors.append(n1)
        n1.neighbors.append(n0)

    @staticmethod
    def connect_directed(n0, n1):
        n0.neighbors.append(n1)


    # Presets -----------------------------------------------------------------

    def kernel_func_life(node, radius):
        return node.history[timestep]

    def combine_func_life(values_by_radius):
        alive = sum([v for values in values_by_radius for v in values[1:]])
        if values_by_radius[0][0]:
            if alive < 2 or alive > 3:
                return 0
            else:
                return 1
        else:
            if alive == 3:
                return 1
            else:
                return 0






def zipf(N, k, s):
    return 1 / ((k ** s) * sum([1 / n ** s for n in range(1, N + 1)]))



def main():
    world = None


if __name__ == '__main__':
    main()
