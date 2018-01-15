#!/usr/bin/env python

import logging
import socket
import threading
from select import select

defaults = { "ip": "0.0.0.0",
             "port": 8888,
             "channel": "lobby",
             "maxconn": 128,
             "bufsize": 4096,
             "valid_commands": ['name'] }

logging.basicConfig(format='%(asctime)s (%(levelname)s): %(message)s', 
                    level=logging.INFO,
                    datefmt='%d.%m.%Y-%H:%M')
log = logging.getLogger(__name__)

class ChatServer:

    def __init__(self):
        self.server_socket = socket.socket()
        self.clients = []
        self.server_socket.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
        self.server_socket.bind((defaults['ip'], defaults['port']))
        self.server_socket.listen()

    def handleConnection(self):
        while True:
            new_connection = self.server_socket.accept()
            log.info("Connection from {}".format(new_connection[1]))
            self.clients.append(Client(new_connection[0]))

    def handleClients(self):
        while True:
            ( self.rlist, _, _ ) = select([client.socket for client in self.clients], [], [], 1)
            for socket in self.rlist:
                for client in self.clients:
                    if socket == client.socket:
                        message = client.recvMessage().decode('UTF-8')
                        if message.startswith('/'):
                            self.executeCommand(client, message)
                        else:
                            sender = client.name
                            for client in self.clients:
                                try:
                                    client.sendMessage(sender + ': ' + message)
                                except (BrokenPipeError, ConnectionResetError):
                                    log.warning("Client {} has gone down... Removing...".format(client.name))
                                    self.clients.remove(client)


    def executeCommand(self, client, message):
        command = message.split()[0][1:]
        log.info("Received Command: {} from {}".format(command, client.name))
        if command == 'name':
            if len(message.split()) is 2:
                client.setName(message.split()[1])
                client.sendMessage("Name set to {}!\n".format(message.split()[1]))
            else:
                client.sendMessage("Sorry! Wrong usage of /name!\n")

    def serveForever(self):
        threading.Thread(target=self.handleConnection).start()
        threading.Thread(target=self.handleClients).start()


class Client:

    def __init__(self, socket):
        self.socket = socket
        self.name = str(self.socket.getpeername())

    def recvMessage(self):
        return self.socket.recv(defaults['bufsize'])

    def sendMessage(self, msg):
        self.socket.send(msg.encode('UTF-8'))

    def setName(self, name):
        self.name = name

if __name__ == '__main__':
    server = ChatServer()
    server.serveForever()
