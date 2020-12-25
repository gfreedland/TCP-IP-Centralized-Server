#######################################################################
# File:             server.py
# Author:           George Freedland
# Purpose:          CSC645 Assigment #1 TCP socket programming
# Description:      Template server class.
# Running:          Python 2: python server.py
#                   Python 3: python3 server.py
#                   Note: Must run the server before the client.
########################################################################

from builtins import object
import socket
from threading import Thread, activeCount
# import threading
import pickle
from client_handler import ClientHandler

# 192.168.56.1 Ethernet adapter VirtualBox Host-Only Network

PORT = 12000
SERVER = socket.gethostbyname(socket.gethostname())
ADDR = (SERVER, PORT)
HEADER = 4096


class Server(object):

    MAX_NUM_CONN = 10  # keeps 10 clients in queue

    # GENERAL SERVER INITIALIZATION - init local variables, create and bind socket.
    def __init__(self, ip_address=SERVER, port=PORT):
        self.host = ip_address
        self.port = port
        self.numOfClients = 0
        self.connected = True
        self.clientName = None
        self.clientRequest = None
        # dictionary of clients handlers objects handling clients. format {clientid:connobject}
        self.clientHandlerObjects = {}
        # dictionary of client names. format {clientid:clientName}
        self.clientNames = {}
        # Format: {who it was sent to:(messagecontent:sentfrom)}
        self.unreadMessages = []
        # Dictionary that holds open chatRooms.
        self.chatRooms = {}

        # create an INET, STREAMing socket
        try:
            self.serversocket = socket.socket(
                socket.AF_INET, socket.SOCK_STREAM)
        except socket.error:
            print('Error creating socket.')

        # bind the socket to a public host, and a well-known port
        try:
            self.serversocket.bind((ip_address, port))
        except socket.error:
            print('Error binding server to ip and port')
            self.serversocket.close()

    # Thread Starts
    def threaded_handle_client(self, conn, addr):
        # On init this sets up variables in ClientHandler.
        # Also sends ID, gets Name then sends Ok
        client_handler = ClientHandler(self, conn, addr)
        print("~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~")
        print(f"NEW CONNECTION from {addr} had been established!")
        print(f"Active Connections/Threads Running: {activeCount() - 1}")
        print("~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~")

        # Main recieve loop determines what to do based on the 'type'
        while self.connected:
            try:
                message = self.receive(conn)
                self.clientRequest = message  # Sets globally so client handler can use
            except socket.error:
                self.numOfClients -= 1
                print("~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~")
                print(
                    f"{self.clientNames[addr[1]]} has disconnected from the server.")
                print("~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~")
                break

            # Give some data about the incoming message
            print("~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~")
            print(
                # f"Incoming message from {addr}\nMessage Header: {message['header']}\nMessage Type: {message['type']}\nMessage Content: {message['content']}")
                f"Incoming message from {addr}\nMessage Header: {message['header']}\nMessage Type: {message['type']}")
            print("~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~")

            # Handle get menu request
            if message['type'] == "GET" and message['content'] == "MENU":
                print("~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~")
                print(f"Sending menu to {addr}...")
                client_handler._sendMenu()
                print("~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~")

            # Handle menu option select
            if message['type'] == "MENUOPTION":
                print("~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~")
                print(
                    f"Handle menu request {message['menuOption']} from {addr}...")
                print("~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~")
                client_handler.process_options()
                if message['menuOption'] == 6:
                    self.numOfClients -= 1
                    break

        # Runs clear/close on client connection
        self.clientNames.pop(addr[1])  # Removes from clientNames
        self.clientHandlerObjects[addr[1]].close()  # Closed connection
        self.clientHandlerObjects.pop(addr[1])  # Removes connection

    # Listens to new clients and sets max clients to MAX_NUM_CONN
    def _listen(self):
        try:
            self.serversocket.listen(1)
            print('Listening at ', SERVER, '/', self.port)
        except socket.error:
            print('Error binding server to ip and port')
            self.serversocket.close()

    # Runs a loop running serversocket.accept to fetch client info and assign a thread to it.
    def _accept_clients(self):
        while True:
            print(f"Num of clients: {self.numOfClients}")
            try:
                conn, addr = self.serversocket.accept()
                self.numOfClients += 1
                if self.numOfClients <= self.MAX_NUM_CONN:
                    Thread(target=self.threaded_handle_client, args=(
                        conn, addr)).start()
                else:
                    response = {
                        'header': HEADER,
                        'type': "NO",
                        'content': None
                    }
                    self.numOfClients -= 1
                    print("A client is trying to connect but the server is full.")
                    self.send(conn, response)

            except socket.error:
                print('Error establishing connection with client')
                break

    # Serializes dictionary with pickle and send to client.
    def send(self, conn, data):
        serializedData = pickle.dumps(data)
        conn.send(serializedData)

   # Receives serliazed data with MAX_BUFFER_SIZE limit
   # deserializes the data into a dictionary with pickle.
   # Returns
    def receive(self, conn, MAX_BUFFER_SIZE=4096):
        raw_data = conn.recv(MAX_BUFFER_SIZE)
        return pickle.loads(raw_data)

    # Sends the client id and waits for a HELLO name send.
    def sendClientId(self, conn, id):
        request = {
            'header': 4096,
            'type': "HELLO",
            'content': id
        }
        self.send(conn, request)

    # Recieves the client's Name
    def receiveClientName(self, conn, id):
        data = self.receive(conn)
        if data['type'] == "HELLO":
            self.clientNames[id] = data['content']

    # Send ok to client
    def sendOk(self, conn):
        request = {
            'header': 4096,
            'type': "OK",
            'content': None
        }
        self.send(conn, request)

    # Main driver after init
    def run(self):
        self._listen()
        self._accept_clients()


# File Startes here.
if __name__ == '__main__':
    print('Server is starting....')
    server = Server()
    server.run()
