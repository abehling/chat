#!/usr/bin/env python

import json
import socket
import threading
import tkinter as tk
from time import sleep
from tkinter import ttk
from tkinter import scrolledtext
from select import select

defaults = { 'bufsize': 4096 }

class Application(tk.Frame):
    def __init__(self, master=None):
        super().__init__(master)
        root.title("Chat")
        root.protocol("WM_DELETE_WINDOW", self.quit)
        root.tk.call('encoding', 'system', 'utf-8')
        self.message = tk.StringVar()
        self.connect_string = tk.StringVar()
        self.connect_string.set("127.0.0.1:8888")
        self.channel = "lobby"
        self.create_widgets()
        self.running = False
        self.pack()

    def create_widgets(self):
        self.server = tk.Entry(self, width=80, textvariable=self.connect_string)
        self.server.bind('<Return>', self.connect)
        self.server.grid(column=0, row=0, sticky='W')
        self.connect_button = tk.Button(self, text='Connect', command=self.connect)
        self.connect_button.grid(column=1, row=0, sticky='E')
        self.scroll = scrolledtext.ScrolledText(self, width=80, height=25)
        self.scroll.grid(column=0, row=1, sticky='W')
        self.userlist = tk.Listbox(self)
        self.userlist.grid(column=1, row=1, sticky='NWES') 
        self.button = tk.Button(self, text='Send', command=self.sendMessage)
        self.button.grid(column=1, row=2, sticky='E')
        self.entry = tk.Entry(self, width=80, textvariable=self.message)
        self.entry.bind('<Return>', self.sendMessage)
        self.entry.focus()
        self.entry.grid(column=0, row=2, sticky='W')

    def quit(self):
        self.running = False
        root.destroy()

    def sendMessage(self, event=None):
        json_string = self.encodeJSON(self.message.get())
        self.socket.send(json_string)
        self.message.set("")

    def encodeJSON(self, msg):
        json_object = {}
        if msg.startswith('/'):
            json_object['type'] = "command"
            json_object['command'] = msg.split()[0][1:]
            if json_object['command'] == "name":
               json_object['data'] = " ".join(msg.split()[1:])
        else:
            json_object['type'] = "message"
            json_object['target'] = "channel"
            json_object['channel'] = self.channel
            json_object['message'] = msg
        return json.dumps(json_object).encode('UTF-8')

    def decodeJSON(self, json_object):
        if json_object['type'] == "message":
            self.updateScrolledText(json_object)
        elif json_object['type'] == "command":
            self.executeCommand(json_object)
        else:
            self.scroll.insert(tk.END, "ERROR: Cannot decode JSON!")

    def updateScrolledText(self, json_object):
        self.scroll.insert(tk.END, "{}: {}\n".format(json_object['sender'],json_object['message']))

    def executeCommand(self, json_object):
        if json_object['command'] == "name" and 'error' not in json_object:
            self.scroll.insert(tk.END, "Name sucessfully changed to {}\n".format(json_object['data']))
        elif json_object['command'] == "list":
            self.userlist.delete(0, tk.END)
            for chatbuddy in json_object['list']:
                self.userlist.insert(tk.END, chatbuddy)
            print(self.userlist.get(0, tk.END))

    def handleConnection(self):
        while self.running:
            rlist, _, _ = select([self.socket], [],[], 1)
            for socket in rlist:
                data = socket.recv(defaults['bufsize'])
                json_object = json.loads(data, encoding='UTF-8')
                self.decodeJSON(json_object)

    def connect(self, event=None):
        if not self.running: 
            self.scroll.insert(tk.END, "Connecting to {}\n".format(self.connect_string.get()))
            self.socket = socket.socket()
            self.socket.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
            self.socket.connect((str(self.connect_string.get()).split(':')[0], int(str(self.connect_string.get()).split(':')[1])))
            self.running = True
            threading.Thread(target=self.handleConnection).start()
            self.server['state'] = tk.DISABLED
            self.connect_button['text'] = "Disconnect"
        else:
            self.scroll.insert(tk.END, "Disconnecting from {}\n".format(self.connect_string.get()))
            self.running = False
            self.server['state'] = tk.NORMAL
            self.connect_button['text'] = "Connect"
            self.socket = None
            self.userlist.delete(0, tk.END)
            

root = tk.Tk()
app = Application(master=root)
app.mainloop()

