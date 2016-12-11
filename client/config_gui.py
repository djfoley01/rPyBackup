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

ostype = platform.system()

### Windows Specific Scheduled Tasks ###
def query_windows_task():
    try:
        FNULL = open(os.devnull, 'w')
        wtask_query = subprocess.Popen(["SchTasks.exe", "/query", "/TN", "rPyBackup", "/XML"], stdout=subprocess.PIPE, stderr=FNULL).communicate()[0]
        wtask_query_xml = ET.fromstring(wtask_query.replace('UTF-16', 'UTF-8'))
        wtask_start_time = wtask_query_xml[3][0][0].text
        FNULL.close()
        return wtask_start_time
    except:
        return "Not Configured"

def create_windows_task(hour, minute):
    #wtask_create = subprocess.Popen(["SchTasks.exe", "/create", "/SC", "DAILY", "/TN", "rPyBackup", "/TR", "C:\rPyBackup\client_cli.py", "/ST", hour + ":" + minute, "/RU", "system", "/RL", "HIGHEST"], stdout=subprocess.PIPE).communicate()[0]
    wtask_create = subprocess.Popen(["SchTasks.exe", "/create", "/SC", "DAILY", "/TN", "rPyBackup", "/TR", "C:\\rPyBackup\client_cli.py -o run", "/ST", hour + ":" + minute, "/RU", "system", "/RL", "HIGHEST"], stdout=subprocess.PIPE).communicate()[0]
    return wtask_create

def modify_windows_task(hour, minute):
    wtask_modify = subprocess.Popen(["SchTasks.exe", "/change", "/TN", "rPyBackup", "/ST", hour + ":" + minute], stdout=subprocess.PIPE).communicate()[0]
    return wtask_modify

def delete_windows_task():
    FNULL = open(os.devnull, 'w')
    wtask_delete = subprocess.Popen(["SchTasks.exe", "/Delete", "/TN", "rPyBackup", "/F"], stdout=subprocess.PIPE, stderr=FNULL).communicate()[0]
    FNULL.close()
    return wtask_delete

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
        
        ### Configuration - Hostname ###
        self.config_name_label = Label(self, text="Hostname: ").grid(column=0,row=0,sticky='EW')
        self.config_nameVariable = StringVar()
        self.config_name = Entry(self,textvariable=self.config_nameVariable)
        self.config_name.grid(column=1,row=0,sticky='EW')
        self.config_name.bind("<Return>", self.ConfigOnPressEnter)
        self.config_nameVariable.set(clientname)
        
        ### Configuration - Server ###
        self.config_server_label = Label(self, text="Server: ").grid(column=0,row=1,sticky='EW')
        self.config_serverVariable = StringVar()
        self.config_server = Entry(self,textvariable=self.config_serverVariable)
        self.config_server.grid(column=1,row=1,sticky='EW')
        self.config_server.bind("<Return>", self.ConfigOnPressEnter)
        self.config_serverVariable.set(HOST)
        
        ### Configuration - Port ###
        self.config_port_label = Label(self, text="Port: ").grid(column=0,row=2,sticky='EW')
        self.config_portVariable = StringVar()
        self.config_port = Entry(self,textvariable=self.config_portVariable)
        self.config_port.grid(column=1,row=2,sticky='EW')
        self.config_port.bind("<Return>", self.ConfigOnPressEnter)
        self.config_portVariable.set(PORT)
        
        ### Configuration - Password ###
        ### Need to add hash function, to store hash in config instead of plain text
        self.config_password_label = Label(self, text="Password: ").grid(column=0,row=3,sticky='EW')
        self.config_passwordVariable = StringVar()
        self.config_password = Entry(self,show='*',textvariable=self.config_passwordVariable)
        self.config_password.grid(column=1,row=3,sticky='EW')
        self.config_password.bind("<Return>", self.ConfigOnPressEnter)
        self.config_passwordVariable.set(password)
        
        configbutton = Button(self,text=u"Save Config",
                            command=self.ConfigOnButtonClick)
        configbutton.grid(column=1,row=8)
        
        ### Configuration - Retention ###
        self.config_retention_label = Label(self, text="Retention (Days): ").grid(column=0,row=4,sticky='EW')
        self.config_retentionVariable = StringVar()
        self.config_retention = Entry(self,textvariable=self.config_retentionVariable)
        self.config_retention.grid(column=1,row=4,sticky='EW')
        self.config_retention.bind("<Return>", self.ConfigOnPressEnter)
        self.config_retentionVariable.set(retention)
        
        ### Configuration - Task Next Run ###
        self.config_nextrun_label = Label(self, text="Next Run: ").grid(column=0,row=5,sticky='EW')
        self.config_nextrunVariable = StringVar()
        self.config_nextrun = Label(self,textvariable=self.config_nextrunVariable)
        self.config_nextrun.grid(column=1,row=5,sticky='EW')
        #self.config_nextrunVar = query_windows_task()
        self.config_nextrunVariable.set(query_windows_task())
        
        ### Configuration - Task Next Run Hour ###
        self.config_nextrunHour_label = Label(self, text="Hour: ").grid(column=0,row=6,sticky='EW')
        self.config_nextrunHourVariable = StringVar()
        self.config_nextrunHour = Entry(self,textvariable=self.config_nextrunHourVariable)
        self.config_nextrunHour.grid(column=1,row=6,sticky='EW')
        self.config_nextrun.bind("<Return>", self.ConfigOnPressEnter)
        self.config_nextrunHourVariable.set(runHour)
        
        ### Configuration - Task Next Run Minute ###
        self.config_nextrunMin_label = Label(self, text="Minute: ").grid(column=0,row=7,sticky='EW')
        self.config_nextrunMinVariable = StringVar()
        self.config_nextrunMin = Entry(self,textvariable=self.config_nextrunMinVariable)
        self.config_nextrunMin.grid(column=1,row=7,sticky='EW')
        self.config_nextrun.bind("<Return>", self.ConfigOnPressEnter)
        self.config_nextrunMinVariable.set(runMin)
        
        ### Configuration - Backup List ###
        # create the listbox (note that size is in characters)
        #task_list = Listbox(root, width=50, height=6)
        self.textPad = ScrolledText(self, width=100, height=30)
        self.task_list = Listbox(self, width=50, height=6)
        self.task_list.grid(row=8, column=4)

        # create a vertical scrollbar to the right of the listbox
        self.yscroll = Scrollbar(command=self.task_list.yview, orient=VERTICAL)
        self.yscroll.grid(row=8, column=5, sticky=N+S)
        self.task_list.configure(yscrollcommand=self.yscroll.set)
        
        ### Action - Upload ###
#        self.action_put_label = Label(self, text="File: ").grid(column=0,row=3,sticky='EW')
#        self.action_putVariable = StringVar()
#        self.action_put = Entry(self,textvariable=self.action_putVariable)
#        self.action_put.grid(column=1,row=3,sticky='EW')
#        self.action_put.bind("<Return>", self.ActionPutOnPressEnter)
#        self.action_putVariable.set(u"Enter File Name")
#        
#        action_put_button = Button(self,text=u"Upload",
#                              command=self.ActionPutOnButtonClick)
#        action_put_button.grid(column=2,row=3)

        # use entry widget to display/edit selection
        self.input = Entry(self, width=50)
        self.input.insert(0, 'Add location')
        self.input.grid(row=6, column=4)
        # pressing the enter key will update edited line
        self.input.bind('<Return>', self.set_list)
        
        self.button_enable_schedule = Button(self, text=' Enable Schedule', command=self.enable_schedule)
        self.button_enable_schedule.grid(row=5, column=3, sticky=E)
        
        self.button_disable_schedule = Button(self, text='Disable Schedule', command=self.disable_schedule)
        self.button_disable_schedule.grid(row=6, column=3, sticky=E)

        #This button is used to add tasks
        self.button_add_task = Button(self, text='  Add ', command=self.new_task)
        self.button_add_task.grid(row=5, column=4, sticky=E)

        #This Button is used to call the delete function
        self.button_delete = Button(self, text='Delete', command=self.delete_item)
        self.button_delete.grid(row=7, column=4, sticky=E)

        # left mouse click on a list item to display selection
        self.task_list.bind('<ButtonRelease-1>', self.get_list)
        
        self.grid_columnconfigure(0,weight=1)
        self.resizable(True,True)
        self.update()
        self.geometry(self.geometry())
        self.config_name.focus_set()
        self.config_name.selection_range(0, END)
        
    def update_vars(self):
        Config.read('config/config.ini')
        HOST = ConfigSectionMap("main")['server']
        PORT = int(ConfigSectionMap("main")['port'])
        clientname = ConfigSectionMap("main")['clientname']
        retention = ConfigSectionMap("main")['retention']
        password = ConfigSectionMap("main")['password']
        runHour = ConfigSectionMap("main")['runhour']
        runMin = ConfigSectionMap("main")['runmin']
        self.config_portVariable.set(PORT)
        self.config_serverVariable.set(HOST)
        self.config_nameVariable.set(clientname)
        self.config_passwordVariable.set(password)
        self.config_nextrunVariable.set(query_windows_task())
        self.config_nextrunMinVariable.set(runMin)
        self.config_nextrunHourVariable.set(runHour)
        
    def ConfigOnButtonClick(self):
        self.save_tasks()
        self.save_config()
        self.update_vars()
        self.config_name.focus_set()
        self.config_name.selection_range(0, END)

    def ConfigOnPressEnter(self,event):
        self.save_tasks()
        self.save_config()
        self.update_vars()
        self.config_name.focus_set()
        self.config_name.selection_range(0, END)
        
    def enable_schedule(self):
        create_windows_task(self.config_nextrunHour.get(), self.config_nextrunMin.get())
        self.update_vars()
    
    def disable_schedule(self):
        delete_windows_task()
        self.update_vars()
        
    def open_task(self): 
        fin = open('config/config_paths', 'a+') 
        fin.seek(0)
        if fin is not None: 
            task_listread = fin.readlines() 
        for item in task_listread: 
            self.task_list.insert(END, item) 
        fin.close()

    def exit(self):
        if tkMessageBox.askokcancel("Quit", "Do you really want to quit?"):
            self.destroy()

    def about(self):
        label = tkMessageBox.showinfo("About", "rPyBackup Configuration Utility\n\nWritten By: Daniel Foley")


    def new_task(self):
        self.task_list.insert(END, self.input.get())


    def delete_item(self):
        """
        delete a selected line from the listbox
        """
        try:
            # get selected line index
            index = self.task_list.curselection()[0]
            self.task_list.delete(index)
        except IndexError:
            pass


    def get_list(self, event):
        """
        function to read the listbox selection
        and put the result in an entry widget
        """
        # get selected line index
        index = self.task_list.curselection()[0]
        # get the line's text
        seltext = self.task_list.get(index)
        # delete previous text in input
        self.input.delete(0, 50)
        # now display the selected text
        self.input.insert(0, seltext)

    def set_list(self, event):
        """
        insert an edited line from the entry widget
        back into the listbox
        """
        try:
            index = self.task_list.curselection()[0]
            # delete old listbox line
            self.task_list.delete(index)
        except IndexError:
            index = END
            # insert edited item back into task_list at index
            self.task_list.insert(index, self.input.get())


    def save_tasks(self):
        """
        save the current listbox contents to a file
        """
        # get a list of listbox lines
        temp_list = list(self.task_list.get(0, END))
        # add a trailing newline char to each line, but remove extisting so not to duplicate newlines
        temp_list = [task.strip() + '\n' for task in temp_list]
        if temp_list is not None:
            fout = open('config/config_paths', 'w')
            fout.writelines(temp_list)
            fout.close()
#        with open('config_paths','r+') as f:
#            for line in f:
#                if not line.isspace():
#                    f.write(line)
#            f.close()
        
    def save_config(self):
        cfgfile = open('config/config.ini', 'w')
        Config.set('main', 'server', self.config_server.get())
        Config.set('main', 'port', self.config_port.get())
        Config.set('main', 'clientname', self.config_name.get())
        Config.set('main', 'retention', self.config_retention.get())
        Config.set('main', 'runHour', self.config_nextrunHour.get())
        Config.set('main', 'runMin', self.config_nextrunMin.get())
        Config.set('main', 'password', self.config_password.get())
        Config.write(cfgfile)
        cfgfile.close()
        
####### Action Functions #######

    
if __name__ == "__main__":
    ### OS Type Check - Now only Windows is configured ###
    # Issue / Bug during privilege escalation where two instances are spawned
    # Fix 
    if ostype == 'Windows':
        if not admin.isUserAdmin():
            admin.runAsAdmin(wait=True)
    else:
        pass
    app = backup_gui(None)
    app.title('rPyBackup Configuration')
    
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