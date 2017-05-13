#! /usr/bin/env python3
# -*- coding: utf-8 -*-
#
import sys, time
import threading as thd
from TouchStyle import *
from TouchAuxiliary import *
from robointerface import *

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
            
class execThread(QThread):
    updateText=pyqtSignal(str)
    clearText=pyqtSignal()
    execThreadFinished=pyqtSignal()
    
    def __init__(self, codeList, output, starter, RIF,TXT, parent=None):
        QThread.__init__(self, parent)
        
        self.codeList=codeList
        
        self.output=output
        self.starter=starter
        
        self.RIF=RIF
        self.TXT=TXT
        
    def run(self):
                
        self.halt=False
        
        self.requireTXT=False
        self.requireRIF=False
        
        self.jmpTable=[]
        self.LoopStack=[]
        
        cnt=0
        
        # scan code for interfaces and jump tags
        for line in self.codeList:
            if "TXT" in line: self.requireTXT=True
            if "RIF" in line: self.requireRIF=True
            if "Tag" in line: 
                self.jmpTable.append([line[4:], cnt])
            cnt=cnt+1
    
        if self.requireTXT and self.TXT==None:
            self.msgOut(QCoreApplication.translate("exec","TXT not found!\nProgram terminated\n"))
            self.stop()
        if self.requireRIF and self.RIF==None:
            self.msgOut(QCoreApplication.translate("exec","RoboIF not found!\nProgram terminated\n"))
            self.stop()
        
        if not self.halt:
            self.clrOut()
            self.msgOut("<Start>")
            self.count=0
        
        while not self.halt and self.count<len(self.codeList):
            line=self.codeList[self.count]
            self.parseLine(line)
            self.count=self.count+1
        
        if not self.halt: self.msgOut("<End>")
        
        if self.RIF:
            for i in range(1,9):
                self.RIF.SetOutput(i,0)
        
        if self.TXT:
            for i in range(1,9):
                pass # shutoff txt outputs here later
        
        self.execThreadFinished.emit()
    
    def __del__(self):
    
        self.halt = True
        self.wait()

    
    def stop(self):
        self.halt=True
        
    def parseLine(self,line):
        stack=line.split()
        if stack[0]  == "#": pass
        elif stack[0]== "Stop": self.count=len(self.codeList)
        elif stack[0]== "Output": self.cmdOutput(stack)
        elif stack[0]== "Motor": self.cmdMotor(stack)
        elif stack[0]== "Delay": self.cmdDelay(stack)
        elif stack[0]== "Jump": self.cmdJump(stack)
        elif stack[0]== "LoopTo": self.cmdLoopTo(stack)
        elif stack[0]== "WaitForInputDig": self.cmdWaitForInputDig(stack)
        elif stack[0]== "IfInputDig": self.cmdIfInputDig(stack)
        elif stack[0]== "Print": self.cmdPrint(line[6:])
        
    def cmdOutput(self, stack):
        if stack[1]=="RIF":
            self.RIF.SetOutput(int(stack[2]),int(stack[3]))

    def cmdMotor(self, stack):
        if stack[1]=="RIF":
            self.RIF.SetMotor(int(stack[2]),stack[3], int(stack[4]))
            
    def cmdDelay(self, stack):
        self.sleeping=True
        self.sleeper=thd.Timer(float(stack[1])/1000, self.wake)
        self.sleeper.start()
        
        while self.sleeping and not self.halt:
            time.sleep(0.001)
        
        self.sleeper.cancel()
        if self.halt:
            self.count=len(self.codeList)
            
    def wake(self):
        self.sleeping=False
        
    def cmdJump(self,stack):
        n=-1
        for line in self.jmpTable:
            if stack[1]==line[0]: n=line[1]
        if n==-1:
            self.msgOut("Jump tag not found!")
            self.halt=True
        else:
            self.count=n
            
    def cmdLoopTo(self,stack):
        found=False
        for n in range(0,len(self.LoopStack)):
            if self.count==self.LoopStack[n][0]:
                self.LoopStack[n][1]=self.LoopStack[n][1]-1
                if self.LoopStack[n][1]>0:
                    self.count=self.LoopStack[n][2]
                else: self.LoopStack.pop(n)
                found=True
                break
        if not found:
            tgt=-1
            for line in self.jmpTable:
                if stack[1]==line[0]: tgt=line[1]
            if tgt==-1:
                self.msgOut("LoopTo tag not found!")
                self.halt=True
            else:
                self.LoopStack.append([self.count, int(stack[2])-1, tgt])
                self.count=tgt
            
    def cmdWaitForInputDig(self,stack):
        if stack[1]=="RIF":
            if stack[3]=="Raising":
                a=self.RIF.Digital(int(stack[2]))
                b=a
                while not (b<a or self.halt): 
                    b=a
                    a=self.RIF.Digital(int(stack[2]))
            elif stack[3]=="Falling":
                a=self.RIF.Digital(int(stack[2]))
                b=a
                while not (b>a or self.halt): 
                    b=a
                    a=self.RIF.Digital(int(stack[2]))
    
    def cmdIfInputDig(self,stack):
        if stack[1]=="RIF":
            if (stack[3]=="True" and self.RIF.Digital(int(stack[2]))) or (stack[3]=="False" and not self.RIF.Digital(int(stack[2]))):
                n=-1
                for line in self.jmpTable:
                    if stack[4]==line[0]: n=line[1]
                if n==-1:
                    self.msgOut("IfInputDig jump tag not found!")
                    self.halt=True
                else:
                    self.count=n

    def cmdPrint(self, message):
        self.msgOut(message)
        
    def msgOut(self,message):
        self.updateText.emit(message)
        
    def clrOut(self):
        self.clearText.emit()
    
class FtcGuiApplication(TouchApplication):
    def __init__(self, args):
        TouchApplication.__init__(self, args)
        
        # some init
        self.RIF=None
        self.TXT=None
        self.etf=False
        
        self.initIFs()
        
        #define variables for test
        
        self.code=[ "# ",
               "# Ampel",
               "# Fussgaenger rot setzen",
               "Output RIF 4 7",
               "Output RIF 5 0",
               "#",
               "Tag gruen",
               "# Fahrzeuge gruen",
               "Output RIF 1 0",
               "Output RIF 2 0",
               "Output RIF 3 7",
               "Print FZ gruen",
               "# Warten auf Fussgaengertaste",
               "Print Warte auf FG",
               "Print ...oder Ende",
               "Tag wait",
               "IfInputDig RIF 2 True ende",
               "IfInputDig RIF 1 False wait",
               "# Signal kommt",
               "Output RIF 6 7",
               "Print Signal kommt",
               "Delay 3000",
               "# Fahrzeuge gruen - gelb",
               "Output RIF 2 7",
               "Print FZ gelb-gruen",
               "Delay 2000",
               "# Fahrzeuge rot",
               "Output RIF 1 7",
               "Output RIF 2 0",
               "Output RIF 3 0",
               "Print FZ rot",
               "Delay 2000",
               "# Fussgaenger gruen",
               "Output RIF 4 0",
               "Output RIF 5 7",
               "Output RIF 6 0",
               "Print FG gruen",
               "Delay 2000",
               "Print Ende FG gruen",
               "Tag blink",
               "Output RIF 5 0",
               "Delay 250",
               "Output RIF 5 7",
               "Delay 250",
               "LoopTo blink 6",
               "# Fussgaenger wieder rot",
               "Output RIF 4 7",
               "Output RIF 5 0",
               "Print FG rot",
               "Delay 2000",
               "# Fahrzeuge gelb",
               "Output RIF 1 0",
               "Output RIF 2 7",
               "Output RIF 3 0",
               "Print FZ gelb",
               "Delay 2000",
               "# und zurueck zum Start",
               "Jump gruen",
               "# Sprungmarke Ende",
               "Tag ende"
             ]
        '''
        self.code=["# head",
                   "Print Es geht los!",
                   "Motor RIF 1 r 7",
                   "Delay 1000",
                   "Stop",
                   "Motor RIF 1 l 7",
                   "Delay 1000",
                   "Motor RIF 1 s 0"
                   ]
                   
        self.code=["# Haendetrockner",
                   "Print Pause",
                   "Delay 2000",
                   "Print Weiter",
                   "Tag top",
                   "Print La",
                   "LoopTo top 2",
                   "#",
                   "# Lichschranke an",
                   "Motor RIF 2 l 7",
                   "# Beginn Endlosschleife",
                   "Tag start",
                   "# warte auf Lichtschranke",
                   "WaitForInputDig RIF 1 Falling",
                   "# Geblaese an",
                   "Motor RIF 1 r 7",
                   "# Warte auf Lichtschranke",
                   "WaitForInputDig RIF 1 Raising",
                   "# Geblaese aus",
                   "Motor RIF 1 s 0",
                   "# und wieder zum start",
                   "Print Jump",
                   "Jump start"
                   ]

        '''
        # would load presets here
        
        # open last project etc.
        
        
        self.n=0
        # init internationalisation
        translator = QTranslator()
        path = os.path.dirname(os.path.realpath(__file__))
        translator.load(QLocale.system(), os.path.join(path, "startide_"))
        self.installTranslator(translator)

        # create the empty main window
        self.mainwindow = TouchWindow("startIDE")
        
        # and the central widget
        self.centralwidget=QWidget()
        
        # the main window layout
        l=QVBoxLayout()

        # program list widget
        self.proglist=QListWidget()
        self.proglist.setStyleSheet("font-family: 'Monospace'; font-size: 14px;")
        self.proglist.itemDoubleClicked.connect(self.progItemDoubleClicked)
        
        c=0
        for a in self.code:
            self.proglist.addItem(a)
            c=c+1
            
        l.addWidget(self.proglist)
        
        # alternate output text field
        
        self.output=QListWidget()
        self.output.setStyleSheet("font-family: 'Monospace'; font-size: 20px;")
        self.output.setSelectionMode(0)
        self.output.setVerticalScrollMode(1)
        self.output.setHorizontalScrollMode(1)
        
        l.addWidget(self.output)
        self.output.hide()
        
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
        self.starter.clicked.connect(self.startStop)
        
        self.start=False
        
        l.addWidget(self.starter)
        
        self.centralwidget.setLayout(l)
        self.mainwindow.setCentralWidget(self.centralwidget)
        
        self.mainwindow.titlebar.close.clicked.connect(self.closed)
        
        self.mainwindow.show()
        self.exec_()
    
    def closed(self):
        if self.start==True: self.startStop()

    def initIFs(self):
        #init robo family
        
        self.RIF=RoboInterface()
        if not self.RIF.hasInterface(): self.RIF=None
                
        self.TXT=None #for now ;-)        

    def startStop(self):
        self.starter.setEnabled(False)
        self.starter.setDisabled(True)
        self.processEvents()
        
        if self.etf:
            self.setMainWindow(True)
            self.etf=False
            self.start=False
        else:
            self.start=not self.start

            if self.start: self.setMainWindow(False)
            
            if self.start:
                self.et = execThread(self.code, self.output, self.starter, self.RIF, self.TXT)
                self.et.updateText.connect(self.updateText)
                self.et.clearText.connect(self.clearText)
                self.et.execThreadFinished.connect(self.execThreadFinished)
                self.et.start() 
            else:
                self.et.stop()
                self.et.wait()
            
            self.processEvents()

        self.starter.setEnabled(True)
        self.starter.setDisabled(False)

    def updateText(self, message):
        self.output.addItem(message)
        if self.output.count()>255: void=self.output.takeItem(0)
        self.output.scrollToBottom()
    
    def clearText(self):
        self.output.clear()
    
    def execThreadFinished(self):
        self.starter.setText(QCoreApplication.translate("main","Close log"))
        self.etf=True
        

    
    def setMainWindow(self, status):
        #true -> main window enabled 
        
        self.add.setVisible(status)
        self.rem.setVisible(status)
        self.upp.setVisible(status)
        self.don.setVisible(status)
        self.proglist.setVisible(status)
        
        self.output.setVisible(not status)
    
        if status: self.starter.setText(QCoreApplication.translate("main","Start")) 
        else:      self.starter.setText(QCoreApplication.translate("main","Stopp"))

    def addCodeLine(self):
        fta=TouchAuxMultibutton(QCoreApplication.translate("addcodeline","Add line"))
        fta.setText(QCoreApplication.translate("addcodeline","Select command type:"))
        fta.setButtons([ QCoreApplication.translate("addcodeline","Inputs"),
                         QCoreApplication.translate("addcodeline","Outputs"),
                         QCoreApplication.translate("addcodeline","Controls"),
                         QCoreApplication.translate("addcodeline","Interaction")
                        ]
                      )
        fta.setTextSize(3)
        fta.setBtnTextSize(3)
        (s,r)=fta.exec_()
        if r==QCoreApplication.translate("addcodeline","Inputs"):
            ftb=TouchAuxMultibutton(QCoreApplication.translate("addcodeline","Inputs"))
            #ftb.setText(QCoreApplication.translate("addcodeline","Select input cmd.:"))
            ftb.setButtons([ QCoreApplication.translate("addcodeline","WaitForInputDig"),
                             QCoreApplication.translate("addcodeline","IfInputDig")
                            ]
                          )
            ftb.setTextSize(3)
            ftb.setBtnTextSize(3)
            (t,p)=ftb.exec_()
        elif r==QCoreApplication.translate("addcodeline","Outputs"):
            ftb=TouchAuxMultibutton(QCoreApplication.translate("addcodeline","Outputs"))
            #ftb.setText(QCoreApplication.translate("addcodeline","Select output cmd.:"))
            ftb.setButtons([ QCoreApplication.translate("addcodeline","Output"),
                             QCoreApplication.translate("addcodeline","Motor"),
                             QCoreApplication.translate("addcodeline","MotorPulsewheel"),
                             QCoreApplication.translate("addcodeline","MotorEncoder")
                            ]
                          )
            ftb.setTextSize(3)
            ftb.setBtnTextSize(3)
            (t,p)=ftb.exec_()
        elif r==QCoreApplication.translate("addcodeline","Controls"):
            ftb=TouchAuxMultibutton(QCoreApplication.translate("addcodeline","Controls"))
            #ftb.setText(QCoreApplication.translate("addcodeline","Select control cmd.:"))
            ftb.setButtons([ QCoreApplication.translate("addcodeline","# comment"),
                             QCoreApplication.translate("addcodeline","Tag"),
                             QCoreApplication.translate("addcodeline","Jump"),
                             QCoreApplication.translate("addcodeline","LoopBack"),
                             QCoreApplication.translate("addcodeline","Delay"),
                             QCoreApplication.translate("addcodeline","Stop")
                            ]
                          )
            ftb.setTextSize(3)
            ftb.setBtnTextSize(3)
            (t,p)=ftb.exec_()
        elif r==QCoreApplication.translate("addcodeline","Interaction"):
            ftb=TouchAuxMultibutton(QCoreApplication.translate("addcodeline","Interact"))
            #ftb.setText(QCoreApplication.translate("addcodeline","Select interact cmd.:"))
            ftb.setButtons([ QCoreApplication.translate("addcodeline","Print"),
                             QCoreApplication.translate("addcodeline","Message"),
                             QCoreApplication.translate("addcodeline","Request")
                            ]
                          )
            ftb.setTextSize(3)
            ftb.setBtnTextSize(3)
            (t,p)=ftb.exec_()             

    def remCodeLine(self):
        row=self.proglist.currentRow()
        del self.code[row]
        void=self.proglist.takeItem(row)
        if self.code==[]:
            self.code=["# new"]
            self.proglist.addItem("# new")
            self.proglist.setCurrentRow(0)
        
    def lineUp(self):
        pass
    def lineDown(self):
        pass

    def progItemDoubleClicked(self):
        itm=self.proglist.currentItem()
        row=self.proglist.currentRow()
        cod=self.code[row]
                

if __name__ == "__main__":
    FtcGuiApplication(sys.argv)
