#! /usr/bin/env python3
# -*- coding: utf-8 -*-
#
import sys
from TouchStyle import *
from TouchAuxiliary import *

class FtcGuiApplication(TouchApplication):
    def __init__(self, args):
        TouchApplication.__init__(self, args)

        # create the empty main window
        self.mainwindow = TouchWindow("startIDE")
        self.mainwindow.show()
        self.exec_()        

if __name__ == "__main__":
    FtcGuiApplication(sys.argv)
