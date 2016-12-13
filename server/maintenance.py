import os, time, logging
import schedule
from time import sleep
from datetime import datetime
from OpenSSL import crypto
import ConfigParser

logging.basicConfig(filename='rPyBackup_maint.log', level=logging.INFO, format='%(asctime)s %(message)s')
Config = ConfigParser.ConfigParser()

def server_checks():
    print "Server Checks"
    check_ssl_cert()
    prune_files()
    
def check_ssl_cert():
    currentDate = datetime.utcnow()
    cert = crypto.load_certificate(crypto.FILETYPE_PEM, file('sslcerts/server.crt').read())
    expDate = datetime.strptime(cert.get_notAfter(),'%Y%m%d%H%M%SZ')
    delta = expDate - currentDate
    logging.info("SSL Certificate Expires in: " + str(delta.days) + "days")

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

def prune_files():
    now = time.time()
    logging.info("Prune Job Started")
    with open('config.ini', 'r') as fin:
        lines=[]
        for line in fin:
            string = line.split(' ', 2)
            if string[0].strip() != '[clients]':
                if string[0].strip() != '':
                    newline = string[0].strip()[:-5]
                    lines.append(newline)
    for directory in list(set(lines)):
        Config.read('config.ini')
        confread = directory + ".rete"
        retention_period = ConfigSectionMap("clients")[confread]
#        print directory + " retention: " + retention_period
        full_path = os.getcwd() + "/data/" + directory
        for f in os.listdir(full_path):
#            print f + " " + str(os.stat(os.path.join(full_path,f)).st_mtime)
            if os.stat(os.path.join(full_path,f)).st_mtime < now - int(retention_period) * 86400:
                file_path = "data/" + directory + "/" + f
                if os.path.isfile(file_path):
                    os.remove(file_path)
                    logging.info(file_path + " file removed; Older than " + retention_period)
                    print file_path + " file removed; Older than " + retention_period
                else:
                    print "Cound not find " + file_path + " to remove due to retention breach"
                    logging.error("Cound not find " + file_path + " to remove due to retention breach")
    logging.info("Prune Job Complete")
    
def server_runtime():
    while True:
        schedule.run_pending()
        sleep(1)
        
schedule.every().day.at("01:30").do(server_checks)

server_runtime()