#!/usr/bin/env python

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
        self.button = tk.Button(self, text='Send', command=self.send)
        self.button.grid(column=1, row=2, sticky='E')
        self.entry = tk.Entry(self, width=80, textvariable=self.message)
        self.entry.bind('<Return>', self.send)
        self.entry.focus()
        self.entry.grid(column=0, row=2, sticky='W')

    def quit(self):
        self.running = False
        root.destroy()

    def send(self, event=None):
        self.socket.send(str(self.message.get()).encode('UTF-8') + b'\n')
        self.message.set("")

    def handleConnection(self):
        while self.running:
            rlist, _, _ = select([self.socket], [],[], 1)
            for socket in rlist:
                data = socket.recv(defaults['bufsize'])
                self.scroll.insert(tk.END, data)

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
            

root = tk.Tk()
app = Application(master=root)
app.mainloop()

