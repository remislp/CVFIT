import os
import numpy as np

from PySide.QtGui import *
from PySide.QtCore import *

from cvfit import cfio
import cvfit.myqtlib.myqtcommon as mqt
import cvfit.myqtlib.dialogs as dialogs


class DataBlock(QWidget):
    def __init__(self, parent=None):
        super(DataBlock, self).__init__(parent)
        self.parent = parent
   
        loadButton = QPushButton("&Load new data")
        self.connect(loadButton, SIGNAL('clicked()'), self.on_load)
        dataListView = QListView()
        self.dataListModel = QStandardItemModel()
        dataListView.setModel(self.dataListModel)
        plotButton = QPushButton("&Plot data")
        self.connect(plotButton, SIGNAL('clicked()'), self.on_plot)
        layout = QVBoxLayout(self)
        layout.addWidget(loadButton)
        layout.addWidget(dataListView)
        layout.addWidget(plotButton)
        layout.addStretch(1)
        
    def on_plot(self):
        
        self.parent.data = []
        for row in range(self.dataListModel.rowCount()):
            i = self.dataListModel.index(row, 0)
            checked = (self.dataListModel.data(i, Qt.CheckStateRole) ==
                Qt.Checked)
            if checked:
                self.parent.data.append(self.allsets[row])
        self.parent.plotblk.on_show()

    def on_load(self):
        filename, path = QFileDialog.getOpenFileName(self.parent,
                "Open a data file...", ".",
                "CSV files (*.csv);;TXT files (*.txt);;All files (*.*)")
        self.parent.log.write('\nLoading file: ' + filename)
        
        try:
            self.allsets = cfio.read_sets_from_csv(filename, col=2)
            self.dataListModel.clear()
            for set in self.allsets:
                item = QStandardItem(set.title)
                item.setCheckState(Qt.Checked)
                item.setCheckable(True)
                self.dataListModel.appendRow(item)
            self.parent.log.write("Loaded: " + 
                os.path.split(str(filename))[1])
            
            self.parent.data = self.allsets
            self.parent.fname = filename
            
        except ValueError:
            self.parent.log.write('fitting.py: WARNING: Oops!' + 
                'File did not load properly...')


class EquationBlock(QWidget):
    def __init__(self, parent=None):
        super(EquationBlock, self).__init__(parent)
        self.parent = parent
        
        eqLabel = QLabel("Please choose equation:                                     ")
        self.eqTitles = [
        '(1) Polynomial (inc. straight line)',
        '(2) Langmuir hyperbola(s) (inc. or dec.)',
        '(3) Hill equation(s) (inc. or dec./common K or max)',
        '(4) Langmuir hyperbola(s) plus straight line',
        '(5) Hill equation(s) plus straight line',
        '(6) Power function y=ybar*(x/x0)^n (linear on log-log plot)',
        '(7) Binding inhibition curve (parameter=KB)']
        self.eqList = QListWidget()
        for name in self.eqTitles:
            self.eqList.addItem(name)

        eqButton = QPushButton("&Load equation")
        self.connect(eqButton, SIGNAL('clicked()'), self.on_equation)
        guessButton = QPushButton("&Initial guesses")
        self.connect(guessButton, SIGNAL('clicked()'), self.on_guess)
        fitButton = QPushButton("&Fit")
        self.connect(fitButton, SIGNAL('clicked()'), self.on_fit)
        
        layout = QVBoxLayout(self)
        layout.addWidget(eqLabel)
        layout.addWidget(self.eqList)
        layout.addWidget(eqButton)
        layout.addWidget(guessButton)
        layout.addWidget(fitButton)
        layout.addStretch(1)
        
    def on_fit(self):
        for fs in self.parent.fits:
            fs.fit()
            fs.calculate_errors()
        self.parent.plotblk.on_show(plotFit=True)
        
    def on_guess(self):
        self.parent.plotblk.on_show(plotGuesses=True)
        dialog = dialogs.GuessDlg(self.parent.fits)
        if dialog.exec_():
            fs = dialog.return_guesses()
        self.parent.fits = fs
        self.parent.plotblk.on_show(plotGuesses=True)
        
    def on_equation(self):
        row = self.eqList.currentRow()
        if row == 1:
            eqname = 'Langmuir'
            eqtype = 'Hill'
        elif row == 2:
            eqname = 'Hill'
            eqtype = 'Hill'
        else:
            self.parent.log.write("This eqation is not implemented yet.")
            self.parent.log.write("Please, choose other equation.")
        
        self.parent.fits = []
        dialog = dialogs.EquationDlg(self.parent.data, eqtype, eqname, self.parent.log)
        if dialog.exec_():
            self.parent.fits = dialog.return_equation()
            
        
class TextBlock(QWidget):
    def __init__(self, parent=None):
        super(TextBlock, self).__init__(parent)
        self.parent = parent
        
        # Prepare text box for printout and set where printout goes
        self.textBox = QTextBrowser()
        self.parent.log = mqt.PrintLog(self.textBox) #, sys.stdout)    
        mqt.startInfo(self.parent.log)
        textVBox = QVBoxLayout()
        textVBox.addWidget(self.textBox)
        aboutButton = QPushButton("&ABOUT")
        self.connect(aboutButton, SIGNAL("clicked()"), self.on_about)
        textVBox.addWidget(aboutButton)
        
        layout = QVBoxLayout(self)
        layout.addWidget(self.textBox)
        layout.addWidget(aboutButton)
        
        
    def on_about(self):
        dialog = mqt.AboutDlg(self)
        if dialog.exec_():
            pass
        
        
class PlotBlock(QWidget):
    def __init__(self, parent=None):
        super(PlotBlock, self).__init__(parent)
        self.parent = parent
        #self.plot_legend = False
        
        # Prepare plot window
        layout = QVBoxLayout(self)
        self.legendChB = QCheckBox("Show L&egend")
        self.legendChB.setChecked(True)
        #self.connect(self.legendChB, SIGNAL("stateChanged()"), self.on_something_changed)
        self.parent.canvas = mqt.MatPlotWin()
        canvastools = mqt.MatPlotTools(self.parent.canvas, self.parent)
        layout.addWidget(self.legendChB)
        layout.addWidget(self.parent.canvas)
        layout.addWidget(canvastools)
        
    def on_something_changed(self):
        self.plot_legend = False
        self.plot_legend = self.legendChB.isChecked()
        self.on_show()
        
    def on_show(self, plotGuesses=False, plotFit=False):
        self.parent.canvas.axes.clear()
        self.parent.canvas.axes.grid(True)
        
        for set in self.parent.data:
            self.parent.canvas.axes.semilogx(set.X, set.Y, 'o', label=set.title)
            
        if plotGuesses:
            for session in self.parent.fits:
                logplotX = np.log10(set.X)
                plotX = 10 ** np.linspace(np.floor(np.amin(logplotX) - 1),
                    np.ceil(np.amax(logplotX)), 100)
                plotYg = session.eq.equation(plotX, session.eq.guess)
                self.parent.canvas.axes.semilogx(plotX, plotYg, 'y-')
        
        if plotFit:
            for session in self.parent.fits:
                logplotX = np.log10(set.X)
                plotX = 10 ** np.linspace(np.floor(np.amin(logplotX) - 1),
                    np.ceil(np.amax(logplotX)), 100)
                plotYg = session.eq.equation(plotX, session.eq.pars)
                self.parent.canvas.axes.semilogx(plotX, plotYg, 'b-')

        if self.legendChB.isChecked():
            self.parent.canvas.axes.legend(loc=2)
            
            
        
        #self.parent.canvas.axes.set_ylim(0, 1)
        #self.parent.canvas.axes.xaxis.set_ticks_position('bottom')
        #self.parent.canvas.axes.yaxis.set_ticks_position('left')
        self.parent.canvas.draw()
        
        
        
        
#
#        for row in range(self.series_list_model.rowCount()):
#            model_index = self.series_list_model.index(row, 0)
#            checked = self.series_list_model.data(model_index,
#                Qt.CheckStateRole) == Qt.Checked
#            name = str(self.series_list_model.data(model_index))
#
#            if checked:
#                has_series = True
#                self.data.add_series_to_fit(name)
#                set = self.data.get_series_data(name)
#                X = set[0]
#                Y = set[1]
#                Yerr = set[2]
#                self.axes.semilogx(X, Y, 'o', label=name)
#
#        if self.fitted:
#
#            self.equation.calcCurves()
#            xy = self.equation.curves
#            for i in range(self.equation.nsets):
#                #name1 = 'fit'+(i+1)
#                self.axes.semilogx(xy[0], xy[i+1], 'r-')
#
#        self.canvas.draw()