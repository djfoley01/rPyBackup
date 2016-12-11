import subprocess
import admin
import platform
import xml.etree.cElementTree as ET
from crontab import CronTab

ostype = platform.system()

if ostype == 'Windows':
    if not admin.isUserAdmin():
        admin.runAsAdmin()
else:
    pass

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
    wtask_create = subprocess.Popen(["SchTasks.exe", "/create", "/SC", "DAILY", "/TN", "rPyBackup", "/TR", "C:\rPyBackup\client_cli.py", "/ST", hour + ":" + minute], stdout=subprocess.PIPE).communicate()[0]
    return wtask_create

def modify_windows_task(hour, minute):
    wtask_modify = subprocess.Popen(["SchTasks.exe", "/change", "/TN", "rPyBackup", "/ST", hour + ":" + minute], stdout=subprocess.PIPE).communicate()[0]
    return wtask_modify

def delete_windows_task(name):
    wtask_delete = subprocess.Popen(["SchTasks.exe", "/Delete", "/TN", name, "/F"], stdout=subprocess.PIPE).communicate()[0]
    return wtask_delete

wtname = "rPyBackup"
hour = "17"
minute = "00"

#if ostype == 'Windows':
#    print "Windows"
print query_windows_task()
    #print create_windows_task(hour, minute)
#print modify_windows_task(hour, minute)
#print delete_windows_task(wtname)
#else:
#    print "Linux"



def create_linux_cron():
    tab = CronTab(user='root')
    cmd = '/var/www/pjr-env/bin/python /var/www/PRJ/job.py'
    cron_job = tab.new(cmd)
    cron_job.minute().on(0)
    cron_job.hour().on(0)
    #writes content to crontab
    tab.write()
    print tab.render()