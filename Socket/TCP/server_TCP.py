import socket

# 创建一个TCP套接字对象
# AF_INET = IPv4; SOCK_STREAM = TCP
server_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)

# 绑定服务器的IP地址和端口号
server_socket.bind(("127.0.0.1", 8888))

# 开始监听客户端的连接请求，最多允许5个客户端同时连接
server_socket.listen(5)
print("服务器启动，等待客户端连接...")

# 定义一个用户信息的字典，用于验证登录
users = {"admin": "123456", "user": "654321"}

# 实现循环监听，处理客户端的连接和通信
while True:
    # 接受一个客户端的连接，返回一个新的套接字对象和客户端的地址
    client_socket, client_address = server_socket.accept()
    print(f"客户端{client_address}已连接")

    # 用一个循环来处理和这个客户端的通信
    while True:
        # 接收客户端发送的数据，最多接收1024字节
        data = client_socket.recv(1024)
        if not data:
            break
        # 把接收到的数据解码为字符串
        message = data.decode()
        print(f"收到客户端{client_address}的消息：{message}")
        username, password = message.split()
        if username in users and users[username] == password:
            reply = "信息正确"
        else:
            reply = "用户名或密码错误，请再次输入"
        # 把回复消息编码为字节
        data = reply.encode()
        # 发送回复消息给客户端
        client_socket.send(data)
        print(f"发送给客户端{client_address}的消息：{reply}")
        
    client_socket.close()
    print(f"客户端{client_address}已断开")

# 关闭（永远不会执行到这一步）
server_socket.close()
