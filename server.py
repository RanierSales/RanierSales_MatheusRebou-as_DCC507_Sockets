import socket
import threading
from datetime import datetime
import os

# ---------------------------
# ARQUIVOS DO SISTEMA
# ---------------------------
USERS_FILE = "usuarios.txt"
MESSAGES_FILE = "menssagens.txt"
HISTORY_DIR = "historico"

# Se não existir, cria
if not os.path.exists(HISTORY_DIR):
    os.makedirs(HISTORY_DIR)

# Armazena clientes conectados
clients = {}   # {username: socket}


# ------------------------------------------------
# Funções auxiliares
# ------------------------------------------------

def user_exists(username):
    with open(USERS_FILE, "r", encoding="utf-8") as f:
        for line in f:
            name, *_ = line.strip().split(";")
            if name == username:
                return True
    return False


def verify_login(username, password):
    with open(USERS_FILE, "r", encoding="utf-8") as f:
        for line in f:
            name, pw = line.strip().split(";")
            if name == username and pw == password:
                return True
    return False


def save_user(username, password):
    with open(USERS_FILE, "a", encoding="utf-8") as f:
        f.write(f"{username};{password}\n")


def save_message(sender, receiver, content, delivered):
    timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    with open(MESSAGES_FILE, "a", encoding="utf-8") as f:
        f.write(f"{sender};{receiver};{content};{timestamp};{delivered}\n")

    # salva também no histórico dos dois
    save_history(sender, f"Você → {receiver}: {content}")
    save_history(receiver, f"{sender}: {content}")


def save_history(username, text):
    file = f"{HISTORY_DIR}/history_{username}.txt"
    timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")

    with open(file, "a", encoding="utf-8") as f:
        f.write(f"[{timestamp}] {text}\n")


def deliver_offline_messages(username, conn):
    """Envia mensagens guardadas para o usuário quando ele loga."""
    new_lines = []

    with open(MESSAGES_FILE, "r", encoding="utf-8") as f:
        lines = f.readlines()

    for line in lines:
        sender, receiver, content, timestamp, delivered = line.strip().split(";")

        if receiver == username and delivered == "0":
            conn.send(f"[OFFLINE] {sender}: {content}\n".encode())
            # marcar como entregue
            new_lines.append(f"{sender};{receiver};{content};{timestamp};1\n")
        else:
            new_lines.append(line)

    # regrava o arquivo todo
    with open(MESSAGES_FILE, "w", encoding="utf-8") as f:
        f.writelines(new_lines)


# ------------------------------------------------
# Lógica principal do cliente
# ------------------------------------------------
def handle_client(conn, addr):
    print(f"[SERVIDOR] Conexão recebida de {addr}")

    # LOGIN / REGISTRO
    conn.send("Digite seu usuário: ".encode())
    username = conn.recv(1024).decode().strip()

    conn.send("Digite sua senha: ".encode())
    password = conn.recv(1024).decode().strip()

    if not user_exists(username):
        # registrar automaticamente
        save_user(username, password)
        conn.send("Usuário criado com sucesso!\n".encode())
    else:
        if not verify_login(username, password):
            conn.send("Senha incorreta. Conexão encerrada.\n".encode())
            conn.close()
            return

        conn.send("Login realizado com sucesso!\n".encode())

    clients[username] = conn

    # Entregar mensagens offline
    deliver_offline_messages(username, conn)

    conn.send("\nComandos disponíveis:\n".encode())
    conn.send("/msg usuario mensagem\n".encode())
    conn.send("/history usuario\n".encode())
    conn.send("/sair\n\n".encode())

    # LOOP PRINCIPAL
    while True:
        try:
            data = conn.recv(1024).decode().strip()

            if not data:
                break

            # Comando de sair
            if data == "/sair":
                conn.send("Desconectado.\n".encode())
                break

            # Enviar mensagem
            if data.startswith("/msg "):
                parts = data.split(" ", 2)
                if len(parts) < 3:
                    conn.send("Uso: /msg usuario mensagem\n".encode())
                    continue

                _, dest, content = parts

                if not user_exists(dest):
                    conn.send("Esse usuário não existe.\n".encode())
                    continue

                if dest in clients:
                    # destinatário online
                    clients[dest].send(f"{username}: {content}\n".encode())
                    save_message(username, dest, content, 1)
                else:
                    # offline
                    save_message(username, dest, content, 0)

                continue

            # Histórico
            if data.startswith("/history "):
                _, dest = data.split(" ", 1)
                file = f"{HISTORY_DIR}/history_{username}.txt"

                if not os.path.exists(file):
                    conn.send("Nenhum histórico encontrado.\n".encode())
                else:
                    with open(file, "r", encoding="utf-8") as f:
                        conn.send(f.read().encode())

                continue

        except:
            break

    # finalização
    del clients[username]
    conn.close()
    print(f"[SERVIDOR] {username} desconectou.")


# ------------------------------------------------
# INICIAR SERVIDOR
# ------------------------------------------------
def start_server():
    server = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    server.bind(("127.0.0.1", 5000))
    server.listen()

    print("[SERVIDOR] Aguardando conexões...")

    while True:
        conn, addr = server.accept()
        thread = threading.Thread(target=handle_client, args=(conn, addr))
        thread.start()


start_server()
