import dynamical_graph as dg
import presets
import graph_tool.all as gt
import numpy as np
import random
import collections
#np.set_printoptions(threshold=np.inf)

from gi.repository import Gtk, Gdk, GdkPixbuf, GObject, GLib
import matplotlib
from matplotlib.figure import Figure
matplotlib.use("GTK3Cairo")
from matplotlib.backends.backend_gtk3 import (
    NavigationToolbar2GTK3 as NavigationToolbar)
from matplotlib.backends.backend_gtk3cairo import (
    FigureCanvasGTK3Cairo as FigureCanvas)
from matplotlib import pyplot as plt
plt.style.use("ggplot")
from mpl_toolkits.mplot3d import axes3d
from matplotlib import animation


class MainWindow(Gtk.Window):
    def __init__(self):
        Gtk.Window.__init__(self, title="RIAS")
        self.connect("destroy", Gtk.main_quit)
        self.set_default_size(1280, 720)

        self.notebook = Gtk.Notebook()
        self.add(self.notebook)

        self.page1 = Box2D()
        label1 = Gtk.Label()
        label1.set_label('2D plot')
        self.page1.set_border_width(10)
        self.notebook.append_page(self.page1, label1)

        #self.page2 = Box3D()
        #label2 = Gtk.Label('3D plot')
        #self.page2.set_border_width(10)
        #self.notebook.append_page(self.page2, label2)


class Box2D(Gtk.VBox):
    def __init__(self):
        Gtk.VBox.__init__(self)
        # Controls ------------------------------------------------------------
        self.controls = {}
        self.grid_controls = Gtk.Grid()
        self.pack_start(self.grid_controls, False, False, 0)

        # Properties setter
        self.controls['entry_num_props'] = Gtk.Entry()
        self.controls['entry_num_props'].set_text("2")
        self.grid_controls.attach(self.controls['entry_num_props'], 1, 1, 1, 1)

        self.controls['button_set_num_props'] = Gtk.Button.new_with_label("Set Number of Properties")
        self.controls['button_set_num_props'].connect("clicked", self.set_num_props)
        self.grid_controls.attach(self.controls['button_set_num_props'], 2, 1, 1, 1)

        # Graph Presets
        self.controls['combobox_graph_presets'] = Gtk.ComboBoxText.new_with_entry()
        self.controls['combobox_graph_presets'].append('lattice', 'lattice')
        self.controls['combobox_graph_presets'].connect("changed", self.on_preset_changed)
        self.controls['combobox_graph_presets'].set_entry_text_column(1)
        self.grid_controls.attach(self.controls['combobox_graph_presets'], 1, 3, 1, 1)


        # Kernel setter
        self.controls['button_set_kernels'] = Gtk.Button.new_with_label("Set Kernels")
        self.controls['button_set_kernels'].connect("clicked", self.create_window_kernels)
        self.grid_controls.attach(self.controls['button_set_kernels'], 1, 5, 1, 1)




        # Initialize graph
        self.controls["button_initialize"] = Gtk.Button.new_with_label("Initialize")
        self.controls['button_initialize'].connect("clicked", self.initialize_graph)
        self.grid_controls.attach(self.controls['button_initialize'], 7, 1, 1, 1)

        # Pause/unpause
        self.paused = True
        self.controls['button_pause'] = Gtk.Button.new_with_label("Start")
        self.controls['button_pause'].connect("clicked", self.pause)
        self.grid_controls.attach(self.controls['button_pause'], 1, 1, 1, 1)

        # Alpha adjustment
        #alpha = Gtk.Adjustment(value=0.5, lower=0, upper=1, step_increment=.01)
        #self.controls['button_alpha'] = Gtk.SpinButton()
        #self.controls['button_alpha'].configure(alpha, .1, 2)
        self.show_all()
        #self.grid_controls.attach(self.controls['button_alpha'], 1, 2, 2, 2)


        # Plot ----------------------------------------------------------------
        self.plot_box = Gtk.VBox(spacing=0)
        self.pack_end(self.plot_box, True, True, 0)
        self.fig, self.ax = plt.subplots(nrows=2, ncols=1)
        self.ax[0] = plt.axes(xlim=(0, 100), ylim=(-1000, 1000))
        self.ax[1] = plt.axes(xlim=(0, 100), ylim=(-1000, 1000))
        self.line1, = self.ax[0].plot([], [], lw=1)
        self.line2, = self.ax[1].plot([], [], lw=1)
        self.timestamp = self.ax[1].annotate('timestep = 0',
                                             xy=(0.15, 0.9),
                                             xycoords='figure fraction')


        fc = FigureCanvas(self.fig)
        self.plot_box.pack_start(fc, True, True, 0)
        nt = NavigationToolbar(fc, self)
        self.plot_box.pack_end(nt, False, False, 0)


        #m = plt.cm.ScalarMappable(cmap=plt.cm.jet)
        #m.set_array(self.dg.X['position'].a)
        #cbar = plt.colorbar(m)

        self.anim = animation.FuncAnimation(self.fig, self.animate,
                                            init_func=self.init_line,
                                            frames=2000, interval=20, blit=False)




    def set_num_props(self, button):
        self.num_props = int(self.controls['entry_num_props'].get_text())
        box_props = Gtk.HBox()
        for i in range(self.num_props):
            entry_prop = 'entry_prop' + str(i)
            self.controls[entry_prop] = Gtk.Entry()
            box_props.pack_end(self.controls[entry_prop], True, True, 0)
        self.controls['button_set_prop_names'] = Gtk.Button.new_with_label("Set Property Names")
        self.controls['button_set_prop_names'].connect("clicked", self.set_prop_names)
        self.grid_controls.remove_row(2)
        self.grid_controls.insert_row(2)
        self.grid_controls.attach(box_props, 1, 2, 1, 1)
        self.grid_controls.attach(self.controls['button_set_prop_names'], 2, 2, 1, 1)
        self.show_all()

    def set_prop_names(self, button):
        self.prop_names = []
        for i in range(self.num_props):
            s = 'entry_prop' + str(i)
            self.prop_names.append(self.controls[s].get_text())



    def initialize_graph(self, button):
        graph_preset = self.controls['combobox_graph_presets'].get_entry_text_column()
        g = graph_preset
        self.dg = dg.DynamicalGraph(self.g, self.time_kernels, self.space_kernels)


    def create_window_kernels(self, button):
        preset_kernels = [f for f in dir(presets.KernelFuncs) if "__" not in f]
        label_space = Gtk.Label(label='Space Kernels')
        grid_space_kernels = Gtk.Grid()
        hbox_space_labels = Gtk.HBox()
        vbox_space_labels = Gtk.VBox()
        label_time = Gtk.Label(label='Time Kernels')
        grid_time_kernels = Gtk.Grid()
        hbox_time_labels = Gtk.HBox()
        vbox_time_labels = Gtk.VBox()
        for i in range(self.num_props):
            label = self.prop_names[i]
            hbox_space_labels.pack_end(Gtk.Label(label=label), True, True, 0)
            vbox_space_labels.pack_end(Gtk.Label(label=label), True, True, 0)
            hbox_time_labels.pack_end(Gtk.Label(label=label), True, True, 0)
            vbox_time_labels.pack_end(Gtk.Label(label=label), True, True, 0)
            for j in range(self.num_props):
                combobox_space = "combobox_space_kernel" + str(i) + str(j)
                combobox_time = "combobox_time_kernel" + str(i) + str(j)
                self.controls[combobox_space] = Gtk.ComboBoxText()
                self.controls[combobox_time] = Gtk.ComboBoxText()
                for kernel in preset_kernels:
                    self.controls[combobox_space].append(kernel, kernel)
                    self.controls[combobox_time].append(kernel, kernel)
                grid_space_kernels.attach(self.controls[combobox_space], j+2, i+1, 1, 1)
                grid_time_kernels.attach(self.controls[combobox_time], j+2, i+1, 1, 1)
        button_set_kernels = Gtk.Button.new_with_label("Set Kernels")
        button_set_kernels.connect("clicked", self.set_kernels)

        grid_kernels = Gtk.Grid()
        grid_kernels.attach(label_space, 2, 1, 1, 1)
        grid_kernels.attach(hbox_space_labels, 2, 2, 1, 1)
        grid_kernels.attach(vbox_space_labels, 1, 3, 1, 1)
        grid_kernels.attach(grid_space_kernels, 2, 3, 1, 1)
        grid_kernels.attach(label_time, 2, 4, 1, 1)
        grid_kernels.attach(hbox_time_labels, 2, 5, 1, 1)
        grid_kernels.attach(vbox_time_labels, 1, 6, 1, 1)
        grid_kernels.attach(grid_time_kernels, 2, 6, 1, 1)
        grid_kernels.attach(button_set_kernels, 2, 7, 1, 1)

        self.window_kernels = Gtk.Window()
        self.window_kernels.set_title("Kernel Controls")
        self.window_kernels.connect("destroy", lambda *w: Gtk.main_quit)
        self.window_kernels.set_modal(True)
        self.window_kernels.add(grid_kernels)
        self.window_kernels.show_all()



    def set_kernels(self, button):
        self.space_kernels = {}
        self.time_kernels = {}
        for i in range(self.num_props):
            self.space_kernels[self.prop_names[i]] = {}
            self.time_kernels[self.prop_names[i]] = {}
            for j in range(self.num_props):
                entry_name = "entry_space_kernel" + str(i) + str(j)
                self.space_kernels[self.prop_names[i]][self.prop_names[j]] = \
                    self.controls[entry_name].get_text()
                entry_name = "entry_time_kernel" + str(i) + str(j)
                self.space_kernels[self.prop_names[i]][self.prop_names[j]] = \
                    self.controls[entry_name].get_text()

        self.window_kernels.gtk_window_close()

    def on_preset_changed(self, preset):
        preset = self.controls['combobox_graph_presets'].get_active_text()
        if preset == 'lattice':
            self.create_lattice_controls()
        else:
            print('Not implemented yet!')

        return

    def create_lattice_controls(self):
        self.grid_lattice_controls = Gtk.Grid()
        for i in range(self.num_props):
            s0 = 'entry_initial_state' + str(i)
            s1 = 'entry_boundary_condition' + str(i)
            self.controls[s0] = Gtk.Entry()
            self.controls[s1] = Gtk.Entry()
            self.grid_lattice_controls.attach(self.controls[s0], i+1, 1, 1, 1)
            self.grid_lattice_controls.attach(self.controls[s1], i+1, 2, 1, 1)
        self.controls['entry_shape'] = Gtk.Entry()
        self.controls['entry_max_radius'] = Gtk.Entry()
        self.controls['checkbutton_periodic'] = Gtk.CheckButton.new_with_label("Periodic")
        self.controls["button_set_graph"] = Gtk.Button.new_with_label("Set Graph")
        self.controls['button_set_graph'].connect("clicked", self.set_graph_lattice)
        self.grid_lattice_controls.attach(self.controls['entry_shape'], 3, 1, 1, 1)
        self.grid_lattice_controls.attach(self.controls['entry_max_radius'], 3, 1, 1, 1)
        self.grid_lattice_controls.attach(self.controls['checkbutton_periodic'], 4, 1, 1, 1)
        self.grid_lattice_controls.attach(self.controls['button_set_graph'], 10, 10, 1, 1)

        self.grid_controls.attach(self.grid_lattice_controls, 1, 4, 1, 1)
        self.show_all()

    def set_graph_lattice(self, button):
        periodic = self.controls['checkbutton_periodic'].get_active()
        shape = eval(self.controls["entry_shape"].get_text())
        max_radius = int(self.controls['entry_max_radius'].get_text())
        self.g = gt.lattice(shape, periodic=periodic)
        for i in range(self.num_props):
            f = self.controls['entry_initial_state' + str(i)]
            self.g.vp[self.prop_names[i]] = list(self.flatten(np.from_function(f, shape)))
            #for v in

    def create_plot(self):
        return


    def flatten(self, l):
        for el in l:
            if isinstance(el, collections.Iterable) and not isinstance(el, (str, bytes)):
                yield from self.flatten(el)
            else:
                yield el

    def pause(self, button):
        self.paused = not self.paused
        if self.paused:
            self.button_pause.set_label('resume')
        else:
            self.button_pause.set_label('pause')


    def init_line(self):
        self.line1.set_data([], [])
        self.line2.set_data([], [])
        return self.line1, self.line2, self.timestamp

    def animate(self, i):
        if not self.paused:
            self.dg.update_graph()
            self.dg.set_alpha(self.button_alpha.get_value())
            self.timestamp.set_text('timestep = ' + str(self.dg.timestep))
        x = np.linspace(0, self.dg.num_v, self.dg.num_v)
        y1 = self.dg.X['position'].a
        self.line1.set_data(x, y1)
        y2 = self.dg.X['velocity'].a
        self.line2.set_data(x, y2)
        return self.line1, self.line2, self.timestamp



class Box3D(Gtk.VBox):
    def __init__(self):
        Gtk.VBox.__init__(self)

        # Controls ------------------------------------------------------------
        self.grid_controls = Gtk.VBox(spacing=0)
        self.pack_start(self.grid_controls, False, False, 0)
        # Pause/unpause
        self.paused = True
        self.button_pause = Gtk.Button.new_with_label("start")
        self.button_pause.connect("clicked", self.pause)
        self.grid_controls.pack_start(self.button_pause, False, True, 0)
        # Alpha adjustment
        adjustment = Gtk.Adjustment(value=0.5, lower=0, upper=1, step_increment=.01)
        self.button_alpha = Gtk.SpinButton()
        self.button_alpha.configure(adjustment, .1, 2)
        self.grid_controls.pack_start(self.button_alpha, False, False, 0)

        # Plot ----------------------------------------------------------------
        self.plot_box = Gtk.VBox(spacing=0)
        self.pack_end(self.plot_box, True, True, 0)


        self.x = np.arange(0,50,1)
        self.y = np.arange(0,50,1)
        self.x2 = np.append(0,self.x.flatten())
        self.y2 = np.append(0,self.y.flatten())
        self.x2,self.y2 = np.meshgrid(self.x2,self.y2)
        self.z = 20 * (np.cos(self.x2 / 5) * np.cos(self.y2 / 5) + 1)

        initial_states_2d = {'position': self.z,
                             'velocity': np.zeros((50, 50))}
        self.dg = dg.DynamicalGraph.init_lattice_2d_4n(initial_states_2d,
                                                     [('velocity', 'position', 1, -1)],
                                dt = 1, alpha = 1/5, periodic=True)
        self.fig = plt.figure()
        self.ax = self.fig.add_subplot(111, projection='3d')
        self.ax.set_xlim3d([0, 50])
        self.ax.set_xlabel('X')
        self.ax.set_ylim3d([0, 50])
        self.ax.set_ylabel('Y')
        self.ax.set_zlim3d([0, 100])
        self.ax.set_zlabel('Z')


        m = plt.cm.ScalarMappable(cmap=plt.cm.jet)
        m.set_array(self.z[0])
        cbar = plt.colorbar(m)

        #self.plot3d = self.ax.plot_trisurf(self.x2.flatten(),self.y2.flatten(),self.z.flatten(),
        #                                   cmap=plt.cm.jet,
        #                                   linewidth=0.1, antialiased=True)

        self.plot3d = self.ax.plot_surface(self.x2, self.y2, self.z, rstride=5, cstride=5, color='k', linewidth=0.5)

        fc = FigureCanvas(self.fig)
        self.plot_box.pack_start(fc, True, True, 0)
        nt = NavigationToolbar(fc, self)
        self.plot_box.pack_end(nt, False, False, 0)

        self.ani = animation.FuncAnimation(self.fig, self.animate_wireframe,
                                           interval=10, blit=False)

    def animate_wireframe(self, i):
        if not self.paused:
            self.dg.update_graph()
            self.plot3d.remove()
            self.plot3d = self.ax.plot_surface(self.x2, self.y2,
                                               np.reshape(self.dg.get_current_state('position'), (-1, len(self.x2[0]))),
                                               rstride=5, cstride=5,
                                               color='k', linewidth=0.5)

    def animate3d(self, i):
        if not self.paused:
            self.dg.update_graph()
            self.plot3d.remove()
            self.plot3d = self.ax.plot_trisurf(self.x2.flatten(),self.y2.flatten(),
                                               self.dg.get_current_state('position'),
                                               cmap=plt.cm.jet,
                                               linewidth=.1, antialiased=True)

    def pause(self, button):
        self.paused = not self.paused
        if self.paused:
            self.button_pause.set_label('resume')
        else:
            self.button_pause.set_label('pause')

def main():
    mw = MainWindow()
    mw.show_all()
    Gtk.main()



if __name__ == '__main__':
    main()

