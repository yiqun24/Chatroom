from socket import *
from threading import *
import tkinter
import tkinter.messagebox
import json
import struct

import tkinter.filedialog
from tkinter import font
from tkinter.scrolledtext import ScrolledText

user = ''
user_id = 0
serverName = '172.16.120.177'
serverPort = 8888


def login():
    global user, ID
    ID = int(entryID.get())
    user = entryUSER.get()

    if not ID:
        tkinter.messagebox.showerror('warning', '账号为空')
    elif not user:
        tkinter.messagebox.showerror('warning', '用户名为空')
    else:
        root.destroy()


root = tkinter.Tk()
root.geometry("320x210")
root.title("Login")
root.resizable(0, 0)
root.configure(background='DeepSkyBlue')

USER = tkinter.StringVar()
USER.set('')
ID = tkinter.StringVar()
ID.set('')

labelID = tkinter.Label(root, text='账号', bg="DeepSkyBlue")
labelID.place(x=40, y=45, width=70, height=40)
entryID = tkinter.Entry(root, width=80, textvariable=ID)
entryID.place(x=100, y=45, width=130, height=30)

labelUSER = tkinter.Label(root, text='用户名', bg="DeepSkyBlue")
labelUSER.place(x=40, y=100, width=70, height=40)
entryUSER = tkinter.Entry(root, width=80, textvariable=USER)
entryUSER.place(x=100, y=100, width=130, height=30)

loginButton = tkinter.Button(root, text='登陆', command=login, bg='Yellow')
loginButton.place(x=135, y=150, width=50, height=25)
root.bind('<Return>', login)
root.mainloop()

# class Client:
#
#     def __init__(self, name, ID):
#         self.userID = ID
#         self.userName = name
#         self.socket = socket(AF_INET, SOCK_STREAM)
#         try:
#             self.socket.connect((serverName, serverPort))
#         except error:
#             print("connection failed! please try again later")
#             exit()

clientSocket = socket(AF_INET, SOCK_STREAM)
try:
    clientSocket.connect((serverName, serverPort))
except error:
    print("connection failed! please try again later")
    exit()

clientSocket.send(json.dumps({
    'ID': ID,
    'name': user
}).encode())

chatRoom = tkinter.Tk()
chatRoom.geometry("725x380")
chatRoom.title('chatroom')
chatRoom.resizable(0, 0)
listbox = ScrolledText(chatRoom)
listbox.place(x=5, y=0, width=640, height=320)

topFont = font.Font(size=20, slant=font.ITALIC)
messageFont = font.Font(family='Times', size=15)
listbox.tag_config('tag1', foreground='Blue', backgroun="yellow", font=topFont)
listbox.tag_config('tag2', font=messageFont)
listbox.insert(tkinter.END, '群聊测试版本1.0，实现基本功能，初步美化界面!\n', 'tag1')

INPUT = tkinter.StringVar()
INPUT.set('')
entryInput = tkinter.Entry(chatRoom,
                           width=120,
                           textvariable=INPUT,
                           relief='sunken')
entryInput.place(x=5, y=320, width=600, height=50)

userBox = tkinter.Listbox(chatRoom)
userBox.place(x=600, y=0, width=120, height=320)


def send():
    message = entryInput.get()
    clientSocket.send(message.encode())
    INPUT.set('')


# 要进行拆包操作，分离包头？
def receive():
    while True:
        header_length = struct.unpack('i', clientSocket.recv(4))[0]
        header = clientSocket.recv(header_length)
        headerInfo = json.loads(header.decode())
        data_size = headerInfo['data_size']
        data_type = headerInfo['data_type']

        res = b''
        recv_size = 0
        while recv_size + 1024 < data_size:
            recv_data = clientSocket.recv(1024)
            res += recv_data
            recv_size += len(recv_data)
        res += clientSocket.recv(data_size-recv_size)

        if data_type == 'message':
            listbox.insert(tkinter.END, res.decode() + '\n', 'tag2')

        elif data_type == 'users_list':
            users = json.loads(res.decode())
            userBox.delete(0, tkinter.END)
            userBox.insert(tkinter.END, "---当前在线用户---\n")
            for i in range(len(users)):
                userBox.insert(tkinter.END, users[i])


sendButton = tkinter.Button(chatRoom,
                            command=send,
                            text="发送",
                            font=('Helvetica', 18),
                            fg='Blue',
                            bg='white')
sendButton.place(x=600, y=320, width=60, height=50)
chatRoom.bind('<Return>', send)
recThread = Thread(target=receive)
recThread.setDaemon(True)
# 这个再查一下哈
recThread.start()
chatRoom.mainloop()
