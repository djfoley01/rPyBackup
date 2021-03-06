import socket, ssl
import thread
import logging
import os
import struct
import ConfigParser
import hashlib

HOST = '0.0.0.0'                 
PORT = 3820

logging.basicConfig(filename='rPyBackup.log', level=logging.INFO, format='%(asctime)s %(message)s')

Config = ConfigParser.ConfigParser()
socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
socket.bind((HOST, PORT))
                    
def hashfile(afile, hasher, blocksize=65536):
    buf = afile.read(blocksize)
    while len(buf) > 0:
        hasher.update(buf)
        buf = afile.read(blocksize)
    return hasher.digest()

def ensure_dir(path):
    directory_path = os.path.dirname(path)
    if not os.path.exists(directory_path):
        os.makedirs(directory_path)
        
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

def save_config(auth_string):
    string = auth_string.split(' ', 2)
    cli_clientname = string[0] + "." + string[2] + ".name"
    cli_retention = string[0] + "." + string[2] + ".rete"
    cli_password = string[0] + "." + string[2] + ".pass"
    cfgfile = open('config.ini', 'w')
    Config.set('clients', cli_clientname, string[0])
    Config.set('clients', cli_retention, string[1])
    Config.set('clients', cli_password, string[2])
    Config.write(cfgfile)
    cfgfile.close()
    logging.info("Config changed / saved ...")
    return

### Not Really authentication - Just ensures if the hostname & password (Not really a password) 
### do not match, then create a new "client" configuration and create directory to put and get files from.
def auth_client(auth_string):
    string = auth_string.split(' ', 2)
    cli_clientname = string[0] + "." + string[2] + ".name"
    cli_retention = string[0] + "." + string[2] + ".rete"
    cli_password = string[0] + "." + string[2] + ".pass"
    Config.read('config.ini')
    try:
        auth_name = ConfigSectionMap("clients")[cli_clientname]
    except:
        save_config(auth_string)
        logging.info("Creating Client: " + string[0] + "." + string[2])
        return cli_clientname
    try:
        auth_ret = ConfigSectionMap("clients")[cli_retention]
    except:
        save_config(auth_string)
    try:
        auth_pass = ConfigSectionMap("clients")[cli_password]
    except:
        save_config(auth_string)
    return cli_clientname
        
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

def on_new_client(socketc,addr):
    try:
        clientsocket = ssl.wrap_socket(socketc, server_side=True,certfile="sslcerts/server.crt",keyfile="sslcerts/server.key")
    except:
        socketc.close()
        return
    logging.info('New client connected .. ' + str(addr))
    auth_client_string = recv_one_message(clientsocket)
    cpath = auth_client(auth_client_string)
    client_path = cpath.strip()[:-5]
    reqCommand = recv_one_message(clientsocket)
    logging.info("Client: " + client_path + " Command: " + reqCommand)
    if not reqCommand:
        pass
    else:
        string = reqCommand.split(' ', 2)   #in case of 'put' and 'get' method
        reqFile = "data/" + client_path + "/" + string[2] 
        ensure_dir(reqFile)
        if (string[1] == 'put'):
            inc_file_hash = recv_one_message(clientsocket)
            file_size = int(clientsocket.recv(16))
            logging.info("Client: " + client_path + " uploading file: " + string[2])
            logging.info("Client: " + client_path + " received file hash: " + inc_file_hash)
            recvd = ''
            with open(reqFile, 'wb') as file_to_write:
                while file_size > len(recvd):
                    data = clientsocket.recv(8192)
                    if not data:
                        break
                    recvd += data
                    file_to_write.write(data)
                
            file_to_write.close()
            file_hash = hashfile(open(reqFile, 'rb'), hashlib.sha256())
            logging.info("Client: " + client_path + " confirmed file hash: " + file_hash)
            if inc_file_hash == file_hash:
                send_one_message(clientsocket, 'From Server: Receive Successful')
                logging.info("Client: " + client_path + " upload successful: " + string[2])
            else:
                send_one_message(clientsocket, 'From Server: Receive Failed - Hashes do not match')
                logging.error("Client: " + client_path + " upload failed: " + string[2])
                
        elif (string[1] == 'get'):
            logging.info("Client: " + client_path + " downloading file: " + string[2])
            file_hash = hashfile(open(reqFile, 'rb'), hashlib.sha256())
            send_one_message(clientsocket, file_hash)
            logging.info("Client: " + client_path + " sent file hash: " + file_hash)
            with open(reqFile, 'rb') as file_to_send:
                data = file_to_send.read()
                clientsocket.sendall('%16d' % len(data))
                clientsocket.sendall(data)
            #print recv_one_message(clientsocket)
            logging.info("Client: " + client_path + " download confirm: " + recv_one_message(clientsocket))
        elif (string[1] == 'ls'):
            logging.info("Client: " + client_path + " sending file list")
            full_path = os.getcwd() + "/data/" + client_path
            listdir = '\n'.join(os.listdir(full_path))
            send_one_message(clientsocket, listdir)
        
    logging.info("Client: " + client_path + " Connection Closed")
    clientsocket.close()
    socketc.close()

socket.listen(5)
while True:
    conn, addr = socket.accept()
    thread.start_new_thread(on_new_client,(conn, addr))
socket.close()