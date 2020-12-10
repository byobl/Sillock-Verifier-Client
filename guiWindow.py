import os
import sys
import csv
import json
from PyQt5.QtWidgets import *
from PyQt5.QtGui import *
from PyQt5.QtCore import *

## for test
import time
import random
import fitz

## add requests, pdfminer, pycryptodome
import requests

from Crypto.Signature import PKCS1_v1_5
from Crypto.PublicKey import RSA
from Crypto.Hash import SHA256
from base64 import b64decode, b64encode
import hashlib


def pdfToTxt(path):
    doc = fitz.open(path)
    return list(filter(lambda x: x != " " and x, doc[0].getText().splitlines()))


## 검증을 서버에서 처리하는 코드도 만들 것
def queryToChainCode(APIkey, didList, queryType):
    didUrl = ""
    for did in didList:
        if didUrl: 
            didUrl += "%2C"
        didUrl += did
    headers = {"Content-Type" : "application/json; charset=utf-8", "apiKey" : APIkey}
    url = "http://bc.sillock.me:8080/user/" + queryType + "/" + didUrl + "?user=admin&domain=test.com"
    response = requests.get(url, headers=headers)
    return response.json()
    
def verifySign(data, publicKey, signature):
    allHashed = ""
    for idx in range(3, len(data) - 1):
        value = data[idx].split(":")[1].strip()
        if value.startswith("#"):
            allHashed += value[1:]
            continue
        encoded = str(value).encode("utf-8")
        _hashed = hashlib.new("sha256")
        _hashed.update(encoded)
        allHashed += _hashed.hexdigest()

    message = SHA256.new(allHashed.encode())
    message = message.hexdigest()

    ## Verify Signature
    rsakey = RSA.importKey(publicKey) 
    signer = PKCS1_v1_5.new(rsakey) 
    digest = SHA256.new(message.encode())

    if signer.verify(digest, b64decode(signature.encode())):
        return True
    return False


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
        self.width     = 720
        self.height    = 720
        
        self.fileList  = list()
        self.numOfDocs = 0
        self.ColNum    = 2

        # Pdf to Text data
        self.pdfList = list()
        
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

        # Query to ChainCode
        APIkey = self.APIkeyInput.text().strip()
        if not APIkey :
            return

        VCList = list()
        DDoList = list()

        # DID가 없는 잘못된 문서일 경우 -> 경고창
        
        for pdf in self.pdfList:
            VCList.append(pdf[1].strip())
            DDoList.append(pdf[2].strip())

        DDoQueryResult = queryToChainCode(APIkey, DDoList, "ddo")['result']
        VCQueryResult = queryToChainCode(APIkey, VCList, "vc")['result']

        # Check Row number of data
        if self.tableWidget.rowCount() == 0:
            return
        
        # certification API-Key
        if len(self.APIkeyInput.text().strip()) == 0:
            return
        
        # request Verification API & change table values
        for row in range(self.numOfDocs):
            for col in range(self.ColNum):
                #print(self.dataset[row], self.dataset[col]) # (file name, file status)
                self.tableWidget.repaint()
                self.tableWidget.update()
                time.sleep(0.5)
            # Verification function() here
            result = verifySign(self.pdfList[row], DDoQueryResult[row]["DDo"]["publicKey"][0]["publickeyPem"], VCQueryResult[row]["DDo"]["proof"]["signature"])
            
            self.tableWidget.item(row, col).setText(str("성공" if result else "실패"))
        
    def upload_files(self): # pdf 검증 추가
        self.openFileNamesDialog()
        
        if len(self.fileList) == 0:
            return
        
        self.numOfDocs = len(self.fileList)
        self.tableWidget.setRowCount(len(self.fileList))
        self.tableWidget.setColumnCount(self.ColNum)
        self.tableWidget.setHorizontalHeaderLabels(["파일 이름", "검증 결과"])
        self.tableWidget.setSortingEnabled(False)

        self.dataset = [[x, "-"] for x in self.fileList]

        self.pdfList = list()
        
        for row in range(self.numOfDocs):
            for col in range(self.ColNum):
                item = QTableWidgetItem(str(self.dataset[row][col]))
                self.tableWidget.setItem(row, col, item)
            ## add pdfFile info
            pdfFile = pdfToTxt(self.fileList[row])
            self.pdfList.append(pdfFile)

    def openFileNamesDialog(self):
        options  = QFileDialog.Options()
        files, _ = QFileDialog.getOpenFileNames(self,
                                                "QFileDialog.getOpenFileNames()", 
                                                "",
                                                "All Files (*);;Python Files (*.py)")
        if files:
            self.fileList = files

