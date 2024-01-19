#!/usr/bin/python3
# -*- coding: utf-8 -*-

import sys
from PyQt5.QtWidgets import (QApplication, QWidget, QAbstractButton, QHBoxLayout, QGroupBox,
                             QLineEdit, QVBoxLayout, QLabel, QGridLayout,QCheckBox, QFrame,
                             QPushButton, QInputDialog, QDialog, QPlainTextEdit, QMessageBox, 
                             QTabWidget, QTabBar, QMainWindow, QMenuBar, QAction, QFileDialog,
                             QSizePolicy, QScrollArea, QDesktopWidget, QTextEdit, QComboBox)
from PyQt5.QtGui import (QIcon, QPainter, QPixmap, QIntValidator, QFont, QPen, QPainter, QColor, 
                         QBrush, QPalette, QFontMetricsF, QTextCursor)
from PyQt5.QtCore import Qt, QRect, QSize, QThread, QThreadPool, QThread, QTimer, QEventLoop, pyqtSignal
from ET_3504_comm import getTemp, setCellParameters, initCommunication, getCOMports, connectET, disconnectET
import time
import os

import ast
import copy


QApplication.setAttribute(Qt.AA_DisableWindowContextHelpButton)


class PicButton(QAbstractButton):
    def __init__(self, pixmap, pixmap_checked, pixmap_disabled, parent=None):
        super(PicButton, self).__init__(parent)
        self.pixmap = pixmap
        self.pixmap_checked = pixmap_checked
        self.pixmap_disabled = pixmap_disabled

        self.setCheckable(True)
        
        self.pressed.connect(self.update)
        self.setMaximumSize(64, 64)

    def paintEvent(self, event):
        currentPixmap = self.pixmap
        
        if self.isEnabled():
            if self.isChecked():
                currentPixmap = self.pixmap_checked
        else:
            currentPixmap = self.pixmap_disabled
        
        painter = QPainter(self)
        painter.drawPixmap(event.rect(), currentPixmap)
        
    def sizeHint(self):
        return self.pixmap.size()

class ETSwitch(QPushButton):
    def __init__(self, parent = None):
        super().__init__(parent)
        self.setCheckable(True)
        self.setMinimumWidth(20)
        self.setMinimumHeight(70)

    def paintEvent(self, event):
        
        label = "ON" if self.isChecked() else "OFF"
        bg_color = QColor(64,255,64) if self.isChecked() else QColor(255,64,64)

        height = 30
        width = 25
        verticalShift = 12

        painter = QPainter(self)
        painter.setRenderHint(QPainter.Antialiasing)
        painter.setBrush(QColor(126,126,126))

        pen = QPen(Qt.black)
        pen.setWidth(2)
        pen.setCapStyle(Qt.FlatCap)
        painter.setPen(pen)
        
        painter.drawRect(verticalShift, 1, width, 2*height)
        painter.setBrush(QBrush(bg_color))
        sw_rect = QRect(verticalShift, 1, width, height)
        if self.isChecked():
            sw_rect.moveBottom(2*height)
        painter.drawRect(sw_rect)
        painter.drawText(sw_rect, Qt.AlignCenter, label)

class CellShuterGB(QGroupBox):
    def __init__(self, cellName, parent = None):
        super().__init__(parent)
        
        self.cellName = cellName
        self.UPPER_GROUP_BOX_HEIGHT = 100
        
        self.initUI()
        
    def initUI(self):
        self.setTitle(self.cellName)
        self.setFont(QFont("Times", 12, QFont.Bold))
        self.setCheckable(False)
        self.setMaximumHeight(self.UPPER_GROUP_BOX_HEIGHT)
        self.setAlignment(Qt.AlignCenter)
        
        self.shutterSwith = ETSwitch()
        self.shutterSwith.setFont(QFont("Times", 10, QFont.Bold))
        self.shutterSwith.setChecked(False)
         
        gbLayout = QHBoxLayout()
        gbLayout.addWidget(self.shutterSwith)
        self.setLayout(gbLayout)

class CellGB(QGroupBox):
    def __init__(self, parent, cellName, cellID):
        super().__init__(parent)
        
        self.cellName = cellName
        self.cellID = cellID
        self.CELL_CONNECTED = False
        self.GROUP_BOX_HEIGHT = 180
        self.GROUP_BOX_WIDTH = 200
        self.parent=parent
        self.cellRunning = False
        self.currentSP = 0
        self.currentTemp = 0
        
        self.initUI()
        
    def initUI(self):
        self.setStyleSheet("QGroupBox {  border: 5px solid gray;} QGroupBox::title {padding: -145 0 0 0;}")
        self.setTitle(self.cellName)
        self.setFont(QFont("Times", 22, QFont.Bold))
        self.setCheckable(False)
        self.setMaximumHeight(self.GROUP_BOX_HEIGHT)
        self.setMinimumWidth(self.GROUP_BOX_WIDTH)
        self.setAlignment(Qt.AlignCenter | Qt.AlignTop)
        
        self.cellButton = PicButton(QPixmap("runButton.png"),QPixmap("stopButton.png"), QPixmap("disabledRunButton.png"))
        self.cellButton.clicked.connect(self.runCell)

        self.currentT = QLabel('xxxx.x')
        self.celciusT = QLabel('°C')
        
        self.currentT.setAlignment(Qt.AlignBottom)
        self.celciusT.setAlignment(Qt.AlignBottom)
        
        self.targetSP_label = QLabel('Target SP:')
        self.targetSP_value = QLabel('xx')
        self.targetSP_celcius = QLabel('°C')
        self.ramp_label = QLabel('Ramp:')
        self.ramp_value = QLabel('xx')
        self.ramp_celcius = QLabel('°C/m')
        self.power_label = QLabel('Power:')
        self.power_value = QLabel('xxx')
        self.power_percent = QLabel('%')
        self.targetSP_value.setAlignment(Qt.AlignRight | Qt.AlignVCenter)
        self.ramp_value.setAlignment(Qt.AlignRight | Qt.AlignVCenter)
        self.power_value.setAlignment(Qt.AlignRight | Qt.AlignVCenter)
#         self.targetSP_celcius.setAlignment(Qt.AlignCenter | Qt.AlignVCenter)
#         self.ramp_celcius.setAlignment(Qt.AlignCenter | Qt.AlignVCenter)
#         self.power_percent.setAlignment(Qt.AlignCenter | Qt.AlignVCenter)
        self.targetSP_value.mousePressEvent = self.changeSetpoint
        self.ramp_value.mousePressEvent = self.changeRamp
        
        
        gbMainLayout = QVBoxLayout()
         
        gbUpLayout = QHBoxLayout()
        gbDownLayout = QGridLayout()
        gbDownLayout.setColumnStretch(0, 2)
        gbDownLayout.setColumnStretch(1, 1)
        gbDownLayout.setColumnStretch(2, 0)
#         gbDownLayout.setAlignment(Qt.AlignRight | Qt.AlignVCenter)
        
        gbUpLayout.addWidget(self.cellButton)
        gbUpLayout.addStretch(1)
        gbUpLayout.addWidget(self.currentT)
        gbUpLayout.addWidget(self.celciusT)
        
        downFrame = QFrame(self)
        downFrame.setStyleSheet('QFrame {font-size: 14px;}')
        downFrame.setLayout(gbDownLayout)
        
        gbDownLayout.addWidget(self.targetSP_label, 0, 0)
        gbDownLayout.addWidget(self.targetSP_value, 0, 1)
        gbDownLayout.addWidget(self.targetSP_celcius, 0, 2)
        gbDownLayout.addWidget(self.ramp_label, 1, 0)
        gbDownLayout.addWidget(self.ramp_value, 1, 1)
        gbDownLayout.addWidget(self.ramp_celcius, 1, 2)
        gbDownLayout.addWidget(self.power_label, 2, 0)
        gbDownLayout.addWidget(self.power_value, 2, 1)
        gbDownLayout.addWidget(self.power_percent, 2, 2)
        
        gbMainLayout.addLayout(gbUpLayout)
        gbMainLayout.addWidget(downFrame)
        downFrame.setFont(QFont("Times", 12, not QFont.Bold))   
        
        self.setLayout(gbMainLayout)
        
        self.currentT.setFont(QFont("Times", 18, QFont.Bold))
        self.celciusT.setFont(QFont("Times", 16, QFont.Bold))


    def changeSetpoint(self, event):
        
        screenHeight = QDesktopWidget().screenGeometry(0).height()
        setpointDialog = QInputDialog(self)
        
        mainWindowX = self.parent.parent().parent.parent().geometry().x()
        mainWindowY = self.parent.parent().parent.parent().geometry().y()
        cellGBX = self.x()
        cellGBY = self.y()
        cellGBHeight = self.height()
        totalCoordY = mainWindowY+cellGBY+cellGBHeight
        if not totalCoordY>=screenHeight-cellGBHeight:
            setpointDialog.move(mainWindowX+cellGBX,totalCoordY)
        else:
            setpointDialog.move(mainWindowX+cellGBX,totalCoordY-cellGBHeight)        
        
        currentSP = self.targetSP_value.text()
        setpointDialog.setInputMode(QInputDialog.IntInput)
        setpointDialog.setIntRange(0, 2000)
        setpointDialog.setIntStep(1)
        try:
            setpointDialog.setIntValue(int(currentSP))
        except:
            setpointDialog.setIntValue(0)
        setpointDialog.setWindowTitle(self.title()+ ' - Target SP')
        setpointDialog.setLabelText('Temperature [°C]\nRange 0-2000')
        setpointDialog.setStyleSheet('''
            QLabel {
            font-size:  12px;
            font: Times;
            }
            QSpinBox  {
            font-size:  20px;
            font: Times;
            }
        ''')
#         setpointDialog.setFont(QFont("Times", 18, QFont.Bold))
        okPressed = setpointDialog.exec_()
        setpoint = setpointDialog.intValue()
        if okPressed:
            self.targetSP_value.setText(str(setpoint))
            
    def changeRamp(self, event):
        
        screenHeight = QDesktopWidget().screenGeometry(0).height()
        setpointDialog = QInputDialog(self)
        
        mainWindowX = self.parent.parent().parent.parent().geometry().x()
        mainWindowY = self.parent.parent().parent.parent().geometry().y()
        cellGBX = self.x()
        cellGBY = self.y()
        cellGBHeight = self.height()
        totalCoordY = mainWindowY+cellGBY+cellGBHeight
        if not totalCoordY>=screenHeight-cellGBHeight:
            setpointDialog.move(mainWindowX+cellGBX,totalCoordY)
        else:
            setpointDialog.move(mainWindowX+cellGBX,totalCoordY-cellGBHeight)   
        
        currentRamp = self.ramp_value.text()
        
        setpointDialog.setInputMode(QInputDialog.IntInput)
        setpointDialog.setIntRange(0, 100)
        setpointDialog.setIntStep(1)
        try:
            setpointDialog.setIntValue(int(currentRamp))
        except:
            setpointDialog.setIntValue(0)
        setpointDialog.setWindowTitle(self.title()+ ' - Ramp')
        setpointDialog.setLabelText('Temperature [°C/m]\nRange 0-100')
        setpointDialog.setStyleSheet('''
            QLabel {
            font-size:  12px;
            font: Times;
            }
            QSpinBox  {
            font-size:  20px;
            font: Times;
            }
        ''')
        okPressed = setpointDialog.exec_()
        ramp = setpointDialog.intValue()
        if okPressed:
            self.ramp_value.setText(str(ramp))
            
        
            
    def runCell(self, event):
        if self.cellButton.isChecked():
            if self.targetSP_value.text() =='xx' or self.ramp_value.text() =='xx':
                time.sleep(0.2)
                self.parent.parent().dataConsole.consoleEdit.append('Set proper numeric setpoint and/or ramp value.')
                self.cellButton.setChecked(False)
                return
            self.currentSP = int(self.targetSP_value.text())
            temperatureSet, rampSet = setCellParameters(self.currentSP, int(self.ramp_value.text()), '0', self.cellID)
            
            cellError = ''
            if (not temperatureSet and not rampSet):
                cellError += 'ERROR %s: not connected.' %(self.cellName)
            elif not temperatureSet:
                cellError += 'ERROR %s: Temperature could not be set.' %(self.cellName)
                self.ramp_value.setText(str(self.ramp_value.text()))
                self.cellButton.setChecked(False)
            elif not rampSet:
                cellError += 'ERROR %s: Ramp could not be set.' %(self.cellName)
                self.targetSP_value.setText(str(self.currentSP))
                self.cellButton.setChecked(True)
            if  len(cellError)>0:
                self.parent.parent().dataConsole.consoleEdit.append(cellError)
                self.cellRunning = self.cellButton.isChecked()
                return
            else:
                self.targetSP_value.setText(str(self.currentSP))
                self.ramp_value.setText(str(self.ramp_value.text()))
                self.cellButton.setChecked(True)
                cellSuccess = '%s: temperature and ramp set.' %(self.cellName)
                self.parent.parent().dataConsole.consoleEdit.append(cellSuccess)
        else:
            temperatureSet, rampSet = setCellParameters(self.currentTemp, int(self.ramp_value.text()), '0', self.cellID)
            cellError = ''
            if (not temperatureSet and not rampSet):
                cellError += 'ERROR %s: not connected.' %(self.cellName)
            elif not temperatureSet:
                cellError += 'ERROR %s: Temperature could not be set.' %(self.cellName)
                self.ramp_value.setText(str(self.ramp_value.text()))
                self.cellButton.setChecked(False)
            elif not rampSet:
                cellError += 'ERROR %s: Ramp could not be set.' %(self.cellName)
                self.targetSP_value.setText(str(self.currentSP))
                self.cellButton.setChecked(True)
            if  len(cellError)>0:
                self.parent.parent().dataConsole.consoleEdit.append(cellError)
                self.cellRunning = self.cellButton.isChecked()
                return
            else:
                self.targetSP_value.setText(str(self.currentTemp))
                self.ramp_value.setText(str(self.ramp_value.text()))
                self.cellButton.setChecked(False)
                cellSuccess = '%s: Stopped.' %(self.cellName)
                self.parent.parent().dataConsole.consoleEdit.append(cellSuccess)
            
        self.cellRunning = self.cellButton.isChecked()
        
    
class ScriptTabs(QWidget):
    
    def __init__(self, parent):
        super(QWidget, self).__init__(parent)
        self.layout = QVBoxLayout(self)
        
        self.tabs = QTabWidget()
        self.tabs.setTabsClosable(False)
        self.tabs.setMovable(True)
        self.tabs.tabCloseRequested.connect(self.closeTab)
        self.tabs.resize(300,200)

        self.layout.addWidget(self.tabs)
        self.setLayout(self.layout)
        
    def closeTab(self, index):
        tab = self.tabs.widget(index)
        tab.deleteLater()
        self.tabs.removeTab(index)
        if self.tabs.count()<2:
            self.tabs.setTabsClosable(False)
        else:
            self.tabs.setTabsClosable(True)
    def addNewScriptTab(self):
        self.newTab = QWidget()
        self.tabs.addTab(self.newTab,"No Name*")
        self.newTab.layout = QVBoxLayout(self)
        self.newTab.scriptSaved = False
        self.newTab.scriptLine = QPlainTextEdit(self.newTab)
        self.newTab.scriptLine.textChanged.connect(self.changeText)
        self.newTab.scriptLine.setTabStopDistance(QFontMetricsF(self.newTab.scriptLine.font()).width(' ') * 4)
        self.newTab.layout.addWidget(self.newTab.scriptLine)
        self.newTab.setLayout(self.newTab.layout)
        if self.tabs.count()<2:
            self.tabs.setTabsClosable(False)
        else:
            self.tabs.setTabsClosable(True)
        self.tabs.setCurrentWidget(self.newTab)
        return self.newTab
    
    def changeText(self):
        self.tabs.currentWidget().scriptSaved = False
        tabIndex = self.tabs.currentIndex()
        tabName = self.tabs.tabText(tabIndex)
        if tabName[-1] != '*':
            self.tabs.setTabText(tabIndex, tabName + '*')
            
class ScriptThread(QThread):
    
    sig_result = pyqtSignal(str)      

    def __init__(self, parent, *args, **kwargs):
        QThread.__init__(self, *args, **kwargs)
        
        self.parent=parent
        self.scriptRunning = False
#     def divideScript(self):
#         scriptText=self.parent.table_widget.tabs.currentWidget().scriptLine.toPlainText()
#         lineCount = self.parent.table_widget.tabs.currentWidget().scriptLine.blockCount()
#         scriptTextLines = scriptText.split('\n')
#         scriptTextOrdered = []
#         for line, lineNumber in zip(scriptTextLines, range(lineCount)):
#             if 'for' in line:
#                 loopLine = line
#                 for subLine in scriptTextLines[lineNumber:]:
#                     if '\t' in subLine:
#                         loopLine += '\n'
#                         loopLine += subLine
#                 scriptTextOrdered.append(loopLine)
#             elif '\t' in line:
#                 pass
#             else:
#                 scriptTextOrdered.append(line)  
#         return scriptTextOrdered
        
       
    def run(self):
        self.scriptRunning = True   
        first = self.parent.firstCell
        second = self.parent.secondCell
        third = self.parent.thirdCell
        fourth = self.parent.fourthCell
        fifth = self.parent.fifthCell
        sixth = self.parent.sixthCell
              
        glob = {'__builtins__': None}
        loc = {'setTemp': self.parent.setTemp, 'sleep': time.sleep, 'len': len, 
               'print': self.parent.printText, 'range': range,
               first.cellName: first, second.cellName: second, third.cellName: third,
               fourth.cellName: fourth, fifth.cellName: fifth, sixth.cellName: sixth}
        
        scriptText=self.parent.table_widget.tabs.currentWidget().scriptLine.toPlainText()
        try:
            eval(compile(scriptText, '<string>', 'exec'), glob, loc)
        except TypeError as te:
#             self.sig_result.emit(str(te))
            self.sig_result.emit('Unknown function/variable name used.')
        except NameError as ne:
            self.sig_result.emit(str(ne))
        except Exception as e:
            self.sig_result.emit(str(e))
        else:
            self.sig_result.emit('Success')
        finally:          
            loop = QEventLoop()
            loop.exec_()
            
    def stop(self):
        self.scriptRunning = False
        if self.parent.commandRunning:
            print('nope')
            time.sleep(0.1)
        self.terminate()
#         self.quit()
        self.wait()
        

class DataCaptureThread(QThread):
    
    sig_result = pyqtSignal(str, str)
    
    def collectData(self):
        cellTemperature, cellWSP = getTemp('0', '4')
        self.sig_result.emit(cellTemperature, cellWSP)
        
#     def setCellsInitialState(self):
#         allCells = [self.parent.firstCell, self.parent.secondCell, self.parent.thirdCell, 
#                     self.parent.fourthCell, self.parent.fifthCell, self.parent.sixthCell]
#         cellsInitialState = initCommunication()
#         print(cellsInitialState)
#         cellIndex=0
#         for singleCell in allCells:
#             singleCell.currentT.setText(cellsInitialState[cellIndex])
#             if cellsInitialState[cellIndex] != 'NC':
#                 singleCell.CELL_CONNECTED = True
#             cellIndex+=1
#             singleCell.setEnabled(singleCell.CELL_CONNECTED)

    def __init__(self, parent,  *args, **kwargs):
        QThread.__init__(self, *args, **kwargs)
        
        self.parent=parent
        
        self.dataCollectionTimer = QTimer()
        self.dataCollectionTimer.moveToThread(self)
        self.dataCollectionTimer.timeout.connect(self.collectData)

    def run(self):
        self.dataCollectionTimer.start(1000)
        loop = QEventLoop()
        loop.exec_()
        
    def stop(self):
        self.quit()
        self.wait()

class ET_help(QWidget):
    def __init__(self):
        super(ET_help, self).__init__()
        
        self.HELP_WIDTH = 300
        
        self.setFixedSize(self.HELP_WIDTH, 300)
        
        self.initUI()
        
    def initUI(self):
        
        self.helpLayout = QHBoxLayout(self)
        self.helpLayout.setAlignment(Qt.AlignLeft)
        
        commandText = '''
        * - optional argument
        To set cell temperature: 
            SetTemp(temp, ramp*, cell name, cell name, ...)
        To wait: 
            sleep(seconds)
        for loop: 
            "for index in range(a, b):
                do sth
                do sth else
            not in loop"
        
        '''
        
        commandHelp = QLabel(commandText, self)
        commandHelp.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Expanding)
        commandHelp.setAlignment(Qt.AlignVCenter)
        commandHelp.setFixedWidth(self.HELP_WIDTH-10)
        commandHelp.setWordWrap(True)
        
        self.helpLayout.addWidget(commandHelp)
        
        self.setLayout(self.helpLayout)
        
        self.setWindowTitle('Help - commands')
        
        self.show()


class DataConsole(QWidget):
    def __init__(self, parent):
        super(DataConsole, self).__init__()
#         self.setMaximumWidth(100)

        
        self.initUI()
        self.parent = parent
        self.parentWidth = self.parent.width()
        self.setMinimumWidth(self.parentWidth)
        
    def initUI(self):
        self.dataConsoleLayout = QVBoxLayout(self)
        self.mainFrame = QFrame(self)
        
        self.consoleTitle = QLabel('Console', self)
        self.consoleTitle.setFont(QFont("Times", 10, QFont.Bold))
        self.consoleEdit = QTextEdit()
        self.consoleEdit.setAlignment(Qt.AlignTop)
        self.consoleEdit.setReadOnly(True)
#         self.consoleEdit.setWordWrap(True)
        self.consoleEdit.setMinimumHeight(100)
        self.consoleEdit.setStyleSheet("""
        QLabel {
            background-color: rgb(255,255,255);
            padding: 3px;
            border-style: solid;
            border-width: 5px;
            border-color: rgb(224,224,224);
        }
        """)
        self.scrolledLabel = QScrollArea()
        self.scrolledLabel.setWidget(self.consoleEdit)
        self.scrolledLabel.setWidgetResizable(True)
        self.scrolledLabel.horizontalScrollBar().setEnabled(False);
        self.scrolledLabel.setHorizontalScrollBarPolicy(Qt.ScrollBarAlwaysOff)
        self.consoleEdit.setVerticalScrollBarPolicy(Qt.ScrollBarAlwaysOn)
        self.consoleEdit.moveCursor(QTextCursor.End)
        self.consoleEdit.ensureCursorVisible()
        
        self.dataConsoleLayout.addWidget(self.consoleTitle)
        self.dataConsoleLayout.addWidget(self.scrolledLabel)
        
        self.setLayout(self.dataConsoleLayout)
        
        self.consoleEdit.verticalScrollBar().rangeChanged.connect(self.ResizeScroll)
        
        
    def addText(self, textToAdd):
        consoleCurrentText = self.consoleEdit.toPlainText()
        newConsoleText = consoleCurrentText +'\n'+textToAdd

        self.consoleEdit.setPlainText(newConsoleText)
        
    def ResizeScroll(self, min, maxi):
        self.consoleEdit.verticalScrollBar().setValue(maxi)
#         self.consoleEdit.scrollToAnchor()
#         self.consoleEdit.moveCursor(QTextCursor.End)
#         self.consoleEdit.ensureCursorVisible()

class ET_main(QWidget):
    
    def __init__(self, parent):
        super(ET_main, self).__init__(parent)
#         self.setFixedSize(760, 600)
        
        self.initUI()
        self.dataCollectionRunning = False
        self.commandRunning = False
        self.parent=parent
        
    def initUI(self):
        
        mainLayout = QHBoxLayout(self)
        # change names for actual materials
        self.leftFrame = QFrame(self)
        self.leftFrame.setFixedWidth(450)
        self.leftLayout = QGridLayout(self.leftFrame)
        self.firstCell = CellGB(self.leftFrame, 'fst', '1')
        self.secondCell = CellGB(self.leftFrame, 'scnd', '2')
        self.thirdCell = CellGB(self.leftFrame, 'thrd', '3')
        self.fourthCell = CellGB(self.leftFrame, 'frth', '4')
        self.fifthCell = CellGB(self.leftFrame, 'fith', '5')
        self.sixthCell = CellGB(self.leftFrame, 'sxth', '6')
        
        self.firstCell.setEnabled(False)
        self.secondCell.setEnabled(False)
        self.thirdCell.setEnabled(False)
        self.fourthCell.setEnabled(False)
        self.fifthCell.setEnabled(False)
        self.sixthCell.setEnabled(False)

#         self.scriptLine = QPlainTextEdit(self.leftFrame)
#         self.scriptLine.setTabStopDistance(QFontMetricsF(self.scriptLine.font()).width(' ') * 4)
        
        
        
        self.leftLayout.addWidget(self.firstCell, 0, 0)
        self.leftLayout.addWidget(self.secondCell, 0, 1)
        self.leftLayout.addWidget(self.thirdCell, 1, 0)
        self.leftLayout.addWidget(self.fourthCell, 1, 1)
        self.leftLayout.addWidget(self.fifthCell, 2, 0)
        self.leftLayout.addWidget(self.sixthCell, 2, 1)
        
        self.rightFrame = QFrame(self)
        self.rightLayout = QVBoxLayout(self.rightFrame)
        
        self.scriptButton = QPushButton('Run Script', self.rightFrame)
        self.scriptButton.clicked.connect(self.runButtonClicked)
        self.endScriptButton = QPushButton('Terminate Script', self.rightFrame)
        self.endScriptButton.clicked.connect(self.terminateScript)
        self.dataConsole = DataConsole(self.rightFrame)
#         self.dataConsole = QLabel('jakiś długi tekst SDfasdadsfasdfsdaf')
#         self.dataConsole.setMinimumHeight(100)
#         self.dataConsole.setStyleSheet("""
#         QLabel {
#             background-color: rgb(255,255,255);
#             border-style: inset;
#             border: 1px solid #000;
#         }
#         """)
        
#         self.rightLayout.addWidget(self.scriptLine)
        self.scriptsTitle = QLabel('Scripts', self)
        self.scriptsTitle.setFont(QFont("Times", 10, QFont.Bold))
        
        self.table_widget = ScriptTabs(self.rightFrame)
        self.table_widget.addNewScriptTab()
        
        self.rightMenuBar = QMenuBar(self.rightFrame)
        self.rightMenuBar.setStyleSheet("""
        QMenuBar {
            width: 100px;
            background-color: rgb(224,224,224);

        }

        QMenuBar::item {
            background-color: rgb(192,192,192);
            border-style: inset;
            border: 1px solid #000;
        }

        QMenuBar::item::selected {
            background-color: rgb(128,128,128);
        }

        QMenu {
            background-color: rgb(192,192,192);
            border: 1px solid #000;           
        }

        QMenu::item::selected {
            background-color: rgb(128,128,128);
        }
        """)
#         mainMenu = self.menuBar()
        self.fileMenu = self.rightMenuBar.addMenu('&File')
        self.helpMenu = self.rightMenuBar.addMenu('&Help')
        
        newScriptAction = QAction('New', self.rightFrame)
        saveScriptAction = QAction('Save', self.rightFrame)
        saveScriptAsAction = QAction('Save as...', self.rightFrame)
        openScriptAction = QAction('Open script', self.rightFrame)
        commandsWindowAction = QAction('Commands', self.rightFrame)
        
        newScriptAction.setShortcut("Ctrl+N")
        saveScriptAction.setShortcut("Ctrl+S")
        openScriptAction.setShortcut("Ctrl+O")
        commandsWindowAction.setShortcut("Ctrl+H")
        
        self.fileMenu.addAction(newScriptAction)
        self.fileMenu.addSeparator()
        self.fileMenu.addAction(saveScriptAction)
        self.fileMenu.addAction(saveScriptAsAction)
        self.fileMenu.addSeparator()
        self.fileMenu.addAction(openScriptAction)
        
        self.helpMenu.addAction(commandsWindowAction)
        
        newScriptAction.triggered.connect(self.addNewTab)
        saveScriptAction.triggered.connect(self.saveScript)
        saveScriptAsAction.triggered.connect(self.saveScriptAs)
        openScriptAction.triggered.connect(self.openScript)
        commandsWindowAction.triggered.connect(self.commandsWindow)
        
        self.rightLayout.addWidget(self.scriptsTitle)
        self.rightLayout.addWidget(self.rightMenuBar)    
        self.rightLayout.addWidget(self.table_widget)
        self.rightLayout.addWidget(self.dataConsole)
        self.rightLayout.addWidget(self.scriptButton)
        self.rightLayout.addWidget(self.endScriptButton)
        
        
        mainLayout.addWidget(self.leftFrame)
        mainLayout.addWidget(self.rightFrame)
          
        self.setLayout(mainLayout) 
        
        self.endScriptButton.setEnabled(False)
        
        self.show()
        
    def startDataCollection(self, event):
        if not self.parent.parent().ET_CONNECTED:
            return
        self.dataCollectionRunning = True
        self.dataCollectionThread = DataCaptureThread(self)
        self.dataCollectionThread.sig_result.connect(self.passCellTemp)
        self.dataCollectionThread.start()
        
    def passCellTemp(self, cellTemp, cellWSP):      
        self.cellTemp = cellTemp
        try:
            self.fourthCell.currentTemp = int(cellTemp)
        except:
            pass
        self.fourthCell.currentT.setText(cellTemp)
        if cellWSP == 'er':
            self.fourthCell.cellRunning = False
            self.fourthCell.cellButton.setChecked(False)
        elif int(cellWSP) == self.fourthCell.currentSP:
            self.fourthCell.cellRunning = False
            self.fourthCell.cellButton.setChecked(False)
        
    def runButtonClicked(self, event):
        activeTabText = self.table_widget.tabs.currentWidget().scriptLine.toPlainText()
        if len(activeTabText)<1:
            return
        self.endScriptButton.setEnabled(True)
        self.dataConsole.consoleEdit.setPlainText('')
        self.scriptThread = ScriptThread(self)
        self.scriptThread.sig_result.connect(self.showScritpFinishedMessage)
        self.scriptThread.start()
        self.scriptButton.setEnabled(False)

    def addNewTab(self, event):
        self.table_widget.addNewScriptTab()
        
    def terminateScript(self, event):
        if self.scriptThread.scriptRunning:
            self.scriptThread.stop()
            self.dataConsole.consoleEdit.append('Script terminated.')
            self.endScriptButton.setEnabled(False)
            self.scriptButton.setEnabled(True)
        else:
            return
        
    def setCellsInitialState(self):
        cellsInitialState = initCommunication()
        self.firstCell.currentT.setText(cellsInitialState[0])
        self.secondCell.currentT.setText(cellsInitialState[1])
        self.thirdCell.currentT.setText(cellsInitialState[2])
        self.fourthCell.currentT.setText(cellsInitialState[3])
        self.fifthCell.currentT.setText(cellsInitialState[4])
        self.sixthCell.currentT.setText(cellsInitialState[5]) 
        
    def showScritpFinishedMessage(self, scriptMessage):
        self.scriptButton.setEnabled(True)
        self.endScriptButton.setEnabled(False)
        if scriptMessage == 'Success':
            self.dataConsole.consoleEdit.append('--------\nScript finished\n--------')
        else:
            self.dataConsole.consoleEdit.append('\n'+'ERROR: '+scriptMessage)

            msg = QMessageBox()
            msg.setIcon(QMessageBox.Warning)
            msg.setText(scriptMessage)
            msg.setWindowTitle("Script error!")
            msg.setStandardButtons(QMessageBox.Ok)
            msg.exec_()

    def saveScript(self, event):
        if self.table_widget.tabs.currentWidget().scriptSaved:
            print(self.table_widget.tabs.currentIndex())
            return
        tabIndex = self.table_widget.tabs.currentIndex()
        tabName = self.table_widget.tabs.tabText(tabIndex)[:-1]
        saveFolder = './'
        if not os.path.exists(saveFolder+tabName+'.txt'):
            scriptFileName, scriptExtension = QFileDialog.getSaveFileName(self, 'Save script', saveFolder + tabName, filter='*.txt')
        else:
            scriptFileName = saveFolder+tabName+'.txt'
        if scriptFileName:
            with open(scriptFileName, 'w') as f: 
                text = self.table_widget.tabs.currentWidget().scriptLine.toPlainText()
                f.write(text)
            newTabName = os.path.splitext(os.path.basename(scriptFileName))[0]
            self.table_widget.tabs.currentWidget().scriptSaved = True
            self.table_widget.tabs.setTabText(tabIndex, newTabName)
            
    def saveScriptAs(self, event):
        saveFolder = './'
        tabIndex = self.table_widget.tabs.currentIndex()
        tabName = self.table_widget.tabs.tabText(tabIndex)[:-1]
        scriptFileName, scriptExtension = QFileDialog.getSaveFileName(self, 'Save script', saveFolder + tabName, filter='*.txt')
        if scriptFileName:
            with open(scriptFileName, 'w') as f: 
                text = self.table_widget.tabs.currentWidget().scriptLine.toPlainText()
                f.write(text)
            newTabName = os.path.splitext(os.path.basename(scriptFileName))[0]
            self.table_widget.tabs.currentWidget().scriptSaved = True
            self.table_widget.tabs.setTabText(tabIndex, newTabName)
    
    def openScript(self, event):
        saveFolder = './'
        scriptFileName, scriptExtension = QFileDialog.getOpenFileName(self, saveFolder ,filter='*.txt')
        if scriptFileName:
            newTabName = os.path.splitext(os.path.basename(scriptFileName))[0]
            allTabs = self.table_widget.tabs.count()
            for tab in range(0, allTabs):
                if self.table_widget.tabs.tabText(tab) == newTabName:
                    self.table_widget.tabs.setCurrentIndex(tab)  
                    return
            newTab = self.table_widget.addNewScriptTab()
            self.table_widget.tabs.setCurrentWidget(newTab)

            tabIndex = self.table_widget.tabs.currentIndex()

            with open(scriptFileName) as f:  
                scriptText = f.read() 
                 
                self.table_widget.tabs.currentWidget().scriptLine.insertPlainText(scriptText)       
                self.table_widget.tabs.setTabText(tabIndex, newTabName)
                
    def commandsWindow(self, event):
        self.helpWindow = ET_help()
        
    def setTemp(self, temperature, *args):
        self.commandRunning = True
        cellsIndicesStart = 0
        ramp=-1

        if isinstance(args[0], int):
            cellsIndicesStart = 1
            ramp = args[0]
            if (ramp<0 or ramp >100):
                raise ValueError('Wrong ramp. Choose in 0-100 °C/m range.')
                return
    
        if temperature<0 or temperature>2000:
            raise ValueError('Wrong temperature. Choose in 0-2000 °C range.')
            return
        
        for arg in args[cellsIndicesStart:]:
            if not arg.CELL_CONNECTED:
                cellError = 'ERROR %s: not connected. Skipping.' %(arg.cellName)
                self.dataConsole.consoleEdit.append(cellError)
                continue
            if ramp ==-1: 
                ramp = arg.ramp_value.text()
                if ramp == 'xx': ramp = 1
            temperatureSet, rampSet = setCellParameters(int(temperature), int(ramp), '0', arg.cellID)
            cellError = ''
            if (not temperatureSet and not rampSet):
                cellError += 'ERROR %s: not connected.' %(arg.cellName)
            elif not temperatureSet:
                cellError += 'ERROR %s: Temperature could not be set.' %(arg.cellName)
                arg.ramp_value.setText(str(ramp))
            elif not rampSet:
                cellError += 'ERROR %s: Ramp could not be set.' %(arg.cellName)
                arg.targetSP_value.setText(str(temperature))
                arg.cellButton.setChecked(True)
            if  len(cellError)>0:
                self.dataConsole.consoleEdit.append(cellError)
                arg.currentSP = int(arg.targetSP_value.text())
                pass
            else:
                arg.targetSP_value.setText(str(temperature))
                arg.ramp_value.setText(str(ramp))
                arg.cellButton.setChecked(True)
                arg.currentSP = int(arg.targetSP_value.text())
                cellSuccess = '%s: temperature and ramp set.' %(arg.cellName)
                self.dataConsole.consoleEdit.append(cellSuccess)
        self.commandRunning = False
                
    def printText(self, *textToPrint):
        fullText=''
        for text in textToPrint:
            fullText += str(text)
        self.dataConsole.consoleEdit.append(fullText)


class MainWindow(QMainWindow):
    def __init__(self, parent=None):
        super(MainWindow, self).__init__(parent)
        self.setFixedSize(800, 620)
        self.initUI()
        
        self.ET_CONNECTED = False
        
    def initUI(self):
        self.mainFrame = QFrame(self)
        self.dummyFrame = QFrame()
        self.mainLayout = QVBoxLayout(self)
        
        self.startTemperatureTab()
        self.mainMenuBar = self.menuBar()
        self.mainMenuBar.setStyleSheet("""
        QMenuBar {
            width: 100px;
            background-color: rgb(224,224,224);
            font-size: 15px;
        }
 
        QMenuBar::item {
            background-color: rgb(192,192,192);
            border-style: inset;
            border: 1px solid #000;
        }
 
        QMenuBar::item::selected {
            background-color: rgb(128,128,128);
        }
 
        QMenu {
            background-color: rgb(192,192,192);
            border: 1px solid #000;           
        }
 
        QMenu::item::selected {
            background-color: rgb(128,128,128);
        }
        """)
        self.fileMenu = self.mainMenuBar.addMenu('&File')
        self.optionsMenu = self.mainMenuBar.addMenu('&Options')
        
        newScriptAction = QAction('New', self)
        saveScriptAction = QAction('Save', self)
        saveScriptAsAction = QAction('Save as...', self)
        openScriptAction = QAction('Open script', self)
        dataCaptureAction = QAction('Start data capture', self)
        self.connectEuroThermsAction = QAction('Connect Eurotherms', self)
        disconnectEuroThermsAction = QAction('Disconnect Eurotherms', self)
        
        self.fileMenu.addAction(newScriptAction)
        self.fileMenu.addSeparator()
        self.fileMenu.addAction(saveScriptAction)
        self.fileMenu.addAction(saveScriptAsAction)
        self.fileMenu.addSeparator()
        self.fileMenu.addAction(openScriptAction)
        
        self.optionsMenu.addAction(dataCaptureAction)
        self.optionsMenu.addSeparator()
        self.optionsMenu.addAction(self.connectEuroThermsAction)
        self.optionsMenu.addAction(disconnectEuroThermsAction)
        
        dataCaptureAction.triggered.connect(self.TemperatureTab.startDataCollection)
        self.connectEuroThermsAction.triggered.connect(self.connectEuroTherms)
        disconnectEuroThermsAction.triggered.connect(self.disconnectEuroTherms)
        
        self.mainLayout.addWidget(self.mainMenuBar)
        self.mainLayout.addWidget(self.mainFrame)
        
        self.setLayout(self.mainLayout)

    def connectEuroTherms(self, event):
        self.connectEuroThermsAction.setEnabled(False)
        self.chooseCOM = PopUpCOM(self)
        
    def disconnectEuroTherms(self, event):
        allCells = [self.TemperatureTab.firstCell, self.TemperatureTab.secondCell, self.TemperatureTab.thirdCell, 
                    self.TemperatureTab.fourthCell, self.TemperatureTab.fifthCell, self.TemperatureTab.sixthCell]
        
        if self.ET_CONNECTED:
            if self.TemperatureTab.dataCollectionRunning:
                self.TemperatureTab.dataCollectionThread.stop()
                self.TemperatureTab.dataCollectionRunning = False
            disconnectET()
            for singleCell in allCells:
                singleCell.currentT.setText('NC')
                if singleCell.CELL_CONNECTED:
                    self.TemperatureTab.dataConsole.consoleEdit.append('Disconnected: '+singleCell.cellName)
                singleCell.CELL_CONNECTED = False
                singleCell.setEnabled(singleCell.CELL_CONNECTED)
            
        self.ET_CONNECTED = False

    def startTemperatureTab(self):
        self.TemperatureTab = ET_main(self.mainFrame)
        self.setWindowTitle('EPI - Temperature')
        self.setCentralWidget(self.TemperatureTab)
        self.show()

#     def startUIWindow(self):
#         self.Window = UIWindow(self)
#         self.setWindowTitle("UIWindow")
#         self.setCentralWidget(self.Window)
#         self.Window.ToolsBTN.clicked.connect(self.startUIToolTab)
#         self.show()
    def closeEvent(self, event):
        if self.TemperatureTab.dataCollectionRunning:
            self.TemperatureTab.dataCollectionThread.stop()
        if self.ET_CONNECTED:
            disconnectET()
        self.TemperatureTab.close()
        event.accept()
        
class PopUpCOM(QDialog):
    
    def __init__(self, parent):
        super(PopUpCOM, self).__init__(parent)
        self.setFixedSize(200,100)
        self.setWindowTitle('COM')
    
        self.parent = parent
        
        self.initUI()
        
    def initUI(self):
        
        popupLayout = QVBoxLayout(self)
        buttonLayout = QHBoxLayout(self)
        
        infoLabel = QLabel('Choose COM port.')
        self.avialableCOMS = QComboBox(self)
        self.COMOKButton = QPushButton('OK')
        self.COMCancelButton = QPushButton('Cancel')
        
        COMports = getCOMports()
        
        for COMport in COMports:
            self.avialableCOMS.addItem(COMport)
            
        self.COMOKButton.clicked.connect(self.applyCOM)
        self.COMCancelButton.clicked.connect(self.cancelCOM)
        
        popupLayout.addWidget(infoLabel)
        popupLayout.addStretch(2)
        popupLayout.addWidget(self.avialableCOMS)
        buttonLayout.addWidget(self.COMOKButton)
        buttonLayout.addWidget(self.COMCancelButton)
        popupLayout.addStretch(3)
        
        popupLayout.addLayout(buttonLayout)
        
        self.setLayout(popupLayout)
        
        self.show()
        
    def setCellsInitialState(self):
        allCells = [self.parent.TemperatureTab.firstCell, self.parent.TemperatureTab.secondCell, self.parent.TemperatureTab.thirdCell, 
                    self.parent.TemperatureTab.fourthCell, self.parent.TemperatureTab.fifthCell, self.parent.TemperatureTab.sixthCell]
        cellsInitialState = initCommunication()
        cellIndex=0
        for singleCell in allCells:
            singleCell.currentT.setText(cellsInitialState[cellIndex])
            if cellsInitialState[cellIndex] != 'NC':
                singleCell.CELL_CONNECTED = True
                self.parent.TemperatureTab.dataConsole.consoleEdit.append('Connected: '+singleCell.cellName)
                self.parent.ET_CONNECTED = True
            cellIndex+=1
            singleCell.setEnabled(singleCell.CELL_CONNECTED)
   
    def applyCOM(self, event):
        if self.parent.ET_CONNECTED:
            self.parent.disconnectEuroTherms(event)
        currentCOM = self.avialableCOMS.currentText()
        connectET(currentCOM)
        self.setCellsInitialState()
        
        if not self.parent.ET_CONNECTED:
            self.parent.TemperatureTab.dataConsole.consoleEdit.append('No avialable Eurotherms at %s.' %(currentCOM) )
            disconnectET()
        self.parent.connectEuroThermsAction.setEnabled(True)
        self.close()
        
    def closeEvent(self, event):
        self.cancelCOM(event)
        
    def cancelCOM(self, event):
        self.parent.connectEuroThermsAction.setEnabled(True)
        self.close()
            
def except_hook(cls, exception, traceback):
    sys.__excepthook__(cls, exception, traceback)  

if __name__ == '__main__':
    
    sys.excepthook = except_hook
    app = QApplication(sys.argv)
    ex = MainWindow()
    sys.exit(app.exec_())