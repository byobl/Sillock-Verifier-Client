import os
import sys
import csv
from PyQt5.QtWidgets import *
from PyQt5.QtGui import *
from PyQt5.QtCore import *

## for test
import time
import random

def restore(settings):
    finfo = QFileInfo(settings.fileName())
    if finfo.exists() and finfo.isFile():
        for w in qApp.allWidgets():
            mo = w.metaObject()
            if w.objectName() != "":
                for i in range(mo.propertyCount()):
                    name = mo.property(i).name()
                    val = settings.value("{}/{}".format(w.objectName(), name), w.property(name))
                    w.setProperty(name, val)

class App(QWidget):  
    settings = QSettings("gui.ini", QSettings.IniFormat)
    
    def __init__(self):
        super().__init__()
        self.title     = 'SILLOCK Client'
        self.left      = 100
        self.top       = 100
        self.width     = 520
        self.height    = 520
        
        self.fileList  = list()
        self.numOfDocs = 0
        self.ColNum    = 2
        
        # test dataset
        self.dataset   = list(list())
        
        self.initUI()
        
        restore(self.settings)
        
    def initUI(self):
        self.setWindowTitle(self.title)
        self.setGeometry(self.left, self.top, self.width, self.height)
        
        # API key Input text
        self.APIkeyInput = QLineEdit(self)
        self.APIkeyInput.setPlaceholderText("API-KEY here")
        
        # Upload button
        upload_btn = QPushButton("Upload", self)
        upload_btn.clicked.connect(self.upload_files)
        
        # CSV save button
        saveCSV_btn  = QPushButton("Save CSV", self)
        saveCSV_btn.clicked.connect(self.saveCSV) #
        
        # Verification Start Button
        veriStart_btn   = QPushButton("검증 시작", self)
        veriStart_btn.clicked.connect(self.veriStart) #
        
        # Verification table Widget
        self.tableWidget = QTableWidget()
        
        ## Set table Widget width
        self.tableWidget.horizontalHeader().setStretchLastSection(True) 
        self.tableWidget.horizontalHeader().setSectionResizeMode(QHeaderView.Stretch)
        self.tableWidget.setSizeAdjustPolicy(QAbstractScrollArea.AdjustToContentsOnFirstShow)
        
        # main Frame
        self.windowLayout = QVBoxLayout()
        self.windowLayout.setContentsMargins(5, 5, 5, 5)
        self.setLayout(self.windowLayout)
        
        # Verification table Layout
        VeriLayout = QVBoxLayout()
        VeriLayout.addWidget(self.tableWidget)
        
        # Set Grid Layout
        # Add Widget to Grid Layout
        ControlGrid = QGridLayout()
        ControlGrid.addWidget(upload_btn,       1, 0)
        ControlGrid.addWidget(saveCSV_btn,      1, 1)
        ControlGrid.addWidget(self.APIkeyInput, 2, 0)
        ControlGrid.addWidget(veriStart_btn,    2, 1)
        
        # Add layout to main Frame
        self.windowLayout.addLayout(VeriLayout ) # VeriLayout  View
        self.windowLayout.addLayout(ControlGrid) # ControlGrid View
        
        self.show()

    def saveCSV(self):
        print("saveToCSV")
        path = QFileDialog.getSaveFileName(self, "Save File", "", "CSV(*.csv)")
        if path[0] != "":
            with open(path[0], 'w', newline="") as csv_file:
                writer = csv.writer(csv_file, dialect='excel')
                for row in range(self.tableWidget.rowCount()):
                    row_data = list()
                    for column in range(self.tableWidget.columnCount()):
                        item = self.tableWidget.item(row, column)
                        if item is not None:
                            row_data.append(item.text())
                        else:
                            row_data.append("")
                    writer.writerow(row_data)
    
    def veriStart(self):
        print(self.APIkeyInput.text()) # API KEY
        
        # Check Row number of data
        if self.tableWidget.rowCount() == 0:
            return
        
        # certification API-Key
        if len(self.APIkeyInput.text().strip()) == 0:
            return
        
        # request Verification API & change table values
        '''
        ## test-Data Sample
        [
            [file name, 0]
            [file name, 1]
            [file name, 0]
            ...
        ]
        '''
        
        for row in range(self.numOfDocs):
            for col in range(self.ColNum):
                #print(self.dataset[row], self.dataset[col]) # (file name, file status)
                self.tableWidget.repaint()
                self.tableWidget.update()
                time.sleep(0.5)
            # Verification function() here
            self.tableWidget.item(row, col).setText(str(random.randint(0, 1)))
        
    def upload_files(self):
        self.openFileNamesDialog()
        
        if len(self.fileList) == 0:
            return
        
        self.numOfDocs = len(self.fileList)
        self.tableWidget.setRowCount(len(self.fileList))
        self.tableWidget.setColumnCount(self.ColNum)
        self.tableWidget.setHorizontalHeaderLabels(["파일 이름", "검증 결과"])
        self.tableWidget.setSortingEnabled(False)
        '''
        ## test-Data Sample
        [
            [file name, result(none) == "-"]
            [file name, result(none) == "-"]
            [file name, result(none) == "-"]
            ...
        ]
        '''
        self.dataset = [[x, "-"] for x in self.fileList]
        
        for row in range(self.numOfDocs):
            for col in range(self.ColNum):
                item = QTableWidgetItem(str(self.dataset[row][col]))
                self.tableWidget.setItem(row, col, item)

    def openFileNamesDialog(self):
        options  = QFileDialog.Options()
        files, _ = QFileDialog.getOpenFileNames(self,
                                                "QFileDialog.getOpenFileNames()", 
                                                "",
                                                "All Files (*);;Python Files (*.py)")
        if files:
            self.fileList = files