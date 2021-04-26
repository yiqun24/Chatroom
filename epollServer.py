from socket import *
from threading import *
import select
import queue
import json
import struct

# 怎么设计这个代码结构更好？
# 静态static方法？把面向对象知识再学一下, 这块好多地方很奇怪
users_list = list()


class User:
    """user_info"""

    def __init__(self, ID, name, mSocket):
        self.user_id = ID
        self.user_name = name
        self.socket = mSocket
        users_list.append(self)


def onlineUsers():
    onlineList = []
    for i in range(len(users_list)):
        onlineList.append(users_list[i].user_name)
    return onlineList


def newUser(ID, name, mSocket):
    # for i in range(len(users_list)):
    #     if users_list[i][0] == info['ID'] and users_list[i][1] != info['name']:
    #         return None
    new_user = User(ID, name, mSocket)
    return new_user


def sendData():
    while True:
        if not messages_queue.empty():
            Data = messages_queue.get()
            if isinstance(Data, str):
                Data = Data.encode()
                for i in range(len(users_list)):
                    # 报头协议，解决粘包问题，短消息是否也需要？
                    headerInfo = {
                        'data_size': len(Data),
                        'data_type': 'message'
                    }
                    header = json.dumps(headerInfo).encode()
                    users_list[i].socket.send(struct.pack('i', len(header)))
                    users_list[i].socket.send(header)
                    users_list[i].socket.send(Data)
            elif isinstance(Data, list):
                usersInfo = json.dumps(Data).encode()
                for i in range(len(users_list)):
                    headerInfo = {
                        'data_size': len(usersInfo),
                        'data_type': 'users_list'
                    }
                    header = json.dumps(headerInfo).encode()
                    users_list[i].socket.send(struct.pack('i', len(header)))
                    users_list[i].socket.send(header)
                    users_list[i].socket.send(usersInfo)


serverSocket = socket(AF_INET, SOCK_STREAM)
# 设置IP地址复用？ 端口立即复用？
serverSocket.setsockopt(SOL_SOCKET, SO_REUSEADDR, 1)
server_addr = ('', 8888)
serverSocket.bind(server_addr)
serverSocket.listen(10)
# 设置非阻塞？不等待
serverSocket.setblocking(False)
# 超时怎么理解
timeout = 10
epoll = select.epoll()  # epoll对象
# 注册服务器监听fd(socket?)等待读事件？ 接收？
epoll.register(serverSocket.fileno(), select.EPOLLIN)
# 连接客户端消息字典
messages_queue = queue.Queue()
# 文件句柄到所对应对象的字典 句柄：对象
fd_to_socket = {serverSocket.fileno(): serverSocket, }

sendThread = Thread(target=sendData)
sendThread.setDaemon(True)
sendThread.start()

while True:
    print("waiting for connection")
    # 轮询注册的事件集合，返回值为[(文件句柄，对应的事件)，(...),....]
    events = epoll.poll(timeout)
    if not events:
        print("epoll超时，没有指定时间发生，重新轮询")
        continue
    print(len(events), "new events!")

    for fd, event in events:
        # 欢迎套接字发生事件，说明有新连接

        if fd == serverSocket.fileno():
            connectSocket, address = serverSocket.accept()
            print("New connection!")
            # 还是非阻塞？
            connectSocket.setblocking(False)
            loginInfo = connectSocket.recv(1024).decode()
            userInfo = json.loads(loginInfo)
            user = newUser(userInfo['ID'], userInfo['name'], connectSocket)
            epoll.register(connectSocket.fileno(), select.EPOLLIN)
            fd_to_socket[connectSocket.fileno()] = user
            # 粘包问题发现
            messages_queue.put("---欢迎 " + user.user_name + "进入聊天室---")
            messages_queue.put(onlineUsers())

        # 关闭事件
        elif event & select.EPOLLHUP:
            print('client closed the connection')
            # 在epoll中注销客户端句柄
            epoll.unregister(fd)
            # 关闭客户端的文件句柄?关闭套接字
            fd_to_socket[fd].socket.close()
            users_list.remove(fd_to_socket[fd])
            # 删除信息 ?
            del fd_to_socket[fd]
            messages_queue.put(onlineUsers())

        # 可读事件 &运算?
        elif event & select.EPOLLIN:
            # 接收数据
            data = fd_to_socket[fd].socket.recv(1024).decode()
            if data:
                print("收到数据 " + data)
                message = fd_to_socket[fd].user_name + ':' + data
                # 需要加锁吗
                messages_queue.put(message)
                # 修改读取到消息的连接到等待写事件集合(即对应客户端收到消息后，再将其fd修改并加入写事件集合?)
                # epoll.modify(socket, select.EPOLLOUT)
            # 客户端关闭连接后的空数据包？FIN包？
            else:
                print('Client closed the connection')
                epoll.unregister(fd)
                fd_to_socket[fd].socket.close()
                users_list.remove(fd_to_socket[fd])
                del fd_to_socket[fd]
                messages_queue.put(onlineUsers())

        # elif event & select.EPOLLOUT:
        #     try:
        #         msg = message_queues[socket].get_nowait()  # 非阻塞方法？
        #     except queue.Empty:
        #         epoll.modify(socket, select.EPOLLIN)
        #     else:
        #         socket.send(msg.encode())

epoll.unregister(serverSocket.fileno())
epoll.close()
serverSocket.close()
