import os
import sys
import csv
import json
import threading
from PyQt5.QtWidgets import *
from PyQt5.QtGui import *
from PyQt5.QtCore import *


## for test
import time
import random
import fitz

## add requests, PyMuPDF, pycryptodome
import requests

from Crypto.Signature import PKCS1_v1_5
from Crypto.PublicKey import RSA
from Crypto.Hash import SHA256
from base64 import b64decode, b64encode
import hashlib


class Worker(QThread):
    verify_update = pyqtSignal(int, bool)
    verify_result = pyqtSignal(object)

    def __init__(self, parent = None):
        super().__init__()
        self.main = parent
        self.working = True

    def run(self):
        # 검증 & 동작 중이면 새로 파일 실행 못하도록!
        VCList = list()
        DDoList = list()

        # DID가 없는 잘못된 문서일 경우 -> 경고창
        
        for pdf in self.pdfList:
            VCList.append(pdf[1].strip())
            DDoList.append(pdf[2].strip())

            
        self.DDoQueryResult = queryToChainCode(self.APIkey, DDoList, "ddo")['result']
        self.VCQueryResult = queryToChainCode(self.APIkey, VCList, "vc")['result']

        verifyResult = {"success" : 0, "failure" : 0}

        for row in range(len(self.pdfList)):
            result = self.verify(row)
            key = "success" if result else "failure"
            verifyResult[key] += 1
        
        self.verify_result.emit(verifyResult)

    def verify(self, row):
        result = verifySign(self.pdfList[row], self.DDoQueryResult[row]["DDo"]["publicKey"][0]["publickeyPem"], self.VCQueryResult[row]["DDo"]["proof"]["signature"])
        self.verify_update.emit(row, result)

        return result
    
    
def pdfToTxt(path):
    doc = fitz.open(path)
    return list(filter(lambda x: x != " " and x, doc[0].getText().splitlines()))

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
        veriStart_btn.clicked.connect(self.veriStart)
        
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

        # Set Progress Bar
        self.pbar = QProgressBar(self)
        self.pbar.setGeometry(20, 600, 600, 20)
        self.pbar.setValue(0)

        # Add Pbar in Layout
        PbarLayout = QVBoxLayout()
        PbarLayout.addWidget(self.pbar)

        # Set Grid Layout
        # Add Widget to Grid Layout
        ControlGrid = QGridLayout()
        ControlGrid.addWidget(upload_btn,       1, 0)
        ControlGrid.addWidget(saveCSV_btn,      1, 1)
        ControlGrid.addWidget(self.APIkeyInput, 2, 0)
        ControlGrid.addWidget(veriStart_btn,    2, 1)
        
        # Add layout to main Frame
        self.windowLayout.addLayout(VeriLayout ) # VeriLayout View
        self.windowLayout.addLayout(PbarLayout ) # PbarLayout View
        self.windowLayout.addLayout(ControlGrid) # ControlGrid View

        self.th = Worker()
        self.th.verify_update.connect(self.paint)
        self.th.verify_result.connect(self.showResult)

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
        self.pbar.setFormat("검증 중...")
        print(self.APIkeyInput.text()) # API KEY
  
        # Check Row number of data
        if self.tableWidget.rowCount() == 0:
            return
        
        # certification API-Key
        if len(self.APIkeyInput.text().strip()) == 0 :
            return

        self.th.APIkey = self.APIkeyInput.text().strip()

        t1 = threading.Thread(target = self.th.run)
        t1.daemon = True
        t1.start()

    def paint(self, row, result):
        for col in range(self.ColNum):
            self.tableWidget.repaint()
            self.tableWidget.update()

        self.tableWidget.item(row, col).setText(str("진실" if result else "거짓"))
        self.pbar.setValue((row + 1) / self.numOfDocs * 100)
    
    def showResult(self, verifyResult):
        buttonReply = QMessageBox.information(self, "검증 결과", "진실: {success}, 거짓: {failure}\n".format(success = verifyResult["success"], failure = verifyResult["failure"]), QMessageBox.Yes)
        self.pbar.setValue(0)
        self.pbar.setFormat("검증 완료")

    def upload_files(self): # pdf 검증 추가
        self.pbar.setFormat("파일 업로딩...")

        self.openFileNamesDialog()
        
        if len(self.fileList) == 0:
            return
        
        self.numOfDocs = len(self.fileList)
        self.tableWidget.setRowCount(len(self.fileList))
        self.tableWidget.setColumnCount(self.ColNum)
        
        self.tableWidget.clear() ## reset tableWidget
        self.tableWidget.setHorizontalHeaderLabels(["파일 이름", "검증 결과"])
        self.tableWidget.setSortingEnabled(False)

        self.dataset = [[x, "-"] for x in self.fileList]

        self.th.pdfList = list()

        for row in range(self.numOfDocs):
            for col in range(self.ColNum):
                item = QTableWidgetItem(str(self.dataset[row][col]))
                self.tableWidget.setItem(row, col, item)
            self.pbar.setValue((row + 1) / self.numOfDocs * 100)
            ## add pdfFile info
            pdfFile = pdfToTxt(self.fileList[row])
            self.th.pdfList.append(pdfFile)
        
        self.pbar.setValue(0)
        self.pbar.setFormat("업로딩 완료")

    def openFileNamesDialog(self):
        options  = QFileDialog.Options()
        files, _ = QFileDialog.getOpenFileNames(self,
                                                "Open Files", 
                                                "",
                                                "PDF Files (*.pdf)")
        if files:
            self.fileList = files

