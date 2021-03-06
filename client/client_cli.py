import socket, ssl
import ConfigParser
import sys
import getopt
import struct
import os
import hashlib
import datetime
import tarfile
import time
#HOST = 'localhost'    # server name goes in here
#PORT = 3820
def retrieve_config():
    server_string = clientname + " " + retention + " " + password
    print "Sending Config.. "
    return server_string

def hashfile(afile, hasher, blocksize=65536):
    buf = afile.read(blocksize)
    while len(buf) > 0:
        hasher.update(buf)
        buf = afile.read(blocksize)
    return hasher.digest()

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

def send_one_message(sock, data):
    length = len(data)
    sock.sendall(struct.pack('!I', length))
    sock.sendall(data)
    
def recv_one_message(sock):
    lengthbuf = recvall(sock, 4)
    length, = struct.unpack('!I', lengthbuf)
    return recvall(sock, length)

def recvall(sock, count):
    buf = b''
    while count:
        newbuf = sock.recv(count)
        if not newbuf: 
            return None
        buf += newbuf
        count -= len(newbuf)
    return buf

def put(commandName):
    s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    socket1 = ssl.wrap_socket(s,ca_certs='config/sslcerts/server.crt',cert_reqs=ssl.CERT_REQUIRED)
    socket1.connect((HOST, PORT))
    send_one_message(socket1, retrieve_config())
    send_one_message(socket1, commandName)
    string = commandName.split(' ', 2)
    inputFile = string[2]
    file_hash = hashfile(open(inputFile, 'rb'), hashlib.sha256())
    send_one_message(socket1, file_hash)
    with open(inputFile, 'rb') as file_to_send:
        data = file_to_send.read()
    socket1.sendall('%16d' % len(data))
    socket1.sendall(data)
    print 'PUT Successful'
    print recv_one_message(socket1)
    socket1.close()
    return


def get(commandName):
    s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    socket1 = ssl.wrap_socket(s,ca_certs='config/sslcerts/server.crt',cert_reqs=ssl.CERT_REQUIRED)
    socket1.connect((HOST, PORT))
    send_one_message(socket1, retrieve_config())
    send_one_message(socket1, commandName)
    string = commandName.split(' ', 2)
    inputFile = string[2]
    inc_file_hash = recv_one_message(socket1)
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
    file_hash = hashfile(open(inputFile, 'rb'), hashlib.sha256())
    if inc_file_hash == file_hash:
        print "Receive Successfull - Hashes Match"
        send_one_message(socket1, "Receive Success - Hashes Match")
    else:
        print "Received Failed - Hashes Do Not Match"
        send_one_message(socket1, "Receive Failed - Hashes Do Not Match")
    print 'GET Complete'
    socket1.close()
    return

def remote_list(clientname):
    s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    socket1 = ssl.wrap_socket(s,ca_certs='config/sslcerts/server.crt',cert_reqs=ssl.CERT_REQUIRED)
    socket1.connect((HOST, PORT))
    send_one_message(socket1, retrieve_config())
    print "Remote Files:"
    commandName = clientname + " ls nofile"
    send_one_message(socket1, commandName)
    rlist = recv_one_message(socket1)
    print rlist
    socket1.close()
    return

def make_tarfile(output_filename, source_dir_list):
    with tarfile.open(output_filename, "w:gz") as tar:
        for source_dir in source_dir_list:
            tar.add(source_dir, arcname=os.path.basename(source_dir))
        tar.close()
        
def make_inctarfile(output_filename, source_dir_list, lastrun):
    now = time.time()
    out = tarfile.open(output_filename, mode='w:gz')

    # start walk via all files to find changed since lastrun
    for dir_to_backup in source_dir_list:
        for root, dirs, files in  os.walk(dir_to_backup, followlinks=True):
            for file in files:
                file = os.path.join(root, file)
                try:
                    filemodtime = os.path.getmtime(file)
                    if filemodtime > float(lastrun):
                        if os.path.isfile(file):
                            print('Adding file: %s...' % file)
                            out.add(file)
                            print('File modified: %s' % time.ctime(os.path.getmtime(file)))
                except OSError as error:
                    print('ERROR: %s' % error)

    print 'Closing archive.'
    out.close()
    
def delete_tarfile(filename):
    print filename
    if os.path.isfile(filename):
        try:
            os.remove(filename)
            print "Successfully removed temporary file"
        except:
            print "Unable to delete temporary file"
    else:
        print "Temporary file not found"
        
def run_configured_backup(clientname):
    data = [line.strip() for line in open("config/config_paths", 'r')]
    fname = clientname
    fmt = "%Y-%m-%d_FullBackup_" + clientname + ".tar.gz"
    output_fname = datetime.datetime.now().strftime(fmt).format(fname)
    make_tarfile(output_fname, data)
    cmd = clientname + " put " + output_fname
    put(cmd)
    delete_tarfile(output_fname)
    set_lastrun()
    
def inc_backup(clientname):
    data = [line.strip() for line in open("config/config_paths", 'r')]
    fname = clientname
    fmt = "%Y-%m-%d_IncrementalBackup_" + clientname + ".tar.gz"
    output_fname = datetime.datetime.now().strftime(fmt).format(fname)
    make_inctarfile(output_fname, data, lastrun)
    cmd = clientname + " put " + output_fname
    put(cmd)
    delete_tarfile(output_fname)
    set_lastrun()
#    print('Creating archive %s...' % backupname)

def set_lastrun():
    now = time.time()
    cfgfile = open('config/config.ini', 'w')
    Config.set('main', 'lastrun', now)
    Config.write(cfgfile)
    cfgfile.close()
    
Config = ConfigParser.ConfigParser()
Config.read('config/config.ini')
HOST = ConfigSectionMap("main")['server']
PORT = int(ConfigSectionMap("main")['port'])
clientname = ConfigSectionMap("main")['clientname']
retention = ConfigSectionMap("main")['retention']
password = ConfigSectionMap("main")['password']
lastrun = ConfigSectionMap("main")['lastrun']

def main(argv):
    opt_arg = ''
    filename = ''
    try:
        opts, args = getopt.getopt(argv,"ho:f:",["option=","file="])
    except getopt.GetoptError:
        print 'client_cli.py -o <option> -f <filename>'
        print 'Available Options: '
        print 'run - Run Full Backup using configuration'
        print 'run_inc - Run Incremental Backup using configuration'
        print 'put - send file'
        print 'get - retrieves file'
        print 'list - lists local directory'
        print 'rlist - shows available files'
        sys.exit(2)
    for opt, arg in opts:
        if opt == '-h':
            print 'client_cli.py -o <option> -f <filename>'
            print 'Available Options:'
            print 'run - Run Full Backup using configuration'
            print 'run_inc - Run Incremental Backup using configuration'
            print 'put - send file'
            print 'get - retrieves file'
            print 'list - lists local directory'
            print 'rlist - shows remote files'
            sys.exit()
        elif opt in ("-o", "--option"):
            opt_arg = arg
        elif opt in ("-f", "--file"):
            filename = arg
    inputCommand = opt_arg + " " + filename
    string = inputCommand.split(' ', 1)
    inputCommand = clientname + " " + inputCommand
    if (string[0] == 'put'):
        put(inputCommand)
    elif (string[0] == 'get'):
        get(inputCommand)
    elif (string[0] == 'list'):
        print os.getcwd()
        print '\n'.join(os.listdir(os.getcwd()))
    elif (string[0] == 'rlist'):
        remote_list(clientname)
    elif (string[0] == 'run'):
        run_configured_backup(clientname)
    elif (string[0] == 'run_inc'):
        inc_backup(clientname)

if __name__ == "__main__":
    main(sys.argv[1:])