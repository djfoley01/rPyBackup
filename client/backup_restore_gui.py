from Tkinter import *
from PIL import ImageTk, Image
from ScrolledText import *
#import tkFileDialog
import tkMessageBox
import ConfigParser
import admin
import xml.etree.cElementTree as ET
import subprocess
import platform
#import sys
import os
import socket
import ssl
import struct

ostype = platform.system()

def ConfigSectionMap(section):
    dict1 = {}
    options = Config.options(section)
    for option in options:
        try:
            dict1[option] = Config.get(section, option)
            if dict1[option] == -1:
                DebugPrint("skip: %s" % option)
        except:
            print("exception on %s!" % option)
            dict1[option] = None
    return dict1

### Configuration - Initial variable load from config.ini ###
Config = ConfigParser.ConfigParser()
Config.read('config/config.ini')
HOST = ConfigSectionMap("main")['server']
PORT = int(ConfigSectionMap("main")['port'])
clientname = ConfigSectionMap("main")['clientname']
password = ConfigSectionMap("main")['password']
retention = ConfigSectionMap("main")['retention']
runHour = ConfigSectionMap("main")['runhour']
runMin = ConfigSectionMap("main")['runmin']

class backup_gui(Tk):
    def __init__(self,parent):
        Tk.__init__(self,parent)
        self.parent = parent
        self.initialize()

    def initialize(self):
        self.grid()
        
        self.textPad = ScrolledText(self, width=100, height=30)
        self.task_list = Listbox(self, width=50, height=8)
        self.task_list.grid(row=8, column=4)
        self.config_blank_label = Label(self, text="").grid(column=10,row=5,sticky='EW')

        # create a vertical scrollbar to the right of the listbox
        self.yscroll = Scrollbar(command=self.task_list.yview, orient=VERTICAL)
        self.yscroll.grid(row=8, column=5, sticky=N+S)
        self.task_list.configure(yscrollcommand=self.yscroll.set)
        
    def exit(self):
        if tkMessageBox.askokcancel("Quit", "Do you really want to quit?"):
            self.destroy()

    def about(self):
        label = tkMessageBox.showinfo("About", "rPyBackup Configuration Utility\n\nWritten By: Daniel Foley")
        
        self.grid_columnconfigure(0,weight=1)
        self.resizable(True,True)
        self.update()
        self.geometry('{}x{}'.format(650, 375))
        self.config_name.focus_set()
        self.config_name.selection_range(0, END)
        
    def open_task(self): 
        fin = self.remote_list().split('\n')
        #if fin is not None: 
         #   task_listread = fin.readlines() 
        for item in fin: 
            self.task_list.insert(END, item) 
        #fin.close()
        
    def remote_list(self):
        s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        socket1 = ssl.wrap_socket(s,ca_certs='config/sslcerts/server.crt',cert_reqs=ssl.CERT_REQUIRED)
        socket1.connect((HOST, PORT))
        self.send_one_message(socket1, self.retrieve_config())
        print "Remote Files:"
        commandName = clientname + " ls nofile"
        self.send_one_message(socket1, commandName)
        rlist = self.recv_one_message(socket1)
        socket1.close()
        return rlist
        
    def retrieve_config(self):
        server_string = clientname + " " + retention + " " + password
        print "Sending Config.. "
        return server_string
        
    def send_one_message(self, sock, data):
        length = len(data)
        sock.sendall(struct.pack('!I', length))
        sock.sendall(data)
    
    def recv_one_message(self, sock):
        lengthbuf = self.recvall(sock, 4)
        length, = struct.unpack('!I', lengthbuf)
        return self.recvall(sock, length)

    def recvall(self, sock, count):
        buf = b''
        while count:
            newbuf = sock.recv(count)
            if not newbuf: 
                return None
            buf += newbuf
            count -= len(newbuf)
            return buf
        
if __name__ == "__main__":
    ### OS Type Check - Now only Windows is configured ###
    # Issue / Bug during privilege escalation where two instances are spawned
    # Fix 

    app = backup_gui(None)
    app.title('rPyBackup Backup & Restore')
    
    menu = Menu(app)
    app.config(menu=menu)
    
    filemenu = Menu(menu)
    menu.add_cascade(label="File", menu=filemenu)
    filemenu.add_separator()
    filemenu.add_command(label="Exit", command=exit)
    
    helpmenu = Menu(menu)
    menu.add_cascade(label="Help", menu=helpmenu)
    helpmenu.add_command(label="About ", command=app.about)
    
    textPad = ScrolledText(app, width=100, height=30)
    task_list = Listbox(app, width=50, height=6)
    logo = ImageTk.PhotoImage(Image.open("images/logo.png"))
    imglabel = Label(app, image=logo).grid(row=0, column=4, rowspan=6,columnspan=3)
    app.iconbitmap('images/favicon.ico')
    
    app.open_task()
    app.mainloop()