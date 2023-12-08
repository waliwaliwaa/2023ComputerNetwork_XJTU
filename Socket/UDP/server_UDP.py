# 导入socket模块
import socket

# 创建一个UDP套接字对象
# AF_INET = IPv4; SOCK_DGRAM = UDP
server_socket = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)

# 绑定服务器的IP地址和端口号
server_socket.bind(("127.0.0.1", 8888))

# 定义一个用户信息的字典，用于验证登录
users = {"admin": "123456", "user": "654321"}

print("服务器启动，等待客户端发送数据...")

# 无限循环，处理客户端发送的数据
while True:
    # 接收客户端发送的数据和客户端的地址，最多接收1024字节
    data, client_address = server_socket.recvfrom(1024)
    # 把接收到的数据解码为字符串
    message = data.decode()
    print(f"收到客户端{client_address}的消息：{message}")
    # 按空格分割消息，得到用户名和密码
    username, password = message.split()
    # 判断用户名和密码是否在用户信息字典中
    if username in users and users[username] == password:
        # 如果正确，发送回复消息“信息正确”
        reply = "信息正确"
    else:
        # 如果错误，发送回复消息“用户名或密码错误，请再次输入”
        reply = "用户名或密码错误，请再次输入"
    # 把回复消息编码为字节
    data = reply.encode()
    # 发送回复消息给客户端
    server_socket.sendto(data, client_address)
    print(f"发送给客户端{client_address}的消息：{reply}")

# 关闭服务器的套接字（永远不会执行到这一步）
server_socket.close()
