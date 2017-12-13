#!/usr/bin/python3
# -*- coding: utf-8 -*-

import translator as tr
import htmlhelper as hth
import cgi, os, json, sys

def mainpage():
    hth.htmlhead("startIDE", tr.translate("Control your model with a finger touch"))
    print('<img src="icon.png">')
    hth.separator()
    hth.text(tr.translate("<b>Download</b> a"))
    hth.link(tr.translate("project"),"index.py?action=PDown")
    hth.text(tr.translate("or a"))
    hth.link(tr.translate("module"),"index.py?action=MDown")
    hth.text(tr.translate("from your TXT."))
    hth.lf(2)
    hth.text(tr.translate("<b>Upload</b> a"))
    hth.link(tr.translate("project"),"index.py?action=PUp")
    hth.text(tr.translate("or a"))
    hth.link(tr.translate("module"),"index.py?action=MUp")
    hth.text(tr.translate("to your TXT."))
    hth.lf(2)
    hth.text(tr.translate("<b>Show</b> a"))
    hth.link(tr.translate("project"),"index.py?action=PList")
    hth.text(tr.translate("or a"))
    hth.link(tr.translate("module"),"index.py?action=MList")
    hth.text(tr.translate("code listing."))
    hth.lf(2)
    hth.text(tr.translate("<b>Download</b> a"))
    hth.link(tr.translate("logfile"),"index.py?action=LogDown") 
    hth.text(tr.translate("from your TXT."))
    hth.lf(1)
    hth.text(tr.translate("<b>Convert</b> a"))
    hth.link(tr.translate("logfile"),"index.py?action=LogCSV") 
    hth.text(tr.translate("to .CSV"))
    hth.separator()
    hth.htmlfoot("","/","TXT Home")

def download(obj:str):
    if obj=="P": hth.htmlhead("startIDE", tr.translate("Download a project from your TXT"))
    elif obj=="M": hth.htmlhead("startIDE", tr.translate("Download a module from your TXT"))
    elif obj=="L": hth.htmlhead("startIDE", tr.translate("Download a log file from your TXT"))
    hth.separator()
    hth.lf()
    
    if obj=="P":
        hth.text(tr.translate("Please select project:"))
        hth.lf(2)
        downloadfiles("projects/")
    elif obj=="M":
        hth.text(tr.translate("Please select module:"))
        hth.lf(2)
        downloadfiles("modules/")
    elif obj=="L":
        hth.text(tr.translate("Please select log file:"))
        hth.lf(2)
        downloadfiles("logfiles/")
    elif obj=="C":
        hth.text(tr.translate("Please select log file:"))
        hth.lf(2)
        downloadCSVfiles("logfiles/")
    hth.lf(2)
    hth.separator()
    hth.htmlfoot("","javascript:history.back()",tr.translate("Back"))

def upload(obj:str):
    if obj=="P": hth.htmlhead("startIDE", tr.translate("Upload a project  to your TXT"))
    elif obj=="M": hth.htmlhead("startIDE", tr.translate("Upload a module to your TXT"))
    
    hth.separator()
    hth.lf(2)
    
    if obj=="P": hth.text(tr.translate("Please select project:"))
    elif obj=="M": hth.text(tr.translate("Please select module:"))
    
    print('<form action="index.py" method="post" enctype="multipart/form-data">')
    print('<label>')
    
    if obj=="P":
        hth.text(tr.translate("Project file:"))
        print('<input name="project" type="file" size="50" accept="application/zip,application/x-zip,application/x-zip-compressed"> </label>')
    elif obj=="M":
        hth.text(tr.translate("Module file:"))
        print('<input name="module" type="file" size="50" accept="application/zip,application/x-zip,application/x-zip-compressed"> </label>')

    print('<button type="submit">')
    hth.text(tr.translate("Upload!"))
    print('</button></form>')

    hth.lf(2)
    hth.separator()
    hth.htmlfoot("","javascript:history.back()",tr.translate("Back"))

def codelist(obj:str):
    if obj=="P": hth.htmlhead("startIDE", tr.translate("Show a project code listing"))
    elif obj=="M": hth.htmlhead("startIDE", tr.translate("Show a module code listing"))
    
    hth.separator()
    hth.lf()

    if obj=="P":
        hth.text(tr.translate("Please select project:"))
        hth.lf(2)
        listfiles("projects/")
    elif obj=="M":
        hth.text(tr.translate("Please select module:"))
        hth.lf(2)
        listfiles("modules/")
    hth.lf(2)
    hth.separator()
    hth.htmlfoot("","javascript:history.back()",tr.translate("Back"))

def listfiles(directory:str):
    stack=os.listdir(directory)
    for a in stack:
        hth.link(a,"index.py?list="+directory+a)
        hth.lf()

def downloadfiles(directory:str):
    stack=os.listdir(directory)
    for a in stack:
        hth.link(a,directory+a,"download")
        hth.lf()    

def downloadCSVfiles(directory:str):
    stack=os.listdir(directory)
    for a in stack:
        if a[-4:]==".txt":
            hth.link(a,"index.py?csv="+directory+a)
            hth.lf()

def uploader(obj:str, fileitem):
    
    filename = fileitem.filename    
    
    if obj=="P": filename = "projects/"+filename
    elif obj=="M": filename = "modules/"+filename
    
    try:
        open(filename, 'wb').write(fileitem.file.read())
        os.chmod(filename,0o666)
        mainpage()
    except:
        hth.htmlhead("startIDE", tr.translate("Upload failed"))
        hth.htmlfoot("","index.py",tr.translate("Back"))

def filelister(name:str):
    print('Content-Type: text/plain')
    print('')

    print("  startIDE code listing: "+name)
    print("  ======================")
    print('')
    with open(name,"r", encoding="utf-8") as f:
        code=json.load(f)
        a=0
        for i in code:
            a=a+1
            print("%5i:  %s" % (a,i))

def csvconvert(name:str):
    varlist=[]
    with open(name, "r", encoding="utf-8") as f:
        for line in f:
            stack=line.split()
            found=False
            for v in varlist:
                if v[0]==stack[0]: found=True
    
            if not found: varlist.append([stack[0],0])
    f.close()
    
    for i in range(0,len(varlist)):
        varlist[i][1]=open(name+"-csv-export-"+str(i), "w", encoding="utf-8")
        varlist[i][1].write(varlist[i][0]+"\n")
    
    with open(name, "r", encoding="utf-8") as f:
        for line in f:
            stack=line.split()
            found=-1
            for i in range(0,len(varlist)):
                if varlist[i][0]==stack[0]: found=i
            
            if found>-1:
                varlist[found][1].write(str(stack[1])+"\n")
    f.close()
    
    for v in varlist:
        v[1].close()
    
    for i in range(0,len(varlist)):
        varlist[i][1]=open(name+"-csv-export-"+str(i), "r", encoding="utf-8")
        
    ofs =len(varlist)
    
    #with open(name+"-csv-export-final", "w", encoding="utf-8") as ef:
    
    print("Content-Type: text/plain; charset=UTF-8")
    print("Content-Disposition: attachment; filename=%s" % os.path.basename(name[:-4]+".csv"))
    print('')
        
    while ofs>0:
        for i in range(0, len(varlist)):
            ln=""
            if not varlist[i][1].closed: ln=varlist[i][1].readline()
            if ln: sys.stdout.write(ln[:-1]+";")   #ef.write(ln[:-1]+";") 
            elif not varlist[i][1].closed:
                varlist[i][1].close()
                ofs=ofs-1 
        
        #sys.stdout.write("\n")
        #ef.close()
    
    for i in range(0,len(varlist)):
        varlist[i][1].close()
        os.remove(name+"-csv-export-"+str(i))
        
# *****************************************************
# *************** Ab hier geht's los ******************
# *****************************************************

if __name__ == "__main__":
    
    form = cgi.FieldStorage()
#    hth.htmlhead("startIDE", tr.translate("Upload a project  to your TXT"))
#    print(form)
#    hth.htmlfoot("","/","TXT Home")
    
    if "action" in form:
        if form["action"].value=="PDown": download("P")
        if form["action"].value=="MDown": download("M")
        if form["action"].value=="PUp": upload("P")
        if form["action"].value=="MUp": upload("M")
        if form["action"].value=="PList": codelist("P")
        if form["action"].value=="MList": codelist("M")
        if form["action"].value=="LogDown": download("L")
        if form["action"].value=="LogCSV": download("C")
    elif "module" in form:
        uploader("M", form["module"])
    elif "project" in form:
        uploader("P", form["project"])
    elif "list" in form:
        filelister(form["list"].value)
    elif "csv" in form:
        csvconvert(form["csv"].value)
    else:
        mainpage()
    
    
