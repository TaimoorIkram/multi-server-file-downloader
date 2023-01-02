import socket
import os
import time
import argparse
import threading

FORMAT = 'utf-8' # Format in which a file is encoded. This format works for .txt, .mp4 file extensions.
SIZE = 1024 # The size of the packets sent over the TCP conneciton, could be smaller, if the router fragments it based on some other smaller MTU.
PORTS_AVAILABLE = [4455, 4456, 4457, 4458, 4459, 4460] # Total ports availble to the server for listening clients. Each port number paired with the machine's IP gives a separate server.

packets = 20

def log(logtype, message):
    """
    Prints out a log message on screen.
    logtype: type of the message i.e. connection, activation, disconnection etc.
    message: the message to be shown on log.
    """

    LOG_TYPES = ['[STARTING]', '[ACTIVE]', '[CONNECTED]', '[DISCONNECTED]', '[SENT]', '[ERROR]' ,'[INFO]'] # Statuses
    print(LOG_TYPES[logtype] + '\t' + message)

def fragment(string, parts):
    """Divides the input string of bytes into "parts" parts.
    string: The byte string to be divided
    parts: Number of parts in which the string is to be divided
    """
    k, m = divmod(len(string), parts)
    return (string[i * k + min(i, m):(i + 1) * k + min(i + 1, m)] for i in range(parts))

def makeserver(status, servernumber):
    """
    Create the server.
    servernumber: based on the number of servers created (0, 1, 2, ...) increases linearly
    """

    # IP = '10.7.81.13' # The IP of the server machine
    # IP = socket.gethostbyname(socket.gethostname()) # For file transfer on a local machine.
    IP = '10.7.49.208' # For file transfer over the internet. Use your device's IP here. Use 'ipconfig' in command prompt for more details on your IP.
    PORT = PORTS_AVAILABLE[servernumber]

    ADDR = (IP,PORT)

    global server_sockets
    server_sockets = []

    log(0, f'Server {servernumber} is starting.')
    server = socket.socket(socket.AF_INET,socket.SOCK_STREAM) # AF_INET for IPv4, SOCK-STREAM for TCP socket, use SOCK_DGRAM for UDP socket.
    server_sockets.append(server) # Append the server socket just made into the array of server sockets.
    

    server_sockets[servernumber].bind(ADDR)
    server_sockets[servernumber].listen()
    log(1, f"Server {servernumber} is active.")

    while True:
        conn, addr = server_sockets[servernumber].accept()
        log(2, f"{addr} connected.")

        ## Sending file(mp4) to the client
        
        # Getting information of the file to be sent
        file_name = file_location
        file_size = os.path.getsize(file_name)

        # Send the file details to the client
        with open(file_name, "rb") as file:
            # conn.send(file_name.encode(FORMAT))
            conn.send(str(file_size).encode(FORMAT))

            data = file.read(file_size)
            
            s = (int(conn.recv(1024))) # Receive the segment number to send from a particular server.

            segments_gen = fragment(data, totalservers) # Fragment the data into available servers.
            segments = [] # Array that contains data to be sent from each server, based on index (0 index has the data to be sent by server 0 and so on).
            for k in segments_gen: # Injection of the data into the segements[] array
                segments.append(k)

            sub_segments_gen = fragment(segments[s], packets) # Divide the segments further into about 20 packets.
            sub_segments = [] # Array that contains subsegments (parts of segment) for every serever (separate array for every server).
            for k in sub_segments_gen:
                sub_segments.append(k)
            seg_num = str(s).encode()
            conn.send(seg_num) # Sending the segment number requested by client.

            for i in range(packets): # Sending the subsegments to the client.
                conn.sendall(sub_segments[i])

        conn.close()
        log(3, f"{addr} has disconnected.")
    
def closeserver(closestring):
    """
    Closes the server according to the command in closestring.
    closestring: the string that initiates server closing process. like 'k0' for server 0
    """
    server_status[int(closestring[1:2])] = False # For instance [True, True, True] --> [False, True, True] for 'kli 0'
    server_sockets[int(closestring[1:2])].close() # For instance [active, active, active] --> [inactive, active, active] for 'kil 0'

def main(status, servercount):
    for servernumber in range(servercount):
        serverthread = threading.Thread(target=makeserver, args=(status, servernumber))
        serverthread.start()

def refresh():
    """
    Refreshes the status of server
    """
    while True:
        time.sleep(interval)
        clrscr()
        for i in range(totalservers):
            print(
                log(6, f"Server {i}\tPort: {PORTS_AVAILABLE[i]} Status: {server_status[i]}, to shutdwon server {i}, type 'k{i}' "))

def clrscr():
    """
    Clear Console Screen
    """
    os.system('cls' if os.name == 'nt' else 'clear')

parser = argparse.ArgumentParser()

# adding parameters
parser.add_argument('-i', '--status_interval', help="Time interval in seconds between server status reporting.", type=int, default=2)
parser.add_argument('-n', '--num_servers', help="Total number of virtual servers.", type=int)
parser.add_argument('-f', '--file_location', help="Address pointing to the file location.", default="to_be_sent.mp4")
parser.add_argument('-p', '--list_of_ports', nargs='+',
                    help="List of port numbers(‘n’ port numbers, one for each server).", type=int, metavar="port_list", default=PORTS_AVAILABLE)
args = parser.parse_args()

interval = args.status_interval # Time interval between refreshes (seconds).
totalservers = args.num_servers # Total number of the servers.
file_location = args.file_location # Location of the file to be sent.
PORTS_AVAILABLE = args.list_of_ports # Changes the list of ports to the list of ports assigned by the user.
server_status = [True] * totalservers # Defines an array of boolean values, where true means the server is running.
server_threads = []

for portnumber in PORTS_AVAILABLE:
    if portnumber < 1024:
        log(5, 'Invalid port number.')
        exit()

if __name__ == '__main__':
    main(server_status, totalservers)

outputThread = threading.Thread(target=refresh)
outputThread.start()
while True:
    command = input()
    closeserver(command)
    print(command) 