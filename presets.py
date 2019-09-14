import graph_tool.all as gt
import random
import numpy as np

class KernelFuncs():
    def laplacian(r):
        if r == 0:
            return 1
        elif r == 1:
            return -1/2
        else:
            return 0

    def identity(r):
        if r == 0:
            return 1
        else:
            return 0

    def zero(r):
        return 0

class Graphs():
    def random(num_attributes, min_vertices, max_vertices, min_attribute, max_attribute, min_edges, max_edges):
        g = gt.Graph()

        num_vertices = random.randint(min_vertices, max_vertices)
        for _ in range(num_vertices):
            g.add_vertices(random.uniform(min_attribute, max_attribute))

        edges = []
        num_edges = random.randint(min_edges, max_edges)
        for _ in range(num_edges):
            edges.append((random.randint(0, num_vertices), random.randint(0, num_vertices)))
        g.add_edges(edges)

        return g

    def lattice_2d_4n(vp_dict, update_rules, dt=1, alpha=1, periodic=True):
        length = len(vp_dict[next(iter(vp_dict))])
        width = len(vp_dict[next(iter(vp_dict))][0])
        g = gt.lattice([length, width], periodic=periodic)
        g.ep["weight"] = g.new_ep("double", val=1)
        for prop_name, prop in vp_dict.items():
            vals = [l for lst in prop for l in lst]
            g.vp[prop_name] = g.new_vp("double", vals=vals)
        return g

    def lattice_2d_8n(vp_dict, periodic=True):
        length = len(vp_dict[next(iter(vp_dict))])
        width = len(vp_dict[next(iter(vp_dict))][0])
        g = gt.lattice([length, width], periodic=periodic)
        num_vertices = g.num_vertices()
        for i in range(length - (0 if periodic else 1)):
            for j in range(width - (0 if periodic else 1)):
                vertex_current = i * length + j
                vertex_se = (vertex_current + length + 1) % num_vertices
                vertex_sw = (vertex_current + length - 1) % num_vertices
                g.add_edge_list([(vertex_current, vertex_se), (vertex_current, vertex_sw)])
        return g

    def lattice_1d(vp_dict, dt=1, alpha=1, periodic=True):
        length = len(vp_dict[next(iter(vp_dict))])
        g = gt.lattice([length], periodic=periodic)
        #g.set_directed(False)
        for prop, vals in vp_dict.items():
            g.vp[prop] = g.new_vp("double", vals=vals)
        g.ep["weight"] = g.new_ep("double", val=1)
        #g.ep["weight"] = g.new_ep("double", vals=[1 if i < 400 else 2 for i in range(1000)])
        return g

    def wave1d():
        length = 1000
        positions = np.from_function(lambda x: 100*np.sin(x) + 500, (length))
        velocities = np.from_function(lambda x: 100*np.cos(x) + 500, (length))

        g = gt.lattice([length], periodic=True)
        g.vp['position'] = g.new_vp('double', vals=positions)
        g.vp['velocity'] = g.new_vp('double', vals=velocities)


    def heat1d():
        return
