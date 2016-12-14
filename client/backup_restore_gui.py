from Tkinter import *
from PIL import ImageTk, Image
from ScrolledText import *
#import tkFileDialog
import tkMessageBox
import ConfigParser
import admin
import hashlib
import tarfile
import time
import datetime
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
lastrun = ConfigSectionMap("main")['lastrun']

class backup_gui(Tk):
    def __init__(self,parent):
        Tk.__init__(self,parent)
        self.parent = parent
        self.initialize()

    def initialize(self):
        self.grid()
        
        self.config_name_label = Label(self, text="Files Located on File Server:").grid(column=4,row=6,sticky='EW')
        
        self.textPad = ScrolledText(self, width=130, height=30)
        self.task_list = Listbox(self, width=65, height=8)
        self.task_list.grid(row=7, column=4)

        # create a vertical scrollbar to the right of the listbox
        self.yscroll = Scrollbar(command=self.task_list.yview, orient=VERTICAL)
        self.yscroll.grid(row=7, column=5, sticky=N+S)
        self.task_list.configure(yscrollcommand=self.yscroll.set)
        
        self.backup_lastrun_label = Label(self, text="Last Run: ").grid(column=0,row=3,sticky='EW')
        self.backup_lastrunVariable = StringVar()
        self.backup_lastrun = Label(self,textvariable=self.backup_lastrunVariable)
        self.backup_lastrun.grid(column=1,row=3,sticky='EW')
        #self.config_nextrunVar = query_windows_task()
        self.backup_lastrunVariable.set(datetime.datetime.fromtimestamp(float(lastrun)).strftime('%Y-%m-%d %H:%M:%S'))
        
        self.status_label = Label(self, text="Status: ").grid(column=3,row=9,sticky='EW')
        self.statusVariable = StringVar()
        self.status = Label(self,textvariable=self.statusVariable,bg='blue',foreground='white')
        self.status.grid(column=4,row=9,sticky='NSEW')
        #self.config_nextrunVar = query_windows_task()
        
        
        self.button_run_full = Button(self, text=' Run Full Backup Now ', command=self.run_configured_backup)
        self.button_run_full.grid(row=4, column=0, sticky=E)
        
        self.button_run_inc = Button(self, text='  Run Inc Backup Now ', command=self.inc_backup)
        self.button_run_inc.grid(row=5, column=0, sticky=E)
        
        self.button_download = Button(self, text='Download Selected Backup', command=self.download_file)
        self.button_download.grid(row=8, column=4, sticky=E)
        
        self.grid_columnconfigure(0,weight=1)
        self.resizable(True,True)
        self.geometry('{}x{}'.format(700, 300))
        
    def download_file(self):
        index = self.task_list.curselection()[0]
        # get the line's text
        seltext = self.task_list.get(index)
        cmd = clientname + " get " + seltext
        self.get(cmd)
        
    def hashfile(self, afile, hasher, blocksize=65536):
        buf = afile.read(blocksize)
        while len(buf) > 0:
            hasher.update(buf)
            buf = afile.read(blocksize)
        return hasher.digest()
    
    def put(self,commandName):
        s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        socket1 = ssl.wrap_socket(s,ca_certs='config/sslcerts/server.crt',cert_reqs=ssl.CERT_REQUIRED)
        socket1.connect((HOST, PORT))
        self.send_one_message(socket1, self.retrieve_config())
        self.send_one_message(socket1, commandName)
        string = commandName.split(' ', 2)
        inputFile = string[2]
        file_hash = self.hashfile(open(inputFile, 'rb'), hashlib.sha256())
        self.send_one_message(socket1, file_hash)
        with open(inputFile, 'rb') as file_to_send:
            data = file_to_send.read()
        socket1.sendall('%16d' % len(data))
        socket1.sendall(data)
        self.statusVariable.set(self.recv_one_message(socket1))
        socket1.close()
        self.open_task()
        return
        
    def get(self,commandName):
        s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        socket1 = ssl.wrap_socket(s,ca_certs='config/sslcerts/server.crt',cert_reqs=ssl.CERT_REQUIRED)
        socket1.connect((HOST, PORT))
        self.send_one_message(socket1, self.retrieve_config())
        self.send_one_message(socket1, commandName)
        string = commandName.split(' ', 2)
        inputFile = string[2]
        inc_file_hash = self.recv_one_message(socket1)
        file_size = int(socket1.recv(16))
        recvd = ''
        with open(inputFile, 'wb') as file_to_write:
            while file_size > len(recvd):
                data = socket1.recv(8192)
                if not data:
                    break
                recvd += data
                file_to_write.write(data)
            
        file_to_write.close()
        file_hash = self.hashfile(open(inputFile, 'rb'), hashlib.sha256())
        if inc_file_hash == file_hash:
            self.statusVariable.set(" Receive Success - Hashes Match")
            self.send_one_message(socket1, "Receive Success - Hashes Match")
        else:
            self.statusVariable.set("Receive Failed - Hashes DoNot Match")
            self.send_one_message(socket1, "Receive Failed - Hashes Do Not Match")
        socket1.close()
        return
        
    def make_tarfile(self, output_filename, source_dir_list):
        with tarfile.open(output_filename, "w:gz") as tar:
            for source_dir in source_dir_list:
                tar.add(source_dir, arcname=os.path.basename(source_dir))
            tar.close()
        
    def make_inctarfile(self, output_filename, source_dir_list, lastrun):
        self.now = time.time()
        self.out = tarfile.open(output_filename, mode='w:gz')

        # start walk via all files to find changed since lastrun
        for dir_to_backup in source_dir_list:
            for root, dirs, files in  os.walk(dir_to_backup, followlinks=True):
                for file in files:
                    file = os.path.join(root, file)
                    try:
                        filemodtime = os.path.getmtime(file)
                        if filemodtime > float(lastrun):
                            if os.path.isfile(file):
                                self.statusVariable.set('Adding file: %s...' % file)
                                self.out.add(file)
                                self.statusVariable.set('File modified: %s' % time.ctime(os.path.getmtime(file)))
                    except OSError as error:
                        self.statusVariable.set('ERROR: %s' % error)

        self.statusVariable.set('Closing archive.')
        self.out.close()
    
    def delete_tarfile(self, filename):
        print filename
        if os.path.isfile(filename):
            try:
                os.remove(filename)
                self.statusVariable.set("Successfully removed temporary file")
            except:
                self.statusVariable.set("Unable to delete temporary file")
        else:
            self.statusVariable.set("Temporary file not found")
        
    def run_configured_backup(self):
        data = [line.strip() for line in open("config/config_paths", 'r')]
        fname = clientname
        fmt = "%m%d%Y_%H%M%S_FullBackup_" + clientname + ".tar.gz"
        output_fname = datetime.datetime.now().strftime(fmt).format(fname)
        self.make_tarfile(output_fname, data)
        cmd = clientname + " put " + output_fname
        self.put(cmd)
        self.delete_tarfile(output_fname)
        self.set_lastrun()
    
    def inc_backup(self):
        data = [line.strip() for line in open("config/config_paths", 'r')]
        fname = clientname
        fmt = "%m%d%Y_%H%M%S_IncBackup_" + clientname + ".tar.gz"
        output_fname = datetime.datetime.now().strftime(fmt).format(fname)
        self.make_inctarfile(output_fname, data, self.get_lastrun())
        cmd = clientname + " put " + output_fname
        self.put(cmd)
        self.delete_tarfile(output_fname)
        self.set_lastrun()
#    print('Creating archive %s...' % backupname)

    def set_lastrun(self):
        now = time.time()
        cfgfile = open('config/config.ini', 'w')
        Config.set('main', 'lastrun', now)
        Config.write(cfgfile)
        cfgfile.close()
        self.update_vars()
        
    def exit(self):
        if tkMessageBox.askokcancel("Quit", "Do you really want to quit?"):
            self.destroy()

    def about(self):
        label = tkMessageBox.showinfo("About", "rPyBackup Backup & Restore GUI\n\nWritten By: Daniel Foley")
        
    def open_task(self): 
        fin = self.remote_list()
        if fin is None:
            return
        task_listread = fin.split('\n')
        self.task_list.delete(0, END)
        #if fin is not None: 
         #   task_listread = fin.readlines() 
        for item in task_listread: 
            self.task_list.insert(END, item) 
        #fin.close()
        
    def remote_list(self):
        try:
            s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            socket1 = ssl.wrap_socket(s,ca_certs='config/sslcerts/server.crt',cert_reqs=ssl.CERT_REQUIRED)
            socket1.connect((HOST, PORT))
            if self.statusVariable.get():
                pass
            else:
                self.statusVariable.set("         Connected to Server         ")
        except:
            self.statusVariable.set("   Failed to connect to Server   ")
            return
        self.send_one_message(socket1, self.retrieve_config())
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
        
    def update_vars(self):
        Config.read('config/config.ini')
        lastrun = ConfigSectionMap("main")['lastrun']
        #lastrun_plain = datetime.datetime.fromtimestamp(lastrun)
        self.backup_lastrunVariable.set(datetime.datetime.fromtimestamp(float(lastrun)).strftime('%Y-%m-%d %H:%M:%S'))
        
    def get_lastrun(self):
        Config.read('config/config.ini')
        lastrun = ConfigSectionMap("main")['lastrun']
        return lastrun
        
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
    #filemenu.add_separator()
    filemenu.add_command(label="Exit", command=exit)
    
    helpmenu = Menu(menu)
    menu.add_cascade(label="Help", menu=helpmenu)
    helpmenu.add_command(label="About ", command=app.about)
    
    textPad = ScrolledText(app, width=100, height=30)
    task_list = Listbox(app, width=50, height=6)
    logo = ImageTk.PhotoImage(Image.open("images/logo.png"))
    imglabel = Label(app, image=logo).grid(row=0, column=2, rowspan=6,columnspan=3)
    app.iconbitmap('images/favicon.ico')
    
    app.open_task()
    app.mainloop()