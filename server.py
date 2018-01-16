#!/usr/bin/env python

import json
import logging
import socket
import threading
import uuid
from select import select

defaults = { "ip": "0.0.0.0",
             "port": 8888,
             "channel": "lobby",
             "maxconn": 128,
             "bufsize": 4096,
             "valid_commands": ['name'] }

logging.basicConfig(format='%(asctime)s (%(levelname)s): %(message)s', 
                    level=logging.DEBUG,
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
            self.clients.append(Client(new_connection[0], str(uuid.uuid1())))

    def handleClients(self):
        while True:
            ( self.rlist, _, _ ) = select([client.socket for client in self.clients], [], [], 1)
            for socket in self.rlist:
                for client in self.clients:
                    if socket == client.socket:
                        message = client.recvMessage().decode('UTF-8')
                        try:
                            json_object = json.loads(message, encoding='UTF-8')
                            self.decodeJSON(client, json_object)
                        except (json.decoder.JSONDecodeError, UnicodeDecodeError):
                            log.warning("Client sent unspecific data... Disconnecting and removing...")
                            client.socket.close()
                            self.clients.remove(client)
#                        if message.startswith('/'):
#                            self.executeCommand(client, message)
#                        else:
#                            sender = client.name
#                            for client in self.clients:
#                                try:
#                                    client.sendMessage(sender + ': ' + message)
#                                except (BrokenPipeError, ConnectionResetError):
#                                    log.warning("Client {} has gone down... Removing...".format(client.name))
#                                    self.clients.remove(client)

    def sendMessage(self, client, json_object):
        json_object['sender'] = client.name
        if json_object['target'] == 'channel':
            to_send = [ client for client in self.clients if json_object['channel'] in client.channels ]
        elif json_object['target'] == 'direct':
            to_send = [ client for client in self.clients if json_object['direct'] in client.name ]
        for client in to_send:
            try:
                client.sendMessage(json_object)
            except (BrokenPipeError, ConnectionResetError):
                log.warning("Client {} has gone down... Removing...".format(client.name))
                self.clients.remove(self)

    def decodeJSON(self, client, json_object):
        log.debug("Received JSON object: {}".format(json_object))
        if json_object['type'] == "command":
            self.executeCommand(client, json_object)
        elif json_object['type'] == "message":
            self.sendMessage(client, json_object)
        else:
            log.error("No valid meesage type! Ignoring...")

    def executeCommand(self, client, json_object):
        log.info("Received Command: {} from {}".format(json_object['command'], client.name))
        if json_object['command'] == 'name':
            if " " not in json_object['data']:
                client.setName(json_object['data'])
                client.sendMessage(json_object)
            else:
                json_object['error'] = "Error! Name could not be set!"
                client.sendMessage(json_object)

    def serveForever(self):
        threading.Thread(target=self.handleConnection).start()
        threading.Thread(target=self.handleClients).start()

class Client:

    def __init__(self, socket, uuid):
        self.socket = socket
        self.uuid = uuid
        self.name = self.uuid
        self.channels = [ "lobby" ]

    def recvMessage(self):
        return self.socket.recv(defaults['bufsize'])

    def sendMessage(self, json_object):
        self.socket.send(json.dumps(json_object).encode('UTF-8'))

    def setName(self, name):
        self.name = name

if __name__ == '__main__':
    server = ChatServer()
    server.serveForever()
