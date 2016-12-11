# rPyBackup 

### Usage:
client_cli.py -o \[option\] -f \[filename\]
 * Available Options:
 * run - Run Backup using configuration \(Not completely implemented yet\)
 * put - send file
 * get - retrieves file
 * list - lists local directory
 * rlist - shows available files

### config_gui 
 - Intentions are to run cross platform, windows currently functional. however requires windows libraries and I still need to seperate functions based on OS type
 - requires packages / libraries in 'client/additional-python-packages'

### client_cli 
- Right now the 'run' option does not upload the file, but it does create the compressed tar file
- The send / receive speeds depend almost entirely on the buffer size during receiving
- To tune transfer speeds, modify the buffer size in the 'get' function in client_cli.py (data = socket1.recv(8192)) and the 'put' function in server.py (data = clientsocket.recv(8192))  
 - 1048576 is 1k best for large files 1g+
 - 524288 is for 500 bytes good for medium to large files
- Client hashes the file before transfer and sends hash to server, once server receives whole file it hashes again then compares to ensure success
		     
### server     
- Server accepts all connections with correct initial message being sent
- will update it's config file with client information for retention period 
  (actual pruning not implemented yet), hostname and password
- will not allow a client with different hostname / password to access other clients data
- Server is multi-threaded and will spawn new threads to allow for multiple client connections
- Similar to the client_cli, the server hashes files before and after sending or receiving to ensure successful transfers

#### TODO config_gui:
 - seperate functions based on OS Type, only load necessary libraries based on OS
 - Windows Task Scheduler functions work, however the cron functions have not been written yet
 - the 'admin' library to escalate privileges in windows spawns a completely new instance
 	- either need to change to only escalate privileges of the actual windows commands
 	  or figure a method of opening ONLY one escalated instance
 - create hash of password to store in configuration file instead of plain text

#### TODO client_cli:
 - Update run option to also transfer file
 - Make buffer size, auto scale for different file sizes to improve performance without modification to code
 - Configure logging
 
#### TODO server:
 - Encrypt socket connections
 - Enable file pruning based on configured retention periods
 - Configure actual authentication to only allow connections from proper clients
 - Create management interface
 - Create start scripts for linux (systemd and init.d)
 - Eventually enable delta backups
 - Configure logging
 
#### TODO all:
 - Create backup / restore gui
 - Across the board I need to work on better exception handling
 - Configure logging for client and server
  

Project By: Daniel Foley <daniel@foley.life>