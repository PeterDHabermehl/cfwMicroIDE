#! /usr/bin/env python3
# -*- coding: utf-8 -*-
#
import sys
from TouchStyle import *
from TouchAuxiliary import *

class FtcGuiApplication(TouchApplication):
    def __init__(self, args):
        TouchApplication.__init__(self, args)
        
        #define variables for test
        code=[ "# test",
               "Output Rob 1 Set 7",
               "Delay 1000",
               "Output Rob 1 Set 0",
               "# Ampel",
               "Output TXT 1 Set 0",
               "Output TXT 2 Set 0",
               "Output TXT 3 Set 7",
               "Delay 1000",
               "Output TXT 2 Set 7",
               "Delay 1000",
               "Output TXT 1 Set 7",
               "Output TXT 2 Set 0",
               "Output TXT 3 Set 0"
             ]
        
        
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
        self.proglist.setStyleSheet("font-family: 'Monospace'; font-size: 12px;")
        
        c=1
        for a in code:
            self.proglist.addItem(("  "+str(c))[-3:]+ ": "+a)
            c=c+1
            
        l.addWidget(self.proglist)
        
        # and the controls
        
        h=QHBoxLayout()
        
        self.add = QPushButton("+")
        self.add.setStyleSheet("font-size: 20px;")
        
        self.rem = QPushButton("-")
        self.rem.setStyleSheet("font-size: 20px;")
        
        self.ins = QPushButton("I")
        self.ins.setStyleSheet("font-size: 20px;")
        
        self.upp = QPushButton("Up")
        self.upp.setStyleSheet("font-size: 20px;")
        
        self.don = QPushButton("Dn")
        self.don.setStyleSheet("font-size: 20px;")
        
        h.addWidget(self.add)
        h.addWidget(self.rem)
        h.addWidget(self.ins)
        h.addWidget(self.upp)
        h.addWidget(self.don)
        
        l.addLayout(h)
        
        self.starter = QPushButton("Start")
        self.starter.setStyleSheet("font-size: 20px;")
        
        l.addWidget(self.starter)
        
        self.centralwidget.setLayout(l)
        self.mainwindow.setCentralWidget(self.centralwidget)
        
        self.mainwindow.show()
        self.exec_()        

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
