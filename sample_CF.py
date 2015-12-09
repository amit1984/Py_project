import sys
from PyQt4 import QtCore, QtGui
if 0:
    import sip
    sip.settracemask(0x3f)

from PyQt4 import Qt
import PyQt4.Qwt5 as Qwt
from PyQt4.Qwt5.anynumpy import *
import zmq
from time import sleep

def fun():
 while 1:
    context = zmq.Context()
    sock = context.socket(zmq.REP)
    sock.bind("tcp://127.0.0.1:5677")
    message = str(sock.recv())
    print message
    sock.close()
    context.term()
    return message

class Ui_MainWindow(object):
    def setupUi(self, MainWindow):
        MainWindow.setObjectName( "MainWindow" )
        MainWindow.resize(800, 600)
        self.gridLayout = QtGui.QGridLayout(MainWindow)
        self.centralwidget = QtGui.QWidget(MainWindow)
        self.centralwidget.setObjectName( "centralwidget" )
        self.verticalLayout = QtGui.QVBoxLayout(self.centralwidget)
        self.verticalLayout.setObjectName( "verticalLayout" )
        self.mdiArea = QtGui.QMdiArea(self.centralwidget)
        self.mdiArea.setVerticalScrollBarPolicy(QtCore.Qt.ScrollBarAsNeeded)
        self.mdiArea.setHorizontalScrollBarPolicy(QtCore.Qt.ScrollBarAsNeeded)
        self.mdiArea.setActivationOrder(QtGui.QMdiArea.CreationOrder)
        self.mdiArea.setViewMode(QtGui.QMdiArea.TabbedView)
        self.mdiArea.setTabsClosable(True)
        self.mdiArea.setTabsMovable(True)
        self.mdiArea.setObjectName( "mdiArea" )
        self.verticalLayout.addWidget(self.mdiArea)
        MainWindow.setCentralWidget(self.centralwidget)
        self.menubar = QtGui.QMenuBar(MainWindow)
        self.menubar.setGeometry(QtCore.QRect(0, 0, 200, 21))
        self.menubar.setObjectName( "menubar" )
        self.menuAdd = QtGui.QMenu(self.menubar)
        self.menuAdd.setObjectName( "menuAdd" )
        MainWindow.setMenuBar(self.menubar)
        self.statusbar = QtGui.QStatusBar(MainWindow)
        self.statusbar.setObjectName( "statusbar" )
        MainWindow.setStatusBar(self.statusbar)
        self.menubar.addAction(self.menuAdd.menuAction())

        self.retranslateUi(MainWindow)
        QtCore.QMetaObject.connectSlotsByName(MainWindow)
        

    def retranslateUi(self, MainWindow):
        MainWindow.setWindowTitle(   "DETECT 2.0.5.0" )
        self.gridLayout = QtGui.QGridLayout(MainWindow)
        self.gridLayout.setObjectName( ("gridLayout"))
        self.centralWidget = QtGui.QWidget(MainWindow)
        self.gridLayout.addWidget(QtGui.QLineEdit("5",parent=None),2,1)
        self.menubar.addMenu('&File')
        self.menubar.addMenu('&view')
        self.menubar.addMenu('&Tools')
        self.menubar.addMenu('&Not Logging')
        self.menubar.addMenu('&Filename')
    


class Sensor_Form(object):
    def setupUi(self, Form):  
        Form.setObjectName( ("Form"))
        Form.resize(400, 800)
        self.gridLayout = QtGui.QGridLayout(Form)
        self.gridLayout.setObjectName( ("gridLayout"))
        self.centralWidget = QtGui.QWidget(Form)
        self.demo = Qwt.QwtPlot(Qwt.QwtText("Detect Online Data"))
        self.demo.setCanvasBackground(Qt.Qt.white)
        self.demo.plotLayout().setAlignCanvasToScales(True)
        self.demo.setFixedHeight(400)
        self.demo.setMinimumWidth(450)   
        grid = Qwt.QwtPlotGrid()
        grid.attach(self.demo)
        grid.setPen(Qt.QPen(Qt.Qt.black, 0, Qt.Qt.DotLine))
        self.gridLayout.addWidget(self.demo,0,0)
        self.gridLayout.addWidget(QtGui.QLineEdit("select parameters",parent=None),0,1,QtCore.Qt.AlignTop)
        self.demo.setAxisTitle(Qwt.QwtPlot.xBottom, "longitude")
        self.demo.setAxisTitle(Qwt.QwtPlot.yLeft, "latitude")
        #self.demo.enableAxis(Qwt.QwtPlot.yRight)
        self.demo.curve = Qwt.QwtPlotCurve("Data y")
        self.demo.curve.setYAxis(Qwt.QwtPlot.yLeft)
        self.demo.curve.setPen(Qt.QPen(Qt.Qt.red))
        self.demo.curve.setSymbol(Qwt.QwtSymbol(
          Qwt.QwtSymbol.Ellipse,
          Qt.QBrush(),
          Qt.QPen(Qt.Qt.red),
          Qt.QSize(7, 7)))
        self.demo.curve.attach(self.demo)    
        ##message = fun()
        #message.split(str=",", num=string.count(message)). for VT200
        ##self.demo.curve.setData([message], [message])
        ##self.demo.replot()   
        grid = Qwt.QwtPlotGrid()
        grid.attach(self.demo)
        grid.setPen(Qt.QPen(Qt.Qt.black, 0, Qt.Qt.DotLine))
        # add a Timer
        #timer = Qt.QTimer()
        #timer.connect(timer, Qt.SIGNAL('timeout()'), self.setupUi)
        #timer.start(1)
        
        self.timer = QtCore.QTimer()
        QtCore.QObject.connect(self.timer, QtCore.SIGNAL("timeout()"), self.timerRun)
        self.timer.start( 500 )
    def timerRun(self):
                print "XXX"
                message = fun()
                msg1 = message.replace("(","")
                msg2 = msg1.replace(")","")
                msg = msg2.split(',')               
                self.demo.curve.setData([float(msg[0])], [float(msg[1])])
                self.demo.replot()   
    
       
class MyApp(QtGui.QMainWindow):
    def __init__(self, parent=None):
        super(MyApp, self).__init__(parent)
        self.ui = Ui_MainWindow()
        self.ui.setupUi(self)

    def Add_Subwindow(self):
        widget = QtGui.QWidget()
        self.subwin_abq = Sensor_Form()
        self.subwin_abq.setupUi(widget)
        self.subwindow = QtGui.QMdiSubWindow(self.ui.mdiArea) 
        widget.setParent(self.subwindow)
        self.subwindow.setWidget(widget)  
        self.subwindow.setWindowTitle("Sensor Data")
        self.ui.mdiArea.addSubWindow(self.subwindow)
        widget.show()
        self.subwindow.show()
        self.subwindow.widget().show()
        
if __name__ == "__main__":
    app = QtGui.QApplication(sys.argv)
    window = MyApp()
    window.show()
    window.Add_Subwindow()
    sys.exit(app.exec_())
