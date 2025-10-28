from qtpy import QtWidgets

from pymodaq_gui import utils as gutils
from pymodaq_utils.config import Config
from pymodaq_utils.logger import set_logger, get_module_name

from pymodaq_gui.utils.dock import Dock, DockArea
from pymodaq_gui.plotting.data_viewers.viewer0D import Viewer0D
from pymodaq_gui.plotting.data_viewers.viewer2D import Viewer2D
from pymodaq.control_modules.daq_viewer import DAQ_Viewer
from pymodaq.control_modules.daq_move import DAQ_Move, DAQ_Move_Hardware, DAQ_Move_UI, DAQ_Move_Actuators, DAQ_Move_base

# todo: replace here *pymodaq_plugins_template* by your plugin package name
from pymodaq_plugins_droplets.utils import Config as PluginConfig
from pymodaq_plugins_droplets.app.droplet_UI import Ui_Form

from qtpy.QtCore import Slot, QDate, QThread

logger = set_logger(get_module_name(__file__))

main_config = Config()
plugin_config = PluginConfig()


# todo: modify the name of this class to reflect its application and change the name in the main
# method at the end of the script
class CustomAppDroplets(gutils.CustomApp):

    # todo: if you wish to create custom Parameter and corresponding widgets. These will be
    # automatically added as children of self.settings. Morevover, the self.settings_tree will
    # render the widgets in a Qtree. If you wish to see it in your app, add is into a Dock
    params = []

    def __init__(self, parent: gutils.DockArea):
        super().__init__(parent)

        self.setup_ui()

    def setup_docks(self):
        '''
        subclass method from CustomApp
        '''
        logger.debug('setting docks')

        # create 2 docks to display the camera DAQ_Viewer (one for its settings, one for its viewer)
        self.dock_detector_settings = Dock("Detector Settings", size=(350, 350))
        self.dockarea.addDock(self.dock_detector_settings, 'below')
        self.dock_detector = Dock("Detector Viewer", size=(350, 350))
        self.dockarea.addDock(self.dock_detector, 'above', self.dock_detector_settings)
        self.detector = DAQ_Viewer(self.dockarea, dock_settings=self.dock_detector_settings,
                                   dock_viewer=self.dock_detector, title="A detector")
        self.detector.daq_type = 'DAQ2D'
        self.detector.detector = 'Thorlabs_DCx'
        QtWidgets.QApplication.processEvents()

        # Create the dock for the Frequency axis DAQ_move for the bath
        self.dock_bath_freq = Dock("BathFreq", size=(350, 350))
        self.dockarea.addDock(self.dock_bath_freq, 'below', self.dock_detector_settings)
        move_widget = QtWidgets.QWidget()
        self.move_bath_freq = DAQ_Move(move_widget)
        self.move_bath_freq.actuator = 'AWGTrueform'
        self.move_bath_freq.controller = 'AWGTrueform'
        self.move_bath_freq.channel = 1
        self.dock_bath_freq.addWidget(move_widget)

        # Create the dock for the Voltage axis DAQ_move for the bath
        self.dock_bath_volt = Dock("BathAmp", size=(350, 350))
        self.dockarea.addDock(self.dock_bath_volt, 'above', self.dock_bath_freq)
        move_widget = QtWidgets.QWidget()
        self.move_bath_volt = DAQ_Move(move_widget)
        self.move_bath_volt.actuator = 'AWGTrueform'
        self.move_bath_volt.controller = 'AWGTrueform'
        self.move_bath_volt.channel = 1
        self.dock_bath_volt.addWidget(move_widget)
        self.move_bath_volt.settings.child('move_settings').child('multiaxes').child('axis').setValue('Voltage1')

        # Create the dock for the Frequency axis DAQ_move for the droplets generation
        self.dock_drop_freq = Dock("DropFreq", size=(350, 350))
        self.dockarea.addDock(self.dock_drop_freq, 'below', self.dock_detector_settings)
        move_widget = QtWidgets.QWidget()
        self.move_drop_freq = DAQ_Move(move_widget)
        self.move_drop_freq.actuator = 'AWGTrueform'
        self.move_drop_freq.controller = 'AWGTrueform'
        self.dock_drop_freq.addWidget(move_widget)

        # Create the dock for the Voltage axis DAQ_move
        self.dock_drop_volt = Dock("DropAmp", size=(350, 350))
        self.dockarea.addDock(self.dock_drop_volt, 'above', self.dock_bath_freq)
        move_widget = QtWidgets.QWidget()
        self.move_drop_volt = DAQ_Move(move_widget)
        self.move_drop_volt.actuator = 'AWGTrueform'
        self.move_drop_volt.controller = 'AWGTrueform'
        self.dock_drop_volt.addWidget(move_widget)
        self.move_drop_volt.settings.child('move_settings').child('multiaxes').child('axis').setValue('Voltage1')

        QtWidgets.QApplication.processEvents()


        # Todo Create the custom UI
        self.DCC = Dock('Droplet Control Center')
        self.dockarea.addDock(self.DCC, 'above', self.dock_bath_freq)

        widget = QtWidgets.QWidget()
        self.ui = Ui_Form()
        self.ui.setupUi(widget)

        self.move_drop_volt.settings.child('move_settings', 'channel').setValue(2)
        self.move_drop_freq.settings.child('move_settings', 'channel').setValue(2)
        self.move_bath_freq.settings.child('move_settings', 'waveform').setValue('Sinus')
        self.move_drop_freq.settings.child('move_settings', 'waveform').setValue('Sinus')


        # self.docks['TestDock'].addWidget(self.settings_tree)
        self.DCC.addWidget(widget)

        self.ui.BathFreqSend.clicked.connect(self.change_bath_frequency)
        self.ui.BathAmpSend.clicked.connect(self.change_bath_voltage)
        self.ui.DropFreqSend.clicked.connect(self.change_drop_frequency)
        self.ui.DropAmpSend.clicked.connect(self.change_drop_voltage)
        self.ui.buttonGroup.buttonClicked.connect(self.change_waveform)
        self.ui.groupBox.clicked.connect(self.initialize_bath)
        self.ui.groupBox_2.clicked.connect(self.initialize_drop)
        self.ui.groupBox_3.clicked.connect(self.initialize_Cam)
        self.ui.ExposureSpin.editingFinished.connect(self.change_exposure)
        QThread.msleep(1000)
        logger.debug('docks are set')

    def initialize_drop(self):
        if self.ui.groupBox_2.isChecked() and not self.move_drop_volt.initialized_state:
            self.move_drop_volt.init_hardware()
            QThread.msleep(1000)
            self.move_drop_freq.init_hardware()
            QThread.msleep(1000)
            self.move_drop_freq.settings.child('move_settings', 'waveform').setValue('Square')

        elif not self.ui.groupBox_2.isChecked() and self.move_drop_volt.initialized_state:
            self.move_drop_freq.close()
            self.move_drop_volt.close()


    def initialize_bath(self):
        if self.ui.groupBox.isChecked() and not self.move_bath_volt.initialized_state:
            self.move_bath_volt.init_hardware()
            QThread.msleep(1000)
            self.move_bath_freq.init_hardware()
            QThread.msleep(1000)
            self.move_bath_freq.settings.child('move_settings', 'waveform').setValue('Sinus')

        elif not self.ui.groupBox.isChecked() and self.move_bath_volt.initialized_state:
            self.move_bath_freq.close()
            self.move_bath_volt.close()



    def initialize_Cam(self):
        if self.ui.groupBox_3.isChecked() and not self.detector.initialized_state:
            self.detector.init_hardware()
            QThread.msleep(1000)
            self.detector.grab()
        elif not self.ui.groupBox_3.isChecked() and self.detector.initialized_state:
            self.detector.close()

    def change_exposure(self):
        self.detector.settings.child('detector_settings', 'exposure').setValue(self.ui.ExposureSpin.value()*0.1)

    def change_bath_frequency(self):
        self.move_bath_freq.move_abs(self.ui.BathFreqSpin.value())
        pass
    def change_bath_voltage(self, voltage):
        self.move_bath_volt.move_abs(self.ui.BathAmpSpin.value()*(1e-3))
        pass

    def change_drop_frequency(self):
        self.move_drop_freq.move_abs(self.ui.DropFreqSpin.value())
        pass
    def change_drop_voltage(self, voltage):
        self.move_drop_volt.move_abs(self.ui.DropAmpSpin.value()*(1e-3))
        pass

    def change_waveform(self, waveform):
        self.move_bath_freq.settings.child('move_settings', 'waveform').setValue(waveform.objectName())

    def setup_actions(self):
        """Method where to create actions to be subclassed. Mandatory

        Examples
        --------
        See Also
        --------
        ActionManager.add_action
        """
        self.add_action('quit', 'Quit', 'close2', "Quit program")
        self.add_action('grab', 'Grab', 'camera', "Grab from camera", checkable=True)
        self.add_action('load', 'Load', 'Open', "Load target file (.h5, .png, .jpg) or data from camera"
                        , checkable=False)
        self.add_action('save', 'Save', 'SaveAs', "Save current data", checkable=False)

    def connect_things(self):
        """Connect actions and/or other widgets signal to methods"""
        pass

    def setup_menu(self, menubar: QtWidgets.QMenuBar = None):
        """Non mandatory method to be subclassed in order to create a menubar

        create menu for actions contained into the self._actions, for instance:

        Examples
        --------
        See Also
        --------
        pymodaq.utils.managers.action_manager.ActionManager
        """
        file_menu = menubar.addMenu('File')
        self.affect_to('load', file_menu)
        self.affect_to('save', file_menu)
        file_menu.addSeparator()
        self.affect_to('quit', file_menu)

    def value_changed(self, param):
        """ Actions to perform when one of the param's value in self.settings is changed from the
        user interface

        For instance:
        if param.name() == 'do_something':
            if param.value():
                print('Do something')
                self.settings.child('main_settings', 'something_done').setValue(False)

        Parameters
        ----------
        param: (Parameter) the parameter whose value just changed
        """
        pass


def main():
    from pymodaq_gui.utils.utils import mkQApp
    app = mkQApp('CustomApp')

    mainwindow = QtWidgets.QMainWindow()
    dockarea = gutils.DockArea()
    mainwindow.setCentralWidget(dockarea)

    # todo: change the name here to be the same as your app class
    prog = CustomAppDroplets(dockarea)

    mainwindow.show()

    app.exec()


if __name__ == '__main__':
    main()
