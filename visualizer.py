import quantum_graph as qg
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

        self.page1 = WaveBox2D()
        label1 = Gtk.Label('2D Wave Equation')
        self.page1.set_border_width(10)
        self.notebook.append_page(self.page1, label1)

        #self.page2 = WaveBox3D()
        #label2 = Gtk.Label('3D Wave Equation')
        #self.page2.set_border_width(10)
        #self.notebook.append_page(self.page2, label2)



class WaveBox2D(Gtk.VBox):
    def __init__(self):
        Gtk.VBox.__init__(self)

        # Controls ------------------------------------------------------------
        self.controls_box = Gtk.VBox(spacing=0)
        self.pack_start(self.controls_box, False, False, 0)
        # Pause/unpause
        self.paused = True
        self.button_pause = Gtk.Button.new_with_label("start")
        self.button_pause.connect("clicked", self.pause)
        self.controls_box.pack_start(self.button_pause, False, True, 0)
        # Alpha adjustment
        adjustment = Gtk.Adjustment(value=0.5, lower=0, upper=1, step_increment=.01)
        self.button_alpha = Gtk.SpinButton()
        self.button_alpha.configure(adjustment, .1, 2)
        self.controls_box.pack_start(self.button_alpha, False, False, 0)

        # Plot ----------------------------------------------------------------
        self.plot_box = Gtk.VBox(spacing=0)
        self.pack_end(self.plot_box, True, True, 0)


        initial_state = {'position':
                         np.concatenate([np.zeros(100) + 100,
                         [200 - i for i in range(200)], np.zeros(700)+500]),
                            'velocity':np.zeros(1000) -1 }


        self.qg = qg.QuantumGraph.init_lattice_1d(initial_state, [('velocity', 'position', 1, -1)],
                                dt = 1, alpha = 1/5, periodic=True)

        self.fig = Figure()
        self.ax= self.fig.add_subplot(111)
        self.ax = plt.axes(xlim=(0, self.qg.num_v), ylim=(-1000, 1000))
        self.line, = self.ax.plot([], [], lw=1)
        self.timestamp = self.ax.annotate('timestep = ' +
                                        str(self.qg.get_timestep()),
                                        xy=(0.15, 0.9),
                                        xycoords='figure fraction')


        fc = FigureCanvas(self.fig)
        self.plot_box.pack_start(fc, True, True, 0)
        nt = NavigationToolbar(fc, self)
        self.plot_box.pack_end(nt, False, False, 0)


        #m = plt.cm.ScalarMappable(cmap=plt.cm.jet)
        #m.set_array(self.qg.X['position'].a)
        #cbar = plt.colorbar(m)

        self.anim = animation.FuncAnimation(self.fig, self.animate, init_func=self.init_plot,
                                    frames=2000, interval=20, blit=False)




    def pause(self, button):
        self.paused = not self.paused
        if self.paused:
            self.button_pause.set_label('resume')
        else:
            self.button_pause.set_label('pause')


    def init_plot(self):
        self.line.set_data([], [])
        return self.line, self.timestamp

    def animate(self):
        if not self.paused:
            self.qg.update_graph()
            self.qg.set_alpha(self.button_alpha.get_value())
            self.timestamp.set_text('timestep = ' + str(self.qg.timestep))
        x = np.linspace(0, self.qg.num_v, self.qg.num_v)
        y = self.qg.X['position'].a
        self.line.set_data(x, y)
        return self.line, self.timestamp


class WaveBox3D(Gtk.VBox):
    def __init__(self):
        Gtk.VBox.__init__(self)

        # Controls ------------------------------------------------------------
        self.controls_box = Gtk.VBox(spacing=0)
        self.pack_start(self.controls_box, False, False, 0)
        # Pause/unpause
        self.paused = True
        self.button_pause = Gtk.Button.new_with_label("start")
        self.button_pause.connect("clicked", self.pause)
        self.controls_box.pack_start(self.button_pause, False, True, 0)
        # Alpha adjustment
        adjustment = Gtk.Adjustment(value=0.5, lower=0, upper=1, step_increment=.01)
        self.button_alpha = Gtk.SpinButton()
        self.button_alpha.configure(adjustment, .1, 2)
        self.controls_box.pack_start(self.button_alpha, False, False, 0)

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
        self.qg = qg.QuantumGraph.init_lattice_2d_4n(initial_states_2d,
                                                     [('velocity', 'position', 1, -1)],
                                dt = 1, alpha = 1/5, periodic=True)
        self.fig = Figure()
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
            print('a ', i)
            self.qg.update_graph()
            self.plot3d.remove()
            self.plot3d = self.ax.plot_surface(self.x2, self.y2,
                                               np.reshape(self.qg.get_current_state('position'), (-1, len(self.x2[0]))),
                                               rstride=5, cstride=5,
                                               color='k', linewidth=0.5)


    def animate3d(self, i):
        if not self.paused:
            self.qg.update_graph()
            self.plot3d.remove()
            self.plot3d = self.ax.plot_trisurf(self.x2.flatten(),self.y2.flatten(),
                                               self.qg.get_current_state('position'),
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

