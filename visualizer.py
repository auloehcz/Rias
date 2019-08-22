import dynamical_graph as dg
import numpy as np
np.set_printoptions(threshold=np.inf)

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
        self.dg = None

        # Controls ------------------------------------------------------------
        self.controls = {}
        self.grid_controls = Gtk.Grid()
        self.pack_start(self.grid_controls, False, False, 0)
        # Pause/unpause
        self.paused = True
        self.controls['button_pause'] = Gtk.Button.new_with_label("start")
        self.controls['button_pause'].connect("clicked", self.pause)
        self.grid_controls.attach(self.controls['button_pause'], 1, 1, 1, 1)
        # Alpha adjustment
        alpha = Gtk.Adjustment(value=0.5, lower=0, upper=1, step_increment=.01)
        self.controls['button_alpha'] = Gtk.SpinButton()
        self.controls['button_alpha'].configure(alpha, .1, 2)
        self.grid_controls.attach(self.controls['button_alpha'], 1, 2, 2, 2)

        # Properties setter
        #label_properties = Gtk.Label()
        #label_properties.set_label('properties')
        #self.grid_controls.attach(label_properties, 10, 1, 1, 1)

        self.controls['entry_num_props'] = Gtk.Entry()
        self.controls['entry_num_props'].set_text("2")
        self.grid_controls.attach(self.controls['entry_num_props'], 5, 1, 1, 1)

        self.controls['button_set_props'] = Gtk.Button.new_with_label("set")
        self.controls['button_set_props'].connect("clicked", self.set_properties)
        self.grid_controls.attach(self.controls['button_set_props'], 6, 1, 1, 1)


        # Reset

        # Presets
        liststore_presets = Gtk.ListStore(int, str)
        liststore_presets.append([1, '1d Wave'])
        liststore_presets.append([2, '1d Heat'])
        self.controls['combobox_presets'] = Gtk.ComboBox.new_with_model_and_entry(liststore_presets)
        self.controls['combobox_presets'].connect("changed", self.on_name_combo_changed)
        self.controls['combobox_presets'].set_entry_text_column(1)
        self.grid_controls.attach(self.controls['combobox_presets'], 2, 1, 2, 1)

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

        self.anim = animation.FuncAnimation(self.fig, self.animate, init_func=self.init_line,
                                    frames=2000, interval=20, blit=False)


    def set_properties(self, button):
        num_props = int(self.controls['entry_num_props'].get_text())
        grid_kernels = Gtk.Grid()
        for i in range(num_props):
            entry_prop = 'self.entry_prop' + str(i)
            self.controls[entry_prop] = Gtk.Entry()
            grid_kernels.attach(self.controls[entry_prop], 1, i+1, 1, 1)
            for j in range(num_props):
                entry_kernel = "self.entry_kernel" + str(i) + str(j)
                self.controls[entry_kernel] = Gtk.Entry()
                grid_kernels.attach(self.controls[entry_kernel], j+2, i+1, 1, 1)
        self.grid_controls.attach(grid_kernels, 7, 1, num_props, num_props+1)
        self.show_all()


    def on_name_combo_changed(self, preset):
        return

    def create_plot(self):
        return


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

