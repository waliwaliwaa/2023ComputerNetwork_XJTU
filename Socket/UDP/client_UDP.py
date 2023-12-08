# 导入socket模块
import socket

# 创建一个UDP套接字对象
# AF_INET = IPv4; SOCK_DGRAM = UDP
client_socket = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)

# 定义服务器的IP地址和端口号
server_address = ("127.0.0.1", 8888)

# 用一个循环来发送和接收数据
while True:
    # 输入要发送的用户名和密码，用空格分隔
    message = input("请输入用户名和密码（用空格分隔）：")
    # 如果输入为空，退出循环
    if not message:
        break
    # 把消息编码为字节
    data = message.encode()
    # 发送消息给服务器
    client_socket.sendto(data, server_address)
    print(f"发送给服务器的消息：{message}")
    # 接收服务器的回复消息，最多接收1024字节
    data, server_address = client_socket.recvfrom(1024)
    # 把接收到的数据解码为字符串
    reply = data.decode()
    print(f"收到服务器的消息：{reply}")
    # 如果回复消息是“信息正确”，退出循环
    if reply == "信息正确":
        break

# 关闭客户端的套接字
client_socket.close()
