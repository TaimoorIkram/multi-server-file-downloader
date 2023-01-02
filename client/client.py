import socket
import time
import argparse

parser = argparse.ArgumentParser()

parser.add_argument('-i', '--metric_interval', help="Time interval in seconds between metric reporting", type=int, default=2)
parser.add_argument('-o', '--output_location', help="Time interval in seconds between metric reporting", default="Received.mp4")
parser.add_argument('-a', '--server_ip_address', help="IP address of server", default=socket.gethostbyname(socket.gethostname()))
parser.add_argument('-p', '--list_of_ports', nargs='+', help="List of port numbers (one for each server)")
parser.add_argument('-r', '--resumebool', help="Whether to resume the existing download in progress", default=0)
args = parser.parse_args()

FORMAT = 'utf-8'
PORTS = args.list_of_ports   # List of ports that user enters 
PORTS = list(map(int, PORTS)) # Creates int list of ports from a string one. For example ['2048', '4096', '6666'] changes to [2048, 4096, 6666] after list(map()) function.
INTERVAL = args.metric_interval # Time interval for refreshing the CLI
RESUMEBOOL = args.resumebool # Time interval for refreshing the CLI
FILE_LOC = args.output_location # Location where the file will be stored.
HOST = args.server_ip_address # IP address of the server
DIVISIONS = 20    # The number of packets in which a segement is divided at the server side
BACKUP_LOC = 'backupBytes.txt'
BACKUP_LOC_BYTESTREAM = 'backupByteStream.txt'

# IP = socket.gethostbyname(socket.gethostname())  # For Local Machine
IP = '10.7.49.208'     # IP Address of Server
PORT = PORTS           
ADDRS = [(IP,PORT[i]) for i in range(len(PORTS))]   # Stores the tuples of IP address of server and the PORT used for conection.
SIZE = 1024

serversRequested = 0
dataSegmentNumbers = [] # Data Segment Numbers sent by the particular server.
dataBytes = []  # Bytes of Data Sent by the Server

def main(serverid):
    """
    Connects the Client with the Specified Server Port
    serverid: The server number to which a client is to be conencted
    Also receives the segment of data form the server
    """
    client = socket.socket(socket.AF_INET,socket.SOCK_STREAM)
    client.connect(ADDRS[serverid])
    
    file_size = client.recv(SIZE).decode(FORMAT)

    ## Now receiving file(mp4) from server
    dataCount = 0    # Count For Receiving the correct amount of data from server
    dataInSegment = b''    # Stores the data bytes of a segment
    segment = serverid     # Indicates the Server sending the segment
    start_time = time.time()

    ## Now receiving file chuncks of data 
    client.send(str(segment).encode(FORMAT))
    client.recv(1)
    
    while dataCount <= int(file_size)/len(PORTS):   # Runs While Loop Till the Data of the segment is fully received
        data = client.recv(SIZE) 
        ## Here no need for decode Format because we have opened our file by 'wb' format
        if not (data):
            break
        dataCount+=len(data)
        dataInSegment += data
    dataSegmentNumbers.append(serverid)
    dataBytes.append(dataInSegment)

    try:
        while(True):
            dataBytes.remove(b'')
    except: pass

    end_time = time.time()
    print("\n[COMPLETED] File transfer completed Total Time : ", end_time - start_time)

    client.close()  # Closing Connection 

def loadBackup():
    """
    Returns the Segement Numbers received Correctly
    """
    try:
        with open(BACKUP_LOC, 'r') as backupFile:
            backupSegments = backupFile.read().split(',')
            backupSegments.remove('')
            return [int(value) for value in backupSegments]
    except: return

def loadBytes():
    """
    Returns the bytes of data of each segment as an array
    """
    try:
        with open(BACKUP_LOC_BYTESTREAM, 'rb') as backupFile:
            backupSegmentsData = backupFile.read().split(b'DELIMITER')
            try:
                while(True):
                    backupSegmentsData.remove(b'')
            except: pass
            return [bytes(value) for value in backupSegmentsData]
    except: return

def saveBackup():
    """
    Creates 2 files 'backupBytes.txt' and 'backupBytesStarem.txt' used for saving the backups.
    """
    with open(BACKUP_LOC, 'w') as backupFile:  # It writes the segment numbers received correctly in a BACK_LOC file
        for i in dataSegmentNumbers:
            backupFile.write(str(i) + ',')
    with open(BACKUP_LOC_BYTESTREAM, 'wb') as backupByteFile: # It writes the data received correctly in a BACK_LOC file
        for dataByte in dataBytes:
            backupByteFile.write(dataByte)
            backupByteFile.write(bytes(b'DELIMITER'))
        
def resume():
    """
    Requests the server to send the remaining segment of data not received at first
    """
    totalSegments = [-1] * len(PORTS)
    totalData = [b''] * len(PORTS)
    downloadedBytes = loadBytes()
    downloadedSegments = loadBackup()

    for i in range(len(downloadedSegments)):
        totalSegments[downloadedSegments[i]] = downloadedSegments[i]
        totalData[downloadedSegments[i]] = downloadedBytes[i]
    
    global dataBytes
    dataBytes = totalData

    for i in range(len(dataBytes)):
        if(dataBytes[i] == b''):
            print('Requesting server ' + str(i))
            main(i)

if __name__ == '__main__':
    if(RESUMEBOOL == '1'):  # Runs when -r 1 is set in CMD
        resume()
    else:
        for servernumber in range(len(PORTS)):
            try: main(servernumber)
            except: pass
    saveBackup()

if(len(dataBytes) >= len(PORTS)): # Makes the output file when all segments of data are received successfully.
    with open(FILE_LOC, 'wb') as outFile:
        for data in dataBytes:
            outFile.write(data)
else:
    print('[ERROR]\tMissing elements: download halted. Continue using the \'-r\' attribute.') 