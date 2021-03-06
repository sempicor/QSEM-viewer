# -*- coding: utf-8 -*-
#
# Copyright 2016 Petras Jokubauskas
#
# This library is free software: you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation, either version 3 of the License, or
# (at your option) any later version.
#
# This library is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with any project and source this library is coupled.
# If not, see <http://www.gnu.org/licenses/>.
#

from PyQt5 import QtCore, Qt, QtGui, QtWidgets
import pyqtgraph as pg

from ..misc import xray_util as xu
from .node import ElementLineTreeModel, SimpleDictNode

from . import element_table_Qt5
from . import CustomWidgets as cw
from .CustomPGWidgets import CustomViewBox, CustomAxisItem
from os import path
import json

main_path = path.join(path.dirname(__file__), path.pardir)
icon_path = path.join(main_path, 'icons')
conf_path = path.join(main_path,
                      'configurations',
                      'lines.json')

with open(conf_path) as fn:
    jsn = fn.read()
lines = json.loads(jsn)

BACKGROUND_COLOR = pg.mkColor(0, 43, 54)


# dealling with greek letters, where windows dos retards made it
# into  latin:

dos_greek = {'a': 'α', 'b': 'β', 'g': 'γ'}


def utfize(text):
    """replace the a,b,c latin letters used by retards stuck in
    ms-dos age to greek α, β, γ
    """
    return ''.join(dos_greek[s] if s in dos_greek else s for s in text)

#pg.setConfigOptions(background=pg.mkColor(0, 43, 54))


class XRayElementTable(element_table_Qt5.ElementTableGUI):
    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.setSpan(0, 3, 1, 3)  # for preview option
        self.setSpan(1, 3, 1, 3)  # for line intensity filter
        self.preview = Qt.QTableWidgetItem('preview')
        self.setItem(0, 3, self.preview)
        self.previewCheck = self.item(0, 3)
        self.previewCheck.setCheckState(QtCore.Qt.Checked)
        self.hv_value = Qt.QDoubleSpinBox()
        self.hv_value.setValue(15.)
        self.hv_value.setSuffix(" kV")
        self.hv_value.setToolTip(''.join(['set HV value which restricts x',
                                          'axis and influences\n',
                                          'heights of',
                                          'preview lines as function\n',
                                          ' of effectivness (2.7 rule)']))
        self.hv_value.setRange(0.1, 1e4)
        self.setCellWidget(1, 3, self.hv_value)
        self.itemChanged.connect(self.setPreviewEnabled)
    
    def setPreviewEnabled(self):
        self.preview_enabled = self.previewCheck.checkState()
        

class AutoEditor(Qt.QDialog):
    """widget for entering min max x and y for
    auto range of the spectra"""
    def __init__(self, title, x_range, y_range, parent=None):
        Qt.QDialog.__init__(self, parent)
        self.setWindowTitle(title)
        self.verticalLayout = Qt.QVBoxLayout(self)
        self._setup_ui()
        self._setup_connections(x_range, y_range)

    def _setup_ui(self):
        self.groupBox1 = Qt.QGroupBox("x min-max", self)
        self.gridLayout = Qt.QHBoxLayout(self.groupBox1)
        self.x_min = Qt.QLineEdit()
        self.x_max = Qt.QLineEdit()
        self.gridLayout.addWidget(self.x_min)
        self.gridLayout.addWidget(self.x_max)
        self.verticalLayout.addWidget(self.groupBox1)

        self.groupBox2 = Qt.QGroupBox("y min-max", self)
        self.gridLayout2 = Qt.QHBoxLayout(self.groupBox2)
        self.y_min = Qt.QLineEdit()
        self.y_max = Qt.QLineEdit()
        self.gridLayout2.addWidget(self.y_min)
        self.gridLayout2.addWidget(self.y_max)
        self.verticalLayout.addWidget(self.groupBox2)

        self.buttonBox = Qt.QDialogButtonBox(self)
        self.buttonBox.setStandardButtons(Qt.QDialogButtonBox.Cancel |
                                          Qt.QDialogButtonBox.Ok)
        self.verticalLayout.addWidget(self.buttonBox)

    def _setup_connections(self, x_range, y_range):
        self.x_min.setText(str(x_range[0]))
        self.x_max.setText(str(x_range[1]))
        self.y_min.setText(str(y_range[0]))
        self.y_max.setText(str(y_range[1]))
        self.buttonBox.rejected.connect(self.reject)
        self.buttonBox.accepted.connect(self.accept)

    def return_ranges(self):
        x_range = (float(self.x_min.text()), float(self.x_max.text()))
        y_range = (float(self.y_min.text()), float(self.y_max.text()))
        return x_range, y_range



        

class LineEnabler(Qt.QWidget):
    
    def __init__(self, parent=None):
        Qt.QWidget.__init__(self,  parent)
        self.gridLayout = QtWidgets.QGridLayout(self)
        self.buttonHide = QtWidgets.QPushButton(self)
        self.buttonHide.setText('Hide')
        self.gridLayout.addWidget(self.buttonHide, 4, 2, 1, 1)
        spacerItem = QtWidgets.QSpacerItem(20, 40,
                                           QtWidgets.QSizePolicy.Minimum,
                                           QtWidgets.QSizePolicy.Expanding)
        self.gridLayout.addItem(spacerItem, 3, 2, 1, 1)
        self.buttonToggle = QtWidgets.QPushButton(self)
        self.buttonToggle.setText('Save to custom')
        self.gridLayout.addWidget(self.buttonToggle, 2, 2, 1, 1)
        self.buttonSave = QtWidgets.QPushButton(self)
        self.buttonSave.setText('Save to default')
        self.gridLayout.addWidget(self.buttonSave, 1, 2, 1, 1)
        self.atom = QtWidgets.QLabel(self)
        font = QtGui.QFont()
        font.setPointSize(40)
        self.atom.setFont(font)
        self.atom.setFrameShape(QtWidgets.QFrame.StyledPanel)
        self.atom.setFrameShadow(QtWidgets.QFrame.Raised)
        self.atom.setLineWidth(2)
        self.atom.setAlignment(QtCore.Qt.AlignCenter)
        self.gridLayout.addWidget(self.atom, 0, 2, 1, 1)
        self.lineView = cw.LeavableTreeView(self)
        self.gridLayout.addWidget(self.lineView, 0, 0, 4, 2)
        if parent is not None:
            self.buttonHide.pressed.connect(parent.hide)
        else:
            self.buttonHide.pressed.connect(self.hide)
        
    @QtCore.pyqtSlot(str)
    def set_element_lines(self,  element):
        if self.parent() is not None:
            if self.parent().isHidden():
                self.parent().show()
        else:
            self.show()
        self.atom.setText(element)
        node_tree = SimpleDictNode.node_builder(lines[element],
                                                name=element)
        model = ElementLineTreeModel(node_tree)
        self.lineView.setModel(model)
        

class PenEditor(Qt.QDialog):
    def __init__(self, text_size, text_color, pen, parent=None):
        Qt.QDialog.__init__(self, parent)
        self.setWindowTitle('customize preview')
        self.verticalLayout = Qt.QVBoxLayout(self)
        self._setup_ui()
        self._setup_connections(text_size, text_color, pen)

    def _setup_ui(self):
        self.groupBox1 = Qt.QGroupBox("Text Style", self)
        self.formLayout = Qt.QFormLayout(self.groupBox1)
        self.formLayout.setWidget(0,
                                  Qt.QFormLayout.LabelRole,
                                  Qt.QLabel('color'))
        self.text_color_btn = pg.ColorButton()
        self.formLayout.setWidget(0,
                                  Qt.QFormLayout.FieldRole,
                                  self.text_color_btn)
        self.formLayout.setWidget(1,
                                  Qt.QFormLayout.LabelRole,
                                  Qt.QLabel('size'))
        self.text_size_spn = pg.SpinBox(value=12, bounds=(1, 64),
                                        suffix='pt', step=1,
                                        int=True)
        self.formLayout.setWidget(1,
                                  Qt.QFormLayout.FieldRole,
                                  self.text_size_spn)
        self.verticalLayout.addWidget(self.groupBox1)

        self.groupBox2 = Qt.QGroupBox("Line Style", self)
        self.formLayout2 = Qt.QFormLayout(self.groupBox2)
        self.formLayout2.setWidget(0,
                                  Qt.QFormLayout.LabelRole,
                                  Qt.QLabel('color'))
        self.line_color_btn = pg.ColorButton()
        self.formLayout2.setWidget(0,
                                  Qt.QFormLayout.FieldRole,
                                  self.line_color_btn)
        self.formLayout2.setWidget(1,
                                  Qt.QFormLayout.LabelRole,
                                  Qt.QLabel('width'))
        self.line_width_spn = pg.SpinBox(value=2, bounds=(0.1, 10),
                                         dec=1, minStep=0.1)
        self.formLayout2.setWidget(1,
                                  Qt.QFormLayout.FieldRole,
                                  self.line_width_spn)
        self.verticalLayout.addWidget(self.groupBox2)
        self.buttonBox = Qt.QDialogButtonBox(self)
        self.buttonBox.setStandardButtons(Qt.QDialogButtonBox.Cancel |
                                          Qt.QDialogButtonBox.Ok)
        self.verticalLayout.addWidget(self.buttonBox)

    def _setup_connections(self, text_size, text_color, pen):
        self.text_size_spn.setValue(text_size)
        self.text_color_btn.setColor(text_color)
        self.line_color_btn.setColor(pen.color())
        self.line_width_spn.setValue(pen.width())
        self.buttonBox.rejected.connect(self.reject)
        self.buttonBox.accepted.connect(self.accept)

    def return_styles(self):
        text_size = self.text_size_spn.value()
        text_color = self.text_color_btn.color()
        line_pen = pg.mkPen(color=self.line_color_btn.color(),
                            width=self.line_width_spn.value())
        return text_size, text_color, line_pen


class EDSCanvas(pg.PlotWidget):
    def __init__(self, kv=15, initial_mode='eds'):
        pg.PlotWidget.__init__(self,
                               viewBox=CustomViewBox(),
                               labels={'left': ['counts', 'cts']},
                               axisItems={'left': pg.AxisItem('left'),
                                          'bottom': CustomAxisItem('bottom')},
                               background=BACKGROUND_COLOR)
        #p1 the main plotItem/canvas
        #p2 secondary viewbox for EDS preview lines
        #p3 third viewbox for EDS marked lines
        self.p1 = self.plotItem
        self.p2 = pg.ViewBox()
        self.p3 = pg.ViewBox()
        self.p1.scene().addItem(self.p2)
        self.p2.setXLink(self.p1)
        self.p3.setXLink(self.p1)
        self.p3.setYLink(self.p1)
        self.bottom_axis = self.p1.axes['bottom']['item']
        self.updateViews()
        self.x_axis_mode = initial_mode
        self.set_kv(kv)
        self.p1.vb.sigResized.connect(self.updateViews)
        self.prev_text_size = 12
        self.prev_marker_pen = pg.mkPen((255,200,255, 180), width=2)
        self.prev_text_color = pg.mkColor((200,200,200))
        self.p1.setLimits(yMin=0)
        self.p3.setLimits(yMin=0)
        self.p2.setLimits(yMin=0)
        self.p2.setYRange(0, 1)
        self.set_xtal(8.75, 0.000144) # default to PET crystal
        self.set_x_mode(self.x_axis_mode)
        self.set_connections()
        
    def set_connections(self):
        self.bottom_axis.energyButton.toggled.connect(self.set_x_axis_from_gui)
    
    def set_x_axis_from_gui(self):
        if self.bottom_axis.energyButton.isChecked():
            self.set_x_mode('eds')
        else:
            self.set_x_mode('wds')
    
    def set_x_axis(self):
        if self.x_axis_mode == 'eds':
            self.p1.setLimits(xMin=-0.5)
            self.p1.setLabels(bottom='keV')
            self.set_kv(self.kv)
        elif self.x_axis_mode == 'wds':
            self.p1.setLimits(xMax=90000)
            self.p1.setLabels(bottom='sin θ')
    
    def tweek_preview_style(self):
        style_dlg = PenEditor(self.prev_text_size,
                              self.prev_text_color,
                              self.prev_marker_pen)
        if style_dlg.exec_():
            values = style_dlg.return_styles()
            self.prev_text_size, self.prev_text_color,\
            self.prev_marker_pen = values
        
    def set_xtal(self, two_D, K):
        self.two_D = two_D
        self.K = K
        self.axis_quotient = xu.calc_scale_to_sin_theta(two_D, K)
    
    def set_x_mode(self, mode):
        self.x_axis_mode = mode
        self.set_x_axis()
        if mode == 'eds':
            self.setXRange(0.45, self.kv)
        elif mode == 'wds':
            self.setXRange(20000, 88000)
    
    def set_kv(self, kv):
        self.kv = kv
        if self.x_axis_mode == 'eds':
            self.p1.setLimits(xMax=self.kv)
        elif self.x_axis_mode == 'wds':
            self.p1.setLimits(xMin=xu.energy_to_sin_theta(self.kv,
                                                          self.two_D,
                                                          self.K))
        
    def updateViews(self):
        self.p2.setGeometry(self.p1.vb.sceneBoundingRect())
        self.p2.linkedViewChanged(self.p1.vb, self.p2.XAxis)
    
    def previewLines(self, element, kv=None, lines=[]):
        if kv is None:
            kv = self.kv
        self.p2.clear()
        if len(lines) == 0:
            if self.x_axis_mode == 'eds':
                lines = xu.xray_lines_for_plot(element, kv)
            elif self.x_axis_mode == 'wds':
                lines = xu.xray_lines_for_plot_wds(element, two_D=self.two_D,
                                                   K=self.K, kv=kv) 
        else:
            #TODO
            pass
        for i in lines:
            line = pg.PlotCurveItem([i[1], i[1]],
                                    [0, i[2]],
                                    pen=self.prev_marker_pen)
            self.p2.addItem(line)
            html_color = 'rgba({0}, {1}, {2}, {3})'.format(
                self.prev_text_color.red(),
                self.prev_text_color.green(),
                self.prev_text_color.blue(),
                self.prev_text_color.alpha())
            text = pg.TextItem(html="""<body style="font-size:{2}pt;
                color:{3};">{0}<sub>{1}</sub></body>""".format(
                                element, utfize(i[0]),
                                self.prev_text_size, html_color),
                               anchor=(0., 1.))
            self.p2.addItem(text)
            text.setPos(i[1], i[2])
            
    def previewOneLine(self, element, line):
        x_pos = xu.xray_energy(element, line)
        if self.x_axis_mode == 'wds':
            x_pos = self.axis_quotient / x_pos
        gr_line = pg.PlotCurveItem([x_pos,  x_pos],
                        [0,  xu.xray_weight(element, line)], 
                        pen=self.prev_marker_pen)
        self.p2.addItem(gr_line)
    
    def clearPreview(self):
        self.p2.clear()
        
    def addLines(self, element, kv=None):
        pass
    
    def auto_custom(self):
        pass


class EDSSpectraGUI(cw.FullscreenableWidget):
    def __init__(self, parent=None, icon_size=None,
                 pet_opacity=None, initial_mode='eds'):
        cw.FullscreenableWidget.__init__(self, parent, icon_size)
        self.resize(550,550)
        self._pet_opacity = pet_opacity
        self.centralwidget = Qt.QWidget()
        self.setCentralWidget(self.centralwidget)
        self.horizontalLayout = Qt.QHBoxLayout(self.centralwidget)
        self.horizontalLayout.setContentsMargins(1,1,1,1)
        self._setup_toolbar()
        self.canvas = EDSCanvas(initial_mode='eds')
        self._setup_connections()
        self.horizontalLayout.addWidget(self.canvas)
        
    def _setup_connections(self):
        self.pet.elementHoveredOver.connect(self.canvas.previewLines)
        self.pet.elementHoveredOff.connect(self.canvas.clearPreview)
        self.config_preview.triggered.connect(
            self.canvas.tweek_preview_style)
        self.pet.hv_value.valueChanged.connect(self.canvas.set_kv)
        self.pet.someButtonRightClicked.connect(
            self.lineSelector.set_element_lines)
        self.lineSelector.lineView.entered.connect(
            self.preview_hovered_lines)
        self.lineSelector.lineView.mouseLeft.connect(
            self.canvas.clearPreview)
        
    def _setup_toolbar(self):
        #add spacer:
        self._empty2 = Qt.QWidget()
        self._empty2.setSizePolicy(Qt.QSizePolicy.Expanding,
                                   Qt.QSizePolicy.Expanding)
        self.toolbar.addWidget(self._empty2)
        self.actionElementTable = Qt.QAction(self)
        self.actionElementTable.setIcon(Qt.QIcon(path.join(icon_path,
                                                           'pt.svg')))
        self.toolbar.addAction(self.actionElementTable)
        self._setup_pet()
        self.actionElementTable.triggered.connect(self.show_pet)
        self.toolbar.addSeparator()
        self.auto_button = cw.CustomToolButton(self)
        self._setup_auto()
        self.toolbar.addWidget(self.auto_button)
        self.config_button = cw.CustomToolButton(self)
        self.config_button.setIcon(
            Qt.QIcon(path.join(icon_path, 'tango_preferences_system.svg')))
        self._setup_config()
        self.toolbar.addWidget(self.config_button)
        self._empty1 = Qt.QWidget()
        self._empty1.setSizePolicy(Qt.QSizePolicy.Expanding,
                                   Qt.QSizePolicy.Expanding)
        self.toolbar.addWidget(self._empty1)
        
        
    def _setup_auto(self):
        menu = Qt.QMenu('auto range')
        self.auto_all = Qt.QAction(Qt.QIcon(path.join(icon_path,
                                                      'auto_all.svg')),
                                   'all', self.auto_button)
        self.auto_width = Qt.QAction(Qt.QIcon(path.join(icon_path,
                                                        'auto_width.svg')),
                                     'width', self.auto_button)
        self.auto_height = Qt.QAction(Qt.QIcon(path.join(icon_path,
                                                    'auto_height.svg')),
                                      'height', self.auto_button)
        self.auto_custom = Qt.QAction(Qt.QIcon(path.join(icon_path,
                                                    'auto_custom.svg')),
                                      'custom', self.auto_button)
        self.custom_conf = Qt.QAction('custom config.', self.auto_button)
        action_list = [self.auto_all, self.auto_width, self.auto_height,
                       self.auto_custom, self.custom_conf]
        for i in action_list[:-1]:
            i.triggered.connect(self.auto_button.set_action_to_default)
        menu.addActions(action_list)
        self.auto_button.setMenu(menu)
        self.auto_button.setDefaultAction(self.auto_all)
        
    def _setup_config(self):
        menu = Qt.QMenu('config')
        self.config_preview = Qt.QAction(Qt.QIcon(path.join(icon_path,
                                        'tango_preferences_system.svg')),
                                    'preview style',
                                    self.config_button)
        self.config_burned = Qt.QAction(Qt.QIcon(path.join(icon_path,
                                        'tango_preferences_system.svg')),
                                    'burned style',
                                    self.config_button)
        action_list = [self.config_preview, self.config_burned]
        for i in action_list:
            i.triggered.connect(self.config_button.set_action_to_default)
        menu.addActions(action_list)
        self.config_button.setMenu(menu)
        self.config_button.setDefaultAction(self.config_preview)
        
    def _setup_pet(self):
        self.dock_pet_win = Qt.QDockWidget('Periodic table', self)
        self.dock_pet_win.setSizePolicy(QtGui.QSizePolicy.Maximum,
                                        QtGui.QSizePolicy.Maximum)
        self.dock_line_win = Qt.QDockWidget('Line selection', self)
        self.pet = XRayElementTable(parent=self.dock_pet_win)
        self.lineSelector = LineEnabler(self.dock_line_win)
        self.dock_pet_win.setWidget(self.pet)
        self.addDockWidget(QtCore.Qt.RightDockWidgetArea,
                           self.dock_pet_win)
        self.dock_pet_win.setAllowedAreas(QtCore.Qt.NoDockWidgetArea)
        self.dock_pet_win.setFloating(True)
        self.dock_line_win.setWidget(self.lineSelector)
        self.addDockWidget(QtCore.Qt.RightDockWidgetArea,
                           self.dock_line_win)
        self.dock_line_win.setAllowedAreas(QtCore.Qt.NoDockWidgetArea)
        self.dock_line_win.setFloating(True)
        if self._pet_opacity:
            self.dock_pet_win.setWindowOpacity(self._pet_opacity)
        self.dock_line_win.hide()
        self.dock_pet_win.hide()
        
    def show_pet(self):
        if self.dock_pet_win.isVisible():
            self.dock_pet_win.hide()
        else:
            self.dock_pet_win.show()
        
    def preview_hovered_lines(self, item):
        self.canvas.clearPreview()
        
        if item is None:
            self.canvas.clearPreview()
            return
        
        h_item = self.lineSelector.lineView.model().getNode(item)
        # hovered item/node ^
        path = h_item.get_tree_path().split(' ')
        
        if 'line' in h_item.name:
            item_type = 'family'
        elif 'line' in h_item._parent.name:
            item_type = 'line'
        else:
            item_type = 'element'
            
        if item_type == 'line':
            element = path[-3]
            line = path[-1]
            self.canvas.previewOneLine(element, line)
        elif item_type == 'family':
            element = path[-2]
            for i in h_item._children:
                self.canvas.previewOneLine(element, i.name)
        elif item_type == 'element':
            self.canvas.previewLines(element)
        
