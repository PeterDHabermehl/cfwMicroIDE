#! /usr/bin/env python3
# -*- coding: utf-8 -*-
#
import sys, time, os, json
import threading as thd
from TouchStyle import *
from TouchAuxiliary import *
from robointerface import *
from datetime import datetime

hostdir = os.path.dirname(os.path.realpath(__file__)) + "/"
projdir = hostdir + "/projects/"

if not os.path.exists(projdir):
    os.mkdir(projdir)
    
try:
    with open(hostdir+"manifest","r") as f:
        r=f.readline()
        while not "version" in r:
          r=f.readline()
        
        if "version" in r:
          vstring = "v" + r[ r.index(":")+2 : ]
        else: vstring=""
        f.close()
except:
    vstring="n/a"    
    

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
    showMessage=pyqtSignal(str)
    
    def __init__(self, codeList, output, starter, RIF,TXT, parent):
        QThread.__init__(self, parent)
        
        self.codeList=codeList
        
        self.output=output
        self.starter=starter
        self.msg=0 # für Messages aus dem GUI Thread
        
        self.RIF=RIF
        self.TXT=TXT
        self.parent=parent
        
    def run(self):

        self.halt=False
        
        self.requireTXT=False
        self.requireRIF=False
        
        self.jmpTable=[]
        self.LoopStack=[]
        self.modTable=[]
        self.modStack=[]
        
        cnt=0
        
        # scan code for interfaces, jump and module tags
        for line in self.codeList:
            if "TXT" in line: self.requireTXT=True
            if "RIF" in line: self.requireRIF=True
            if "Tag" in line: 
                self.jmpTable.append([line[4:], cnt])
            elif "Module" in line:
                self.modTable.append([line[7:], cnt])
            cnt=cnt+1

        self.clrOut()
        
        if self.requireTXT and self.TXT==None:
            self.msgOut(QCoreApplication.translate("exec","TXT not found!\nProgram terminated\n"))
            self.stop()
        if self.requireRIF and self.RIF==None:
            self.msgOut(QCoreApplication.translate("exec","RoboIF not found!\nProgram terminated\n"))
            self.stop()
        
        if not self.halt:
            self.msgOut("<Start>")
            self.count=0
        self.parent.processEvents()        
        
        while not self.halt and self.count<len(self.codeList):
            line=self.codeList[self.count]
            self.parseLine(line)
            self.count=self.count+1
            self.parent.processEvents()
        
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
        
    def setMsg(self, num):
        self.msg=num
        
    def parseLine(self,line):
        stack=line.split()
        if stack[0]  == "#": pass
        elif stack[0]== "Stop": self.count=len(self.codeList)
        elif stack[0]== "Output": self.cmdOutput(stack)
        elif stack[0]== "Motor": self.cmdMotor(stack)
        elif stack[0]== "MotorP": self.cmdMotorPulsewheel(stack)
        elif stack[0]== "Delay": self.cmdDelay(stack)
        elif stack[0]== "Jump": self.cmdJump(stack)
        elif stack[0]== "LoopTo": self.cmdLoopTo(stack)
        elif stack[0]== "WaitInDig": self.cmdWaitForInputDig(stack)
        elif stack[0]== "IfInDig": self.cmdIfInputDig(stack)
        elif stack[0]== "Print": self.cmdPrint(line[6:])
        elif stack[0]== "Clear": self.clrOut()
        elif stack[0]== "Message": self.cmdMessage(line[8:])
        elif stack[0]== "Module": self.count=len(self.codeList)
        elif stack[0]== "Call": self.cmdCall(stack)
        elif stack[0]== "Return": self.cmdReturn()
        
    def cmdOutput(self, stack):
        if stack[1]=="RIF":
            self.RIF.SetOutput(int(stack[2]),int(stack[3]))

    def cmdMotor(self, stack):
        if stack[1]=="RIF":
            self.RIF.SetMotor(int(stack[2]),stack[3], int(stack[4]))
    
    def cmdMotorPulsewheel(self, stack):
        m=int(stack[2])      # Output No.
        if stack[3] == "None": e = -1
        else: e = int(stack[3])   # End switch input
        p=int(stack[4]) # Pulse input
        d=stack[5]      # Direction
        s=int(stack[6]) # speed
        n=int(stack[7]) # pulses
        if stack[1]=="RIF":
            if e>-1:
                if d=="l" and self.RIF.Digital(e): return
            
            a=self.RIF.Digital(p)
            self.RIF.SetMotor(m,d,s)
            c=0
            while c<n and not self.halt:
                if e>-1:
                    if d=="l" and self.RIF.Digital(e): break
                b=a
                a=self.RIF.Digital(p)
                if not a==b: c=c+1
            
            self.RIF.SetMotor(m,"s",0)
            
            
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
        self.tOut=False
        self.tAct=False
        
        if len(stack)>4:
            if stack[4].isnumeric():
                if int(stack[4])>0:
                    self.timer = QTimer()
                    self.timer.setSingleShot(True)
                    self.timer.timeout.connect(self.timerstop)
                    self.timer.start(int(stack[4]))  
                    self.tAct=True

        if stack[1]=="RIF":
            if stack[3]=="Raising":
                a=self.RIF.Digital(int(stack[2]))
                b=a
                while not (b<a or self.halt or self.tOut ): 
                    b=a
                    a=self.RIF.Digital(int(stack[2]))
                    self.parent.processEvents()
            elif stack[3]=="Falling":
                a=self.RIF.Digital(int(stack[2]))
                b=a
                while not (b>a or self.halt or self.tOut ): 
                    b=a
                    a=self.RIF.Digital(int(stack[2]))
                    self.parent.processEvents()
        if self.tAct:
            self.timer.stop()
    
    def timerstop(self):
        self.tOut=True            
    
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

    def cmdCall(self, stack):
        n=-1
        for line in self.modTable:
            if stack[1]==line[0]: n=line[1]
        
        if n==-1:
            self.msgOut("Call module not found!")
            self.halt=True
        else:
            self.modStack.append(self.count)
            self.count=n

    def cmdReturn(self):
        try:
            self.count=self.modStack.pop()#[1]
        except:
            self.msgOut("Return without Call!")
            self.halt=True
    
    def cmdPrint(self, message):
        self.msgOut(message)
        time.sleep(0.005)
    
    def cmdMessage(self, rawline):
        self.msg=0
        self.showMessage.emit(rawline)
        while self.msg==0:
            time.sleep(0.01)
        self.msg=0
    
    def msgOut(self,message):
        self.updateText.emit(message)
        
    def clrOut(self):
        self.clearText.emit()
        time.sleep(0.005)

class editWaitForInputDig(TouchDialog):
    def __init__(self, cmdline, parent):
        TouchDialog.__init__(self, QCoreApplication.translate("ecl","WaitInDig"), parent)
        
        self.cmdline=cmdline
    
    def exec_(self):
    
        self.confirm = self.titlebar.addConfirm()
        self.confirm.clicked.connect(self.on_confirm)
    
        self.titlebar.setCancelButton()
        
        self.layout=QVBoxLayout()
        
        k1=QVBoxLayout()
        l=QLabel(QCoreApplication.translate("ecl", "Device"))
        l.setStyleSheet("font-size: 20px;")
        
        k1.addWidget(l)
        
        self.interface=QComboBox()
        self.interface.setStyleSheet("font-size: 20px;")
        self.interface.addItems(["RIF","TXT"])

        if self.cmdline.split()[1]=="TXT": self.interface.setCurrentIndex(1)

        k1.addWidget(self.interface)
        
        
        k2=QVBoxLayout()
        l=QLabel(QCoreApplication.translate("ecl","Port"))
        l.setStyleSheet("font-size: 20px;")
        k2.addWidget(l)
        
        self.port=QComboBox()
        self.port.setStyleSheet("font-size: 20px;")
        self.port.addItems(["I 1","I 2","I 3","I 4","I 5","I 6","I 7","I 8"])

        self.port.setCurrentIndex(int(self.cmdline.split()[2])-1)
        k2.addWidget(self.port)
        
        k9=QHBoxLayout()
        k9.addLayout(k1)
        k9.addStretch()
        k9.addLayout(k2)
        
        self.layout.addLayout(k9)
        
        l=QLabel(QCoreApplication.translate("ecl","Condition"))
        l.setStyleSheet("font-size: 20px;")
        self.layout.addWidget(l)     
        
        self.thd=QComboBox()
        self.thd.setStyleSheet("font-size: 20px;")
        self.thd.addItems(["Raising","Falling"])
        if self.cmdline.split()[3]=="Falling": self.thd.setCurrentIndex(1)
        self.layout.addWidget(self.thd)
        
        self.layout.addStretch()
        
        l=QLabel(QCoreApplication.translate("ecl","Timeout"))
        l.setStyleSheet("font-size: 20px;")
        self.layout.addWidget(l)     
        
        self.value=QLineEdit()
        self.value.setReadOnly(True)
        self.value.setStyleSheet("font-size: 20px;")
        self.value.setText(self.cmdline.split()[4])
        self.value.mousePressEvent=self.getValue
        self.layout.addWidget(self.value)
        
        self.layout.addStretch()
        
        self.centralWidget.setLayout(self.layout)
        
        TouchDialog.exec_(self)
        return self.cmdline
    
    def on_confirm(self):
        self.cmdline="WaitInDig " +self.interface.currentText()+ " " + self.port.currentText()[2:] + " " + self.thd.currentText() + " " + self.value.text()
        self.close()
    
    def getValue(self,m):
        a=self.value.text()
        t=TouchAuxKeyboard(QCoreApplication.translate("ecl","TOut"),a,None).exec_()
        if not t.isnumeric(): t=a
        t=str(max(min(int(t),99999),0))
        self.value.setText(t)

class editIfInputDig(TouchDialog):
    def __init__(self, cmdline, taglist, parent):
        TouchDialog.__init__(self, QCoreApplication.translate("ecl","IfInDig"), parent)
        
        self.cmdline=cmdline
        self.taglist=taglist
    
    def exec_(self):
    
        self.confirm = self.titlebar.addConfirm()
        self.confirm.clicked.connect(self.on_confirm)
    
        self.titlebar.setCancelButton()
        
        self.layout=QVBoxLayout()
        
        k1=QVBoxLayout()
        l=QLabel(QCoreApplication.translate("ecl", "Device"))
        l.setStyleSheet("font-size: 20px;")
        
        k1.addWidget(l)
        
        self.interface=QComboBox()
        self.interface.setStyleSheet("font-size: 20px;")
        self.interface.addItems(["RIF","TXT"])

        if self.cmdline.split()[1]=="TXT": self.interface.setCurrentIndex(1)

        k1.addWidget(self.interface)
        
        
        k2=QVBoxLayout()
        l=QLabel(QCoreApplication.translate("ecl","Port"))
        l.setStyleSheet("font-size: 20px;")
        k2.addWidget(l)
        
        self.port=QComboBox()
        self.port.setStyleSheet("font-size: 20px;")
        self.port.addItems(["I 1","I 2","I 3","I 4","I 5","I 6","I 7","I 8"])

        self.port.setCurrentIndex(int(self.cmdline.split()[2])-1)
        k2.addWidget(self.port)
        
        k9=QHBoxLayout()
        k9.addLayout(k1)
        k9.addStretch()
        k9.addLayout(k2)
        
        self.layout.addLayout(k9)
        
        l=QLabel(QCoreApplication.translate("ecl","Condition"))
        l.setStyleSheet("font-size: 20px;")
        self.layout.addWidget(l)     
        
        self.thd=QComboBox()
        self.thd.setStyleSheet("font-size: 20px;")
        self.thd.addItems(["True","False"])
        if self.cmdline.split()[3]=="False": self.thd.setCurrentIndex(1)
        self.layout.addWidget(self.thd)
        
        self.layout.addStretch()
        
        self.tags=QListWidget()
        self.tags.setStyleSheet("font-size: 20px;")
        self.tags.addItems(self.taglist)

        try:
            if self.cmdline.split()[4] in self.taglist:
                for i in range(self.tags.count()):
                    if self.cmdline.split()[4]==self.tags.item(i).text(): self.tags.setCurrentRow(i)
        except:
            self.tags.setCurrentRow(0)
            
        self.layout.addWidget(self.tags)
        
        self.centralWidget.setLayout(self.layout)
        
        TouchDialog.exec_(self)
        return self.cmdline
    
    def on_confirm(self):
        self.cmdline="IfInDig " +self.interface.currentText()+ " " + self.port.currentText()[2:] + " " + self.thd.currentText() + " " + self.tags.item(self.tags.currentRow()).text()
        self.close()

class editOutput(TouchDialog):
    def __init__(self, cmdline, parent=None):
        TouchDialog.__init__(self, QCoreApplication.translate("ecl","Output"), parent)
        
        self.cmdline=cmdline
    
    def exec_(self):
    
        self.confirm = self.titlebar.addConfirm()
        self.confirm.clicked.connect(self.on_confirm)
    
        self.titlebar.setCancelButton()
        
        self.layout=QVBoxLayout()
        
        k1=QVBoxLayout()
        l=QLabel(QCoreApplication.translate("ecl", "Device"))
        l.setStyleSheet("font-size: 20px;")
        
        k1.addWidget(l)
        
        self.interface=QComboBox()
        self.interface.setStyleSheet("font-size: 20px;")
        self.interface.addItems(["RIF","TXT"])

        if self.cmdline.split()[1]=="TXT": self.interface.setCurrentIndex(1)
        self.interface.currentIndexChanged.connect(self.ifChanged)
        k1.addWidget(self.interface)
        
        #self.layout.addStretch()
        
        k2=QVBoxLayout()
        l=QLabel(QCoreApplication.translate("ecl","Port"))
        l.setStyleSheet("font-size: 20px;")
        k2.addWidget(l)
        
        self.port=QComboBox()
        self.port.setStyleSheet("font-size: 20px;")
        self.port.addItems(["O 1","O 2","O 3","O 4","O 5","O 6","O 7","O 8"])

        self.port.setCurrentIndex(int(self.cmdline.split()[2])-1)
        k2.addWidget(self.port)
        
        k9=QHBoxLayout()
        k9.addLayout(k1)
        k9.addStretch()
        k9.addLayout(k2)
        
        self.layout.addLayout(k9)
        
        l=QLabel(QCoreApplication.translate("ecl","Value"))
        l.setStyleSheet("font-size: 20px;")
        self.layout.addWidget(l)     
        
        self.value=QLineEdit()
        self.value.setReadOnly(True)
        self.value.setStyleSheet("font-size: 20px;")
        self.value.setText(self.cmdline.split()[3])
        self.value.mousePressEvent=self.getValue
        self.layout.addWidget(self.value)
        
        self.layout.addStretch()
        
        self.centralWidget.setLayout(self.layout)
        
        TouchDialog.exec_(self)
        return self.cmdline
    
    def on_confirm(self):
        self.cmdline="Output " +self.interface.currentText()+ " " + self.port.currentText()[2:] + " " + self.value.text()
        self.close()
    
    def ifChanged(self):
        self.valueChanged()
    
    def getValue(self,m):
        a=self.value.text()
        t=TouchAuxKeyboard(QCoreApplication.translate("ecl","Value"),a,None).exec_()
        if not t.isnumeric(): t=a
        self.value.setText(t)
        self.valueChanged()
        
    def valueChanged(self):
        if not self.value.text().isnumeric(): self.value.setText("0")
        if self.interface.currentIndex()==0: self.value.setText(str(max(0,min(7,int(self.value.text())))))
        else: self.value.setText(str(max(0,min(511,int(self.value.text())))))

class editMotor(TouchDialog):
    def __init__(self, cmdline, parent=None):
        TouchDialog.__init__(self, QCoreApplication.translate("ecl","Motor"), parent)
        
        self.cmdline=cmdline
    
    def exec_(self):
    
        self.confirm = self.titlebar.addConfirm()
        self.confirm.clicked.connect(self.on_confirm)
    
        self.titlebar.setCancelButton()
        
        self.layout=QVBoxLayout()
        
        k1=QVBoxLayout()
        l=QLabel(QCoreApplication.translate("ecl", "Device"))
        l.setStyleSheet("font-size: 20px;")
        
        k1.addWidget(l)
        
        self.interface=QComboBox()
        self.interface.setStyleSheet("font-size: 20px;")
        self.interface.addItems(["RIF","TXT"])

        if self.cmdline.split()[1]=="TXT": self.interface.setCurrentIndex(1)
        self.interface.currentIndexChanged.connect(self.ifChanged)
        k1.addWidget(self.interface)
        
        #self.layout.addStretch()
        
        k2=QVBoxLayout()
        l=QLabel(QCoreApplication.translate("ecl","Port"))
        l.setStyleSheet("font-size: 20px;")
        k2.addWidget(l)
        
        self.port=QComboBox()
        self.port.setStyleSheet("font-size: 20px;")
        self.port.addItems(["M 1","M 2","M 3","M 4"])

        self.port.setCurrentIndex(int(self.cmdline.split()[2])-1)
        k2.addWidget(self.port)
        
        k8=QHBoxLayout()
        k8.addLayout(k1)
        k8.addStretch()
        k8.addLayout(k2)
        
        self.layout.addLayout(k8)        
        
        k3=QVBoxLayout()
        l=QLabel(QCoreApplication.translate("ecl","Value"))
        l.setStyleSheet("font-size: 20px;")
        k3.addWidget(l)     
        
        self.value=QLineEdit()
        self.value.setReadOnly(True)
        self.value.setStyleSheet("font-size: 20px;")
        self.value.setText(self.cmdline.split()[4])
        self.value.mousePressEvent=self.getValue
        k3.addWidget(self.value)
        
        k4=QVBoxLayout()
        l=QLabel(QCoreApplication.translate("ecl","Direction"))
        l.setStyleSheet("font-size: 20px;")
        k4.addWidget(l)
        
        self.direction=QComboBox()
        self.direction.setStyleSheet("font-size: 20px;")
        self.direction.addItems([QCoreApplication.translate("ecl","right"),QCoreApplication.translate("ecl","left"),QCoreApplication.translate("ecl","stop")])
        if self.cmdline.split()[3][:1]=="r": self.direction.setCurrentIndex(0)
        elif self.cmdline.split()[3][:1]=="l": self.direction.setCurrentIndex(1)
        elif self.cmdline.split()[3][:1]=="s": self.direction.setCurrentIndex(2)
        k4.addWidget(self.direction)
        
        k9=QHBoxLayout()
        k9.addLayout(k3)
        k9.addStretch()
        k9.addLayout(k4)
        
        self.layout.addLayout(k9)
        
        
        self.layout.addStretch()
        
        
        self.centralWidget.setLayout(self.layout)
        
        TouchDialog.exec_(self)
        return self.cmdline
    
    def on_confirm(self):
        self.cmdline="Motor " +self.interface.currentText()+ " " + self.port.currentText()[2:] + " "
        if self.direction.currentIndex()==0: d="r"
        elif self.direction.currentIndex()==1: d="l"
        elif self.direction.currentIndex()==2:
            d="s"
            self.value.setText("0")
            
        self.cmdline=self.cmdline + d + " " + self.value.text()
        self.close()
    
    def ifChanged(self):
        self.valueChanged()
    
    def getValue(self,m):
        a=self.value.text()
        t=TouchAuxKeyboard(QCoreApplication.translate("ecl","Value"),a,self).exec_()
        if not t.isnumeric(): t=a
        self.value.setText(t)
        self.valueChanged()
        
    def valueChanged(self):
        if not self.value.text().isnumeric(): self.value.setText("0")
        if self.interface.currentIndex()==0: self.value.setText(str(max(0,min(7,int(self.value.text())))))
        else: self.value.setText(str(max(0,min(511,int(self.value.text())))))

class editMotorPulsewheel(TouchDialog):
    def __init__(self, cmdline, parent=None):
        TouchDialog.__init__(self, QCoreApplication.translate("ecl","MotorP"), parent)
        
        self.cmdline=cmdline
    
    def exec_(self):
    
        self.confirm = self.titlebar.addConfirm()
        self.confirm.clicked.connect(self.on_confirm)
    
        self.titlebar.setCancelButton()
        
        self.layout=QVBoxLayout()

        #l=QLabel(QCoreApplication.translate("ecl", "with Pulsewheel"))
        #l.setStyleSheet("font-size: 20px;")        
        #self.layout.addWidget(l)
        #self.layout.addStretch()
        
        k1=QVBoxLayout()
        l=QLabel(QCoreApplication.translate("ecl", "Device"))
        l.setStyleSheet("font-size: 20px;")
        
        k1.addWidget(l)
        
        self.interface=QComboBox()
        self.interface.setStyleSheet("font-size: 20px;")
        self.interface.addItems(["RIF","TXT"])

        if self.cmdline.split()[1]=="TXT": self.interface.setCurrentIndex(1)
        self.interface.currentIndexChanged.connect(self.ifChanged)
        k1.addWidget(self.interface)
        
        #self.layout.addStretch()
        
        k2=QVBoxLayout()
        l=QLabel(QCoreApplication.translate("ecl","Port"))
        l.setStyleSheet("font-size: 20px;")
        k2.addWidget(l)
        
        self.port=QComboBox()
        self.port.setStyleSheet("font-size: 20px;")
        self.port.addItems(["M 1","M 2","M 3","M 4"])

        self.port.setCurrentIndex(int(self.cmdline.split()[2])-1)
        k2.addWidget(self.port)
        
        k8=QHBoxLayout()
        k8.addLayout(k1)
        k8.addStretch()
        k8.addLayout(k2)
        
        self.layout.addLayout(k8)        
        
        k3=QVBoxLayout()
        l=QLabel(QCoreApplication.translate("ecl","Value"))
        l.setStyleSheet("font-size: 20px;")
        k3.addWidget(l)     
        
        self.value=QLineEdit()
        self.value.setReadOnly(True)
        self.value.setStyleSheet("font-size: 20px;")
        self.value.setText(self.cmdline.split()[6])
        self.value.mousePressEvent=self.getValue
        k3.addWidget(self.value)
        
        k4=QVBoxLayout()
        l=QLabel(QCoreApplication.translate("ecl","Direction"))
        l.setStyleSheet("font-size: 20px;")
        k4.addWidget(l)
        
        self.direction=QComboBox()
        self.direction.setStyleSheet("font-size: 20px;")
        self.direction.addItems([QCoreApplication.translate("ecl","right"),QCoreApplication.translate("ecl","left"),QCoreApplication.translate("ecl","stop")])
        if self.cmdline.split()[5][:1]=="r": self.direction.setCurrentIndex(0)
        elif self.cmdline.split()[5][:1]=="l": self.direction.setCurrentIndex(1)
        elif self.cmdline.split()[5][:1]=="s": self.direction.setCurrentIndex(2)
        k4.addWidget(self.direction)
        
        k9=QHBoxLayout()
        k9.addLayout(k3)
        k9.addStretch()
        k9.addLayout(k4)
        
        self.layout.addLayout(k9)
    
        self.layout.addStretch()
        
        k5=QVBoxLayout()
        l=QLabel(QCoreApplication.translate("ecl", "End Sw."))
        l.setStyleSheet("font-size: 20px;")
        
        k5.addWidget(l)
        
        self.endSw=QComboBox()
        self.endSw.setStyleSheet("font-size: 20px;")
        self.endSw.addItems(["I 1","I 2","I 3","I 4","I 5","I 6","I 7","I 8"])
        self.endSw.setCurrentIndex(int(self.cmdline.split()[3])-1)

        k5.addWidget(self.endSw)
        
        #self.layout.addStretch()
        
        k6=QVBoxLayout()
        l=QLabel(QCoreApplication.translate("ecl","Pulse Inp."))
        l.setStyleSheet("font-size: 20px;")
        k6.addWidget(l)
        
        self.pulseSw=QComboBox()
        self.pulseSw.setStyleSheet("font-size: 20px;")
        self.pulseSw.addItems(["I 1","I 2","I 3","I 4","I 5","I 6","I 7","I 8"])

        self.pulseSw.setCurrentIndex(int(self.cmdline.split()[4])-1)
        k6.addWidget(self.pulseSw)
        
        k10=QHBoxLayout()
        k10.addLayout(k5)
        k10.addStretch()
        k10.addLayout(k6)
        
        self.layout.addLayout(k10)
        self.layout.addStretch()
        
        k13=QHBoxLayout()
        
        k11=QLabel("Pulses")
        k11.setStyleSheet("font-size: 20px;")
        
        k13.addWidget(k11)
        k13.addStretch()
        
        self.pulses=QLineEdit(self.cmdline.split()[7])
        self.pulses.setReadOnly(True)
        self.pulses.setStyleSheet("font-size: 20px;")
        self.pulses.mousePressEvent=self.getPulses
        k13.addWidget(self.pulses)
        
        self.layout.addLayout(k13)
        
        self.centralWidget.setLayout(self.layout)
        
        TouchDialog.exec_(self)
        return self.cmdline
    
    def on_confirm(self):
        self.cmdline="MotorP " +self.interface.currentText()+ " " + self.port.currentText()[2:] + " "
        self.cmdline=self.cmdline + self.endSw.currentText()[2:] + " " + self.pulseSw.currentText()[2:] + " "
        
        if self.direction.currentIndex()==0: d="r"
        elif self.direction.currentIndex()==1: d="l"
        elif self.direction.currentIndex()==2:
            d="s"
            self.value.setText("0")
            
        self.cmdline=self.cmdline + d + " " + self.value.text()
        self.cmdline=self.cmdline + " " + self.pulses.text()
        self.close()
    
    def ifChanged(self):
        self.valueChanged()
    
    def getValue(self,m):
        a=self.value.text()
        t=TouchAuxKeyboard(QCoreApplication.translate("ecl","Value"),a,self).exec_()
        if not t.isnumeric(): t=a
        self.value.setText(t)
        self.valueChanged()
    
    def getPulses(self,m):
        a=self.pulses.text()
        t=TouchAuxKeyboard(QCoreApplication.translate("ecl","Pulses"),a,self).exec_()
        if not t.isnumeric(): t=a
        if int(t)<0: t=str(0)
        if int(t)>9999: t=str(9999)
        self.pulses.setText(t)
      
        
    def valueChanged(self):
        if not self.value.text().isnumeric(): self.value.setText("0")
        if self.interface.currentIndex()==0: self.value.setText(str(max(0,min(7,int(self.value.text())))))
        else: self.value.setText(str(max(0,min(511,int(self.value.text())))))   
        
class editLoopTo(TouchDialog):
    def __init__(self, cmdline, taglist, parent):
        TouchDialog.__init__(self, QCoreApplication.translate("ecl","LoopTo"), parent)
        
        self.cmdline=cmdline
        self.taglist=taglist
    
    def exec_(self):
    
        self.confirm = self.titlebar.addConfirm()
        self.confirm.clicked.connect(self.on_confirm)
    
        self.titlebar.setCancelButton()
        
        self.layout=QVBoxLayout()
        

        l=QLabel(QCoreApplication.translate("ecl", "Loop target"))
        l.setStyleSheet("font-size: 20px;")
        self.layout.addWidget(l)
        
        self.tags=QListWidget()
        self.tags.setStyleSheet("font-size: 20px;")
        self.tags.addItems(self.taglist)
        try:
            if self.cmdline.split()[1] in self.taglist: self.tags.setCurrentRow(self.cmdline.split()[1])
        except:
            self.tags.setCurrentRow(0)
            
        self.layout.addWidget(self.tags)
        
        self.layout.addStretch()

        l=QLabel(QCoreApplication.translate("ecl", "Count"))
        l.setStyleSheet("font-size: 20px;")
        self.layout.addWidget(l)
        
        self.value=QLineEdit()
        self.value.setReadOnly(True)
        self.value.setStyleSheet("font-size: 20px;")
        self.value.setText(self.cmdline.split()[2])
        self.value.mousePressEvent=self.getValue
        self.layout.addWidget(self.value)
        
        self.layout.addStretch()
        
        self.centralWidget.setLayout(self.layout)
        
        TouchDialog.exec_(self)
        return self.cmdline
    
    def on_confirm(self):
        self.cmdline="LoopTo " +self.tags.item(self.tags.currentRow()).text()+ " " + self.value.text()
        self.close()
        
    def getValue(self,m):
        a=self.value.text()
        t=TouchAuxKeyboard(QCoreApplication.translate("ecl","TOut"),a,None).exec_()
        if not t.isnumeric(): t=a
        t=str(max(min(int(t),99999),0))
        self.value.setText(t)
        
        
class FtcGuiApplication(TouchApplication):
    response=pyqtSignal(int)
    wfiTimerStopped=pyqtSignal()
    
    def __init__(self, args):
        TouchApplication.__init__(self, args)
        
        # some init
        self.RIF=None
        self.TXT=None
        self.etf=False
        
        self.initIFs()
        
        self.lastIF="TXT"
        if self.RIF != None and self.TXT==None: self.lastIF="RIF"
        
        #define variables for test
        
        self.code=["# new"]
        
        # would load presets here
        
        # open last project etc.
        
        self.codeSaved=True
        self.codeName="startIDE"
        
        self.n=0
        
        # init internationalisation
        translator = QTranslator()
        path = os.path.dirname(os.path.realpath(__file__))
        translator.load(QLocale.system(), os.path.join(path, "startide_"))
        self.installTranslator(translator)

        # create the empty main window
        self.mainwindow = TouchWindow("startIDE")
        
        # add a menu
        
        self.menu=self.mainwindow.addMenu()
        self.menu.setStyleSheet("font-size: 20px;")
                
        self.m_project = self.menu.addAction(QCoreApplication.translate("mmain","Project"))
        self.m_project.triggered.connect(self.on_menu_project)     
        
        self.menu.addSeparator()
        
        self.m_interf = self.menu.addAction(QCoreApplication.translate("mmain","Interfaces"))
        self.m_interf.triggered.connect(self.on_menu_interfaces)  
        
        self.menu.addSeparator()
        
        self.m_about=self.menu.addAction(QCoreApplication.translate("mmain","About"))
        self.m_about.triggered.connect(self.on_menu_about)
        
        
        # and the central widget
        self.centralwidget=QWidget()
        
        # the main window layout
        l=QVBoxLayout()    
        
        # program list widget
        self.proglist=QListWidget()
        self.proglist.setStyleSheet("font-family: 'Monospace'; font-size: 16px;")
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

    def on_menu_about(self):
        t=TouchMessageBox(QCoreApplication.translate("m_about","About"), self.mainwindow)
        t.setCancelButton()
        t.setText("<center><h2>startIDE</h2><hr>" + QCoreApplication.translate("m_about","A tiny IDE to control Robo Family Interfaces and TXT Hardware") + "<hr>(c)2017 Peter Habermehl<br>Version: "+vstring)
        t.setTextSize(1)
        t.setBtnTextSize(2)
        t.setPosButton(QCoreApplication.translate("m_about","Okay"))
        (v1,v2)=t.exec_() 
    
    def on_menu_project(self):
        fta=TouchAuxMultibutton(QCoreApplication.translate("m_project","Project"), self.mainwindow)
        fta.setButtons([ QCoreApplication.translate("m_project","New"),
                        "",
                         QCoreApplication.translate("m_project","Load"),
                         QCoreApplication.translate("m_project","Save"),
                        "",
                         QCoreApplication.translate("m_project","Delete")
                        ]
                      )
        fta.setTextSize(3)
        fta.setBtnTextSize(3)
        (s,r)=fta.exec_()      
        
        if   r == QCoreApplication.translate("m_project","New"):    self.project_new()
        elif r == QCoreApplication.translate("m_project","Load"):   self.project_load()
        elif r == QCoreApplication.translate("m_project","Save"):   self.project_save()
        elif r == QCoreApplication.translate("m_project","Delete"): self.project_delete()
    
    def project_new(self):
        if not self.codeSaved:
            t=TouchMessageBox(QCoreApplication.translate("m_project","New"), self.mainwindow)
            t.setCancelButton()
            t.setText(QCoreApplication.translate("m_project","Current project was not saved. Do you want to discard it?"))
            t.setBtnTextSize(2)
            t.setPosButton(QCoreApplication.translate("m_project","Yes"))
            t.setNegButton(QCoreApplication.translate("m_project","No"))
            (r,s)=t.exec_()
            
            if s !=  QCoreApplication.translate("m_project","Yes"): return
        
        self.proglist.clear()
        self.code=[]
        self.proglist.addItem("# new")
        self.proglist.setCurrentRow(0)
        
        self.codeSaved=False
        
    def project_load(self):
        if not self.codeSaved:
            t=TouchMessageBox(QCoreApplication.translate("m_project","Load"), self.mainwindow)
            t.setCancelButton()
            t.setText(QCoreApplication.translate("m_project","Current project was not saved. Do you want to discard it?"))
            t.setBtnTextSize(2)
            t.setPosButton(QCoreApplication.translate("m_project","Yes"))
            t.setNegButton(QCoreApplication.translate("m_project","No"))
            (r,s)=t.exec_()
            
            if s !=  QCoreApplication.translate("m_project","Yes"): return
        
        # get list of projecs and query user
        filelist=os.listdir(projdir)
        filelist.sort()
        if len(filelist)>0:
            (s,r)=TouchAuxListRequester(QCoreApplication.translate("m_project","Load"),QCoreApplication.translate("ecl","Project"),filelist,filelist[0],"Okay",self.mainwindow).exec_()
        else:
            t=TouchMessageBox(QCoreApplication.translate("m_project","Load"), self.mainwindow)
            t.setCancelButton()
            t.setText(QCoreApplication.translate("m_project","No saved projects found."))
            t.setBtnTextSize(2)
            t.setPosButton(QCoreApplication.translate("m_project","Okay"))
            (v1,v2)=t.exec_()   
            s=False
            
        if not s: return
    
        with open(projdir+r,"r", encoding="utf-8") as f:
            self.code=json.load(f)
        
        self.proglist.clear()
        self.proglist.addItems(self.code)
        
        self.codeSaved=True
        self.codeName=r

    def project_save(self):
        (s,r)=TouchAuxRequestText(QCoreApplication.translate("m_project","Save"),
                            QCoreApplication.translate("m_project","Enter project file name:"),
                            self.codeName,
                            QCoreApplication.translate("m_project","Okay"), self.mainwindow
                            ).exec_()
        
        if not s: return
        pfn=r
        if os.path.isfile(projdir+pfn):
            t=TouchMessageBox(QCoreApplication.translate("m_project","Save"), self.mainwindow)
            t.setCancelButton()
            t.setText(QCoreApplication.translate("m_project","A file with this name already exists. Do you want to overwrite it?"))
            t.setBtnTextSize(2)
            t.setPosButton(QCoreApplication.translate("m_project","Yes"))
            t.setNegButton(QCoreApplication.translate("m_project","No"))
            (r,s)=t.exec_()
            
            if s !=  QCoreApplication.translate("m_project","Yes"): return
        
        self.codeFromListWidget()
        
        with open(projdir+pfn,"w", encoding="utf-8") as f:
            
            json.dump(self.code,f)
            f.close()
    
        self.codeSaved=True
        self.codeName=pfn
        
    def project_delete(self):
 
        # get list of projecs and query user
        filelist=os.listdir(projdir)                          
        if len(filelist)>0:
            (s,r)=TouchAuxListRequester(QCoreApplication.translate("m_project","Delete"),QCoreApplication.translate("ecl","Project"),filelist,filelist[0],"Okay",self.mainwindow).exec_()
        else:
            t=TouchMessageBox(QCoreApplication.translate("m_project","Delete"), self.mainwindow)
            t.setCancelButton()
            t.setText(QCoreApplication.translate("m_project","No saved projects found."))
            t.setBtnTextSize(2)
            t.setPosButton(QCoreApplication.translate("m_project","Okay"))
            (v1,v2)=t.exec_()   
            s=False
            
        if not s: return
        
        t=TouchMessageBox(QCoreApplication.translate("m_project","Delete"), self.mainwindow)
        t.setCancelButton()
        t.setText(QCoreApplication.translate("m_project","Do you really want to permanently delete this project?")+"<br>"+r)
        t.setBtnTextSize(2)
        t.setPosButton(QCoreApplication.translate("m_project","Yes"))
        t.setNegButton(QCoreApplication.translate("m_project","No"))
        (v1,v2)=t.exec_()
            
        if v2 !=  QCoreApplication.translate("m_project","Yes"): return
        
        os.remove(projdir+r)
        
        if self.codeName==r: self.codeSaved=False
        
    def on_menu_interfaces(self):
        
        self.initIFs()
        
        if self.RIF==None: s= QCoreApplication.translate("m_interfaces","No Robo device")
        else: s = self.RIF.GetDeviceTypeString()
                
        t = QCoreApplication.translate("m_interfaces","No TXT device")
        
        text="<center>" + QCoreApplication.translate("m_interfaces","Hardware found:") + "<hr><i>" + s + "<hr>" + t
        
        t=TouchMessageBox(QCoreApplication.translate("m_interfaces","Interfaces"), self.mainwindow)
        t.setCancelButton()
        t.setText(text)
        t.setTextSize(1)
        t.setBtnTextSize(2)
        t.setPosButton(QCoreApplication.translate("m_interfaces","Okay"))
        (v1,v2)=t.exec_()  
        
        
    def initIFs(self):
        # close, if open
        if self.RIF:
            self.RIF.close()
            time.sleep(0.1)
            
        #init robo family
        
        self.RIF=RoboInterface()
        if not self.RIF.hasInterface(): self.RIF=None
        
        self.TXT=None #for now ;-)        
            

    def codeFromListWidget(self):
        self.code=[]
        for i in range(0,self.proglist.count()): self.code.append(self.proglist.item(i).text())
        
    def startStop(self):
        self.starter.setEnabled(False)
        self.menu.setEnabled(False)
        self.mainwindow.titlebar.menubut.hide()
        self.starter.setDisabled(True)
        self.processEvents()
        
        if self.etf:
            self.setMainWindow(True)
            self.mainwindow.titlebar.menubut.show()
            self.menu.setEnabled(True)
            self.etf=False
            self.start=False
        else:
            self.start=not self.start
            
            if self.start:
                self.codeFromListWidget()
                self.setMainWindow(False)
                self.et = execThread(self.code, self.output, self.starter, self.RIF, self.TXT, self)
                self.et.updateText.connect(self.updateText)
                self.et.clearText.connect(self.clearText)
                self.et.execThreadFinished.connect(self.execThreadFinished)
                self.et.showMessage.connect(self.messageBox)
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
        
    def messageBox(self, stack):
        msg=stack[1:stack[1:].find("'")+1]
        btn=stack[len(msg)+3:][1:-1]
        t=TouchMessageBox(QCoreApplication.translate("exec","Message"), self.mainwindow)
        t.setCancelButton()
        t.setText(msg)
        t.setTextSize(2)
        t.setBtnTextSize(2)
        t.setPosButton(btn)
        (v1,v2)=t.exec_()       
        self.et.setMsg(1)
    
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
        fta=TouchAuxMultibutton(QCoreApplication.translate("addcodeline","Add line"), self.mainwindow)
        fta.setText(QCoreApplication.translate("addcodeline","Select command type:"))
        fta.setButtons([ QCoreApplication.translate("addcodeline","Inputs"),
                         QCoreApplication.translate("addcodeline","Outputs"),
                         QCoreApplication.translate("addcodeline","Controls"),
                         QCoreApplication.translate("addcodeline","Modules"),
                         QCoreApplication.translate("addcodeline","Interaction")
                        ]
                      )
        fta.setTextSize(3)
        fta.setBtnTextSize(3)
        (s,r)=fta.exec_()
        if r==QCoreApplication.translate("addcodeline","Inputs"):
            ftb=TouchAuxMultibutton(QCoreApplication.translate("addcodeline","Inputs"), self.mainwindow)
            ftb.setButtons([ QCoreApplication.translate("addcodeline","WaitForInputDig"),
                             QCoreApplication.translate("addcodeline","IfInputDig")
                            ]
                          )
            ftb.setTextSize(3)
            ftb.setBtnTextSize(3)
            (t,p)=ftb.exec_()
            if t:
                if   p==QCoreApplication.translate("addcodeline","WaitForInputDig"):    self.acl_waitForInputDig()
                elif p==QCoreApplication.translate("addcodeline","IfInputDig"):         self.acl_ifInputDig()
                
        elif r==QCoreApplication.translate("addcodeline","Outputs"):
            ftb=TouchAuxMultibutton(QCoreApplication.translate("addcodeline","Outputs"), self.mainwindow)
            ftb.setButtons([ QCoreApplication.translate("addcodeline","Output"),
                             QCoreApplication.translate("addcodeline","Motor"),
                             QCoreApplication.translate("addcodeline","MotorPulsewheel"),
                             QCoreApplication.translate("addcodeline","MotorEncoder")
                            ]
                          )
            ftb.setTextSize(3)
            ftb.setBtnTextSize(3)
            (t,p)=ftb.exec_()
            if t:
                if   p==QCoreApplication.translate("addcodeline","Output"):  self.acl_output()
                elif p==QCoreApplication.translate("addcodeline","Motor"):   self.acl_motor()
                elif p==QCoreApplication.translate("addcodeline","MotorPulsewheel"):   self.acl_motorPulsewheel()
                    
        elif r==QCoreApplication.translate("addcodeline","Controls"):
            ftb=TouchAuxMultibutton(QCoreApplication.translate("addcodeline","Controls"), self.mainwindow)
            ftb.setButtons([ QCoreApplication.translate("addcodeline","# comment"),
                             QCoreApplication.translate("addcodeline","Tag"),
                             QCoreApplication.translate("addcodeline","Jump"),
                             QCoreApplication.translate("addcodeline","LoopTo"),
                             QCoreApplication.translate("addcodeline","Delay"),
                             QCoreApplication.translate("addcodeline","Stop")
                            ]
                          )
            ftb.setTextSize(3)
            ftb.setBtnTextSize(3)
            (t,p)=ftb.exec_()
            if t:
                if   p==QCoreApplication.translate("addcodeline","# comment"):  self.acl_comment()
                elif p==QCoreApplication.translate("addcodeline","Tag"):        self.acl_tag()
                elif p==QCoreApplication.translate("addcodeline","Jump"):       self.acl_jump()
                elif p==QCoreApplication.translate("addcodeline","LoopTo"):     self.acl_loopTo()
                elif p==QCoreApplication.translate("addcodeline","Delay"):      self.acl_delay()
                elif p==QCoreApplication.translate("addcodeline","Stop"):       self.acl_stop()
        
        elif r==QCoreApplication.translate("addcodeline","Modules"):
            ftb=TouchAuxMultibutton(QCoreApplication.translate("addcodeline","Modules"), self.mainwindow)
            ftb.setButtons([ QCoreApplication.translate("addcodeline","Call"),
                             QCoreApplication.translate("addcodeline","Module"),
                             QCoreApplication.translate("addcodeline","Return")
                            ]
                          )
            ftb.setTextSize(3)
            ftb.setBtnTextSize(3)
            (t,p)=ftb.exec_()
            if t:
                if   p==QCoreApplication.translate("addcodeline","Call"):     self.acl_call()
                elif p==QCoreApplication.translate("addcodeline","Module"):   self.acl_module()
                elif p==QCoreApplication.translate("addcodeline","Return"):   self.acl_return()
                            
        elif r==QCoreApplication.translate("addcodeline","Interaction"):
            ftb=TouchAuxMultibutton(QCoreApplication.translate("addcodeline","Interact"), self.mainwindow)
            ftb.setButtons([ QCoreApplication.translate("addcodeline","Print"),
                             QCoreApplication.translate("addcodeline","Clear"),
                             QCoreApplication.translate("addcodeline","Message"),
                             QCoreApplication.translate("addcodeline","Request")
                            ]
                          )
            ftb.setTextSize(3)
            ftb.setBtnTextSize(3)
            (t,p)=ftb.exec_()
            if t:
                if   p==QCoreApplication.translate("addcodeline","Print"):      self.acl_print()
                elif p==QCoreApplication.translate("addcodeline","Clear"):        self.acl_clear()

    def acl(self,code):
        self.proglist.insertItem(self.proglist.currentRow()+1,code)
        self.proglist.setCurrentRow(self.proglist.currentRow()+1)
        self.progItemDoubleClicked()
        try:
            s=self.proglist.item(self.proglist.currentRow()).text().split()[1]
            if s=="RIF" or s=="TXT": self.lastIF=s
        except:
            pass
        
    def acl_waitForInputDig(self):
        self.acl("WaitInDig " + self.lastIF + " 1 Raising 0")
    
    def acl_ifInputDig(self):
        self.acl("IfInDig " + self.lastIF + " 1 True")
    
    def acl_output(self):
        self.acl("Output " + self.lastIF + " 1 0")
        
    def acl_motor(self):
        self.acl("Motor " + self.lastIF + " 1 l 0")
    
    def acl_motorPulsewheel(self):
        self.acl("MotorP " + self.lastIF + " 1 1 2 l 7 10")
    
    def acl_stop(self):
        self.acl("Stop")
    
    def acl_comment(self):
        self.acl("# ")
        
    def acl_tag(self):
        self.acl("Tag ")
        
    def acl_jump(self):
        self.acl("Jump ")
    
    def acl_loopTo(self):
        self.acl("LoopTo ? 2")
    
    def acl_delay(self):
        self.acl("Delay 1000")
    
    def acl_call(self):
        self.acl("Call ")
        
    def acl_module(self):
        self.acl("Module ")        
        
    def acl_return(self):
        self.acl("Return")
    
    def acl_print(self):
        self.acl("Print ")
    
    def acl_clear(self):
        self.acl("Clear")
    
    def remCodeLine(self):
        row=self.proglist.currentRow()
        void=self.proglist.takeItem(row)
        if self.proglist.count()==0:
            self.proglist.addItem("# new")
            self.proglist.setCurrentRow(0)
        
        self.codeSaved=False
        
    def lineUp(self):
        pass
    def lineDown(self):
        pass

    def progItemDoubleClicked(self):
        crow=self.proglist.currentRow()
        itm=self.proglist.item(crow).text()
        stack=itm.split()
        
        if   stack[0] == "Output":     itm=self.ecl_output(itm)
        elif stack[0] == "Motor":      itm=self.ecl_motor(itm)
        elif stack[0] == "MotorP":     itm=self.ecl_motorPulsewheel(itm)
        elif stack[0] == "MotorE":     itm=self.ecl_motorEncoder(itm)
        elif stack[0] == "WaitInDig":  itm=self.ecl_waitForInputDig(itm)
        elif stack[0] == "IfInDig":    itm=self.ecl_ifInputDig(itm)
        elif stack[0] == "#":          itm=self.ecl_comment(itm)
        elif stack[0] == "Tag":        itm=self.ecl_tag(itm)
        elif stack[0] == "Jump":       itm=self.ecl_jump(itm)
        elif stack[0] == "LoopTo":     itm=self.ecl_loopTo(itm)
        elif stack[0] == "Delay":      itm=self.ecl_delay(itm)
        elif stack[0] == "Stop":       itm=self.ecl_stop(itm)
        elif stack[0] == "Call":       itm=self.ecl_call(itm)
        elif stack[0] == "Module":     itm=self.ecl_module(itm)
        elif stack[0] == "Print":      itm=self.ecl_print(itm)
        elif stack[0] == "Message":    itm=self.ecl_message(itm)
        elif stack[0] == "Request":    itm=self.ecl_request(itm)
        
        self.proglist.setCurrentRow(crow)
        self.proglist.item(crow).setText(itm)
        self.codeSaved=False

    def ecl_output(self, itm):
        return editOutput(itm,self.mainwindow).exec_()
    
    def ecl_motor(self, itm):
        return editMotor(itm,self.mainwindow).exec_()
    
    def ecl_motorPulsewheel(self, itm):
        return editMotorPulsewheel(itm,self.mainwindow).exec_()
    
    def ecl_motorEncoder(self, itm):
        return itm
    
    def ecl_waitForInputDig(self, itm):
        return editWaitForInputDig(itm,self.mainwindow).exec_()
    
    def ecl_ifInputDig(self, itm):
        tagteam=[]
        for i in range(0,self.proglist.count()):
            if self.proglist.item(i).text().split()[0]=="Tag": tagteam.append(self.proglist.item(i).text()[4:])
  
        if len(tagteam)==0:
            t=TouchMessageBox(QCoreApplication.translate("ecl","IfInDig"), self.mainwindow)
            t.setCancelButton()
            t.setText(QCoreApplication.translate("ecl","No Tags defined!"))
            t.setTextSize(2)
            t.setBtnTextSize(2)
            t.setPosButton(QCoreApplication.translate("ecl","Okay"))
            (v1,v2)=t.exec_()
            return itm
        
        return editIfInputDig(itm,tagteam,self.mainwindow).exec_()
    
    def ecl_comment(self, itm):
        return "# "+TouchAuxKeyboard(QCoreApplication.translate("ecl","Comment"),itm[2:],self.mainwindow).exec_()
    
    def ecl_tag(self, itm):
        return "Tag "+clean(TouchAuxKeyboard(QCoreApplication.translate("ecl","Tag"),itm[4:],self.mainwindow).exec_(),32)
    
    def ecl_jump(self, itm):
        itm=itm[5:]
        tagteam=[]
        for i in range(0,self.proglist.count()):
            if self.proglist.item(i).text().split()[0]=="Tag": tagteam.append(self.proglist.item(i).text()[4:])
  
        if len(tagteam)==0:
            t=TouchMessageBox(QCoreApplication.translate("ecl","Jump"), self.mainwindow)
            t.setCancelButton()
            t.setText(QCoreApplication.translate("ecl","No Tags defined!"))
            t.setTextSize(2)
            t.setBtnTextSize(2)
            t.setPosButton(QCoreApplication.translate("ecl","Okay"))
            (v1,v2)=t.exec_()
            return "Jump "+itm
        
        if not itm in tagteam: itm=tagteam[0]
        (s,r)=TouchAuxListRequester(QCoreApplication.translate("ecl","Jump"),QCoreApplication.translate("ecl","Target"),tagteam,itm,"Okay", self.mainwindow).exec_()
        
        if not s: return "Jump "+itm
        return "Jump "+r
        
    def ecl_loopTo(self, itm):
        tagteam=[]
        for i in range(0,self.proglist.count()):
            if self.proglist.item(i).text().split()[0]=="Tag": tagteam.append(self.proglist.item(i).text()[4:])
  
        if len(tagteam)==0:
            t=TouchMessageBox(QCoreApplication.translate("ecl","LoopTo"), self.mainwindow)
            t.setCancelButton()
            t.setText(QCoreApplication.translate("ecl","No Tags defined!"))
            t.setTextSize(2)
            t.setBtnTextSize(2)
            t.setPosButton(QCoreApplication.translate("ecl","Okay"))
            (v1,v2)=t.exec_()
            return itm
        
        return editLoopTo(itm,tagteam,self.mainwindow).exec_()
    
    def ecl_delay(self, itm):
        t=TouchAuxKeyboard(QCoreApplication.translate("ecl","Delay"),itm[6:],self.mainwindow).exec_()
        try:
            return "Delay "+str(int(t))
        except:
            pass
        return "Delay "+itm
        
    def ecl_stop(self, itm):
        return itm
    
    def ecl_module(self, itm):
        return "Module "+clean(TouchAuxKeyboard(QCoreApplication.translate("ecl","Module"),itm[7:],self.mainwindow).exec_(),32)
    
    def ecl_call(self, itm):
        itm=itm[5:]
        tagteam=[]
        for i in range(0,self.proglist.count()):
            if self.proglist.item(i).text().split()[0]=="Module": tagteam.append(self.proglist.item(i).text()[7:])
  
        if len(tagteam)==0:
            t=TouchMessageBox(QCoreApplication.translate("ecl","Call"), self.mainwindow)
            t.setCancelButton()
            t.setText(QCoreApplication.translate("ecl","No Modules defined!"))
            t.setTextSize(2)
            t.setBtnTextSize(2)
            t.setPosButton(QCoreApplication.translate("ecl","Okay"))
            (v1,v2)=t.exec_()
            return "Call "+itm
        
        if not itm in tagteam: itm=tagteam[0]
        (s,r)=TouchAuxListRequester(QCoreApplication.translate("ecl","Call"),QCoreApplication.translate("ecl","Target"),tagteam,itm,"Okay", self.mainwindow).exec_()
        
        if not s: return "Call "+itm
        return "Call "+r    

    def ecl_print(self, itm):
        return "Print "+TouchAuxKeyboard(QCoreApplication.translate("ecl","Delay"),itm[6:],self.mainwindow).exec_()
        
    def ecl_message(self, itm):
        return itm
    
    def ecl_request(self, itm):
        return itm
    
    
def clean(text,maxlen):
    res=""
    valid="abcdefghijklmnopqrstuvwxyzABCDEFGHIJKLMNOPQRSTUVWXYZ1234567890_-."
    for ch in text:
        if ch in valid: res=res+ch
    return res[:maxlen]


if __name__ == "__main__":
    FtcGuiApplication(sys.argv)
