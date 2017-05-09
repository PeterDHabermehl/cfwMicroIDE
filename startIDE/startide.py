#! /usr/bin/env python3
# -*- coding: utf-8 -*-
#
import sys
from TouchStyle import *
from TouchAuxiliary import *

class QDblPushButton(QPushButton):
    doubleClicked = pyqtSignal()
    clicked = pyqtSignal()

    def __init__(self, *args, **kwargs):
        QPushButton.__init__(self, *args, **kwargs)
        self.timer = QTimer()
        self.timer.setSingleShot(True)
        self.timer.timeout.connect(self.clicked.emit)
        super().clicked.connect(self.checkDoubleClick)

    @pyqtSlot()
    def checkDoubleClick(self):
        if self.timer.isActive():
            self.doubleClicked.emit()
            self.timer.stop()
        else:
            self.timer.start(250)

class FtcGuiApplication(TouchApplication):
    def __init__(self, args):
        TouchApplication.__init__(self, args)
        
        #define variables for test
        self.code=[ "# start",
               "# test",
               "Output Rob 1 7",
               "Delay 1000",
               "Output Rob 1 0",
               "MotorPulse Rob 1 1 2 R 10",
               "MotorEncod TXT 1 1 R 255",
               "#",
               "# Ampel",
               "#",
               "Tag gruen",
               "# grün",
               "Output TXT 1 0",
               "Output TXT 2 0",
               "Output TXT 3 512",
               "Delay 2000",
               "# grün - gelb",
               "Output TXT 2 512",
               "Delay 1000",
               "# rot",
               "Output TXT 1 512",
               "Output TXT 2 0",
               "Output TXT 3 0",
               "Delay 2000",
               "# gelb",
               "Output TXT 1 0",
               "Output TXT 2 512",
               "Output TXT 3 0",
               "Delay 1000",
               "Jump gruen"
             ]
        
        #self.code=["# head"]
        
        # would load presets here
        
        # open last project etc.
        
        # init internationalisation
        translator = QTranslator()
        path = os.path.dirname(os.path.realpath(__file__))
        translator.load(QLocale.system(), os.path.join(path, "startide_"))
        self.installTranslator(translator)

        # create the empty main window
        self.mainwindow = TouchWindow("startIDE")
        
        # and the central widget
        self.centralwidget=QWidget()
        
        #
        l=QVBoxLayout()

        
        self.proglist=QListWidget()
        self.proglist.setStyleSheet("font-family: 'Monospace'; font-size: 14px;")
        self.proglist.itemDoubleClicked.connect(self.progItemDoubleClicked)
        
        c=0
        for a in self.code:
            #self.proglist.addItem(("  "+str(c))[-3:]+ ": "+a)
            self.proglist.addItem(a)
            c=c+1
            
        l.addWidget(self.proglist)
        self.proglist.setCurrentRow(0)
        
        # and the controls
        
        h=QHBoxLayout()
        
        self.add = QPushButton("+")
        self.add.setStyleSheet("font-size: 20px;")
        self.add.clicked.connect(self.addCodeLine)
        
        self.rem = QDblPushButton("-")
        self.rem.setStyleSheet("font-size: 20px;")
        self.rem.doubleClicked.connect(self.remCodeLine)
        
        self.upp = QPushButton("\u02C4") #QCoreApplication.translate("main","Up"))
        self.upp.setStyleSheet("font-size: 20px;")
        self.upp.clicked.connect(self.lineUp)
        
        self.don = QPushButton("\u02C5")#QCoreApplication.translate("main","Dn"))
        self.don.setStyleSheet("font-size: 20px;")
        self.don.clicked.connect(self.lineDown)
        
        h.addWidget(self.add)
        h.addWidget(self.rem)
        h.addWidget(self.upp)
        h.addWidget(self.don)
        
        l.addLayout(h)
        
        self.starter = QPushButton(QCoreApplication.translate("main","Start"))
        self.starter.setStyleSheet("font-size: 20px;")
        
        l.addWidget(self.starter)
        
        self.centralwidget.setLayout(l)
        self.mainwindow.setCentralWidget(self.centralwidget)
        
        self.mainwindow.show()
        self.exec_()
    
    def addCodeLine(self):
        fta=TouchAuxMultibutton(QCoreApplication.translate("addcodeline","Add line"))
        fta.setText(QCoreApplication.translate("addcodeline","Select command type:"))
        fta.setButtons([ QCoreApplication.translate("addcodeline","Inputs"),
                         QCoreApplication.translate("addcodeline","Outputs"),
                         QCoreApplication.translate("addcodeline","Controls"),
                         QCoreApplication.translate("addcodeline","Interaction")
                        ]
                      )
        fta.setTextSize(2)
        fta.setBtnTextSize(2)
        (s,r)=fta.exec_()
        if r==QCoreApplication.translate("addcodeline","Inputs"): print("inputs")
        elif r==QCoreApplication.translate("addcodeline","Outputs"): print("outputs")
        elif r==QCoreApplication.translate("addcodeline","Controls"):print("controls")
        elif r==QCoreApplication.translate("addcodeline","Interaction"):print("interaction")
                         
    def remCodeLine(self):
        print("remCodeLine")
    def lineUp(self):
        pass
    def lineDown(self):
        pass

    def progItemDoubleClicked(self):
        print("DOBLGLIG")
        itm=self.proglist.currentItem()
        row=self.proglist.currentRow()
        cod=self.code[row]
        print(itm.text(), row, ":", "'"+cod+"'")
        
    def mkItemWidget(self, text):
        k=QHBoxLayout()
        s=""
        p=0
        for word in text.split():
            if p==0:
                l=QLabel(word)
                l.setStyleSheet("font-size: 8px;")
                k.addWidget(l)
                l=QVBoxLayout()
                p=1
            elif p==1:
                r=QLabel("<"+word+">")
                r.setStyleSheet("font-size: 15px;")
                l.addWidget(r)
                p=2
            else:
                s=s+" <"+word+">"
            r=QLabel(s)
            r.setStyleSheet("font-size: 12px;")
            l.addWidget(r)
            
        return l
        

if __name__ == "__main__":
    FtcGuiApplication(sys.argv)
