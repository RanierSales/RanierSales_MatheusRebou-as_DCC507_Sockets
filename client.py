import socket
import threading

HOST = "127.0.0.1"
PORT = 5000

def receive_messages(sock):
    while True:
        try:
            data = sock.recv(1024).decode()
            if not data:
                break
            print(data)
        except:
            break

sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
sock.connect((HOST, PORT))

# Thread de recebimento
thread = threading.Thread(target=receive_messages, args=(sock,))
thread.daemon = True
thread.start()

# Loop de envio
while True:
    msg = input()
    sock.send(msg.encode())

    if msg == "/sair":
        break

sock.close()
