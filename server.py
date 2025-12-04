import socket
import threading
from datetime import datetime
import os

# ---------------------------
# ARQUIVOS DO SISTEMA
# ---------------------------
USERS_FILE = "usuarios.txt"
MESSAGES_FILE = "mensagens.txt"
HISTORY_DIR = "historico"

# Se não existir, cria
if not os.path.exists(HISTORY_DIR):
    os.makedirs(HISTORY_DIR)

# Armazena clientes conectados
clients = {}   # {username: socket}

SHARED_LOCK = threading.Lock()
FILE_LOCK = threading.Lock()


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

    with FILE_LOCK:
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

def recv_line(conn):
    """Lê do socket ate encontrar o caractere de nova linha (\\n)"""
    buffer = b''
    while True:
        chunk = conn.recv(1)
        if not chunk:
            return ""
        
        buffer += chunk

        if buffer.endswith(b'\n'):
            return buffer.decode().strip()


# ------------------------------------------------
# Lógica principal do cliente
# ------------------------------------------------
def handle_client(conn, addr):
    print(f"[SERVIDOR] Conexão recebida de {addr}")
    
    username = None
    password = None
    auth_state = "USER_PROMPT" # USER_PROMPT -> PASS_PROMPT -> LOGGED_IN

    conn.send("/PROMPT_USER Digite seu usuário: \n".encode())

    client_buffer = b''

    while True:
        try:
            data_chunk = conn.recv(1024)
            if not data_chunk:
                break
            client_buffer += data_chunk

            while b'\n' in client_buffer:
                message_end_index = client_buffer.find(b'\n')
                full_message = client_buffer[:message_end_index + 1]
                client_buffer = client_buffer[message_end_index + 1:]
                message = full_message.decode().strip()

                if auth_state == "USER_PROMPT":
                    username = message
                    # Se o usuario existir, vamos passar para a senha
                    conn.send("/PROMPT_PASS Digite sua senha: \n".encode())
                    auth_state = "PASS_PROMPT"
                    continue

                elif auth_state == "PASS_PROMPT":
                    password = message

                    if not user_exists(username):
                        save_user(username, password)
                        conn.send("/LOGIN_OK Usuário criado com sucesso!\n".encode())
                        auth_state = "LOGGED_IN"
                    elif not verify_login(username, password):
                        conn.send("/LOGIN_FAIL Senha incorreta. Conexão encerrada.\n".encode())
                        conn.close()
                        return
                    else:
                        conn.send("/LOGIN_OK Login realizado com sucesso!\n".encode())
                        auth_state = "LOGGED_IN"
                    
                    # Squando logamos com sucesso, mostramos as opcoes do menu
                    if auth_state == "LOGGED_IN":
                        with SHARED_LOCK:
                            clients[username] = conn
                        deliver_offline_messages(username, conn)

                        conn.send("\nComandos disponíveis:\n".encode())
                        conn.send("/msg usuario mensagem\n".encode())
                        conn.send("/history usuario\n".encode())
                        conn.send("/sair\n\n".encode())
                        continue

                if auth_state == "LOGGED_IN":
                    
                    if message == "/sair":
                        conn.send("Desconectado.\n".encode())
                        break
                    
                    if message.startswith("/msg "):
                        parts = message.split(" ", 2)
                        if len(parts) < 3:
                            conn.send("Uso: /msg usuario mensagem\n".encode())
                            continue
                        
                        _, dest, content = parts

                        if not user_exists(dest):
                            conn.send("Esse usuário não existe.\n".encode())
                            continue

                        with SHARED_LOCK:
                            if dest in clients:
                                clients[dest].send(f"{username}: {content}\n".encode())
                                save_message(username, dest, content, 1)
                            else:
                                save_message(username, dest, content, 0)
                        
                        continue
                    if message.startswith("/history "):
                        _, dest = message.split(" ", 1)
                        file = f"{HISTORY_DIR}/history_{username}.txt"

                        if not os.path.exists(file):
                            conn.send("Nenhum histórico encontrado.\n".encode())
                        else:
                            with open(file, "r", encoding="utf-8") as f:
                                conn.send(f.read().encode())

                        continue

        except Exception as e:
            break

    # finalização
    if username and username in clients:
        with SHARED_LOCK:
            del clients[username]
    conn.close()
    if username:
        print(f"[SERVIDOR] {username} desconectou.")
    else:
        print(f"[SERVIDOR] Conexão desconhecida encerrada.")


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
