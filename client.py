import socket
import threading
import tkinter as tk

HOST = "127.0.0.1"
PORT = 5000
CLIENT_STATE = 0
RECV_BUFFER = b''

sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
sock.connect((HOST, PORT))

# Inicializacao da Interface
root = tk.Tk()
root.title("Sistema de Mensageria - Cliente")

chat_history = tk.Text(root, state=tk.DISABLED, width=50, height=20)
chat_history.pack(padx=10, pady=5)

message_entry = tk.Entry(root, width=50)
message_entry.pack(padx=10, pady=5)

def send_message_trigger(event=None):
    send_message()

# Como fazemos a tecla Enter ser reconhecida para envio
message_entry.bind('<Return>', send_message_trigger)

send_button = tk.Button(root, text="Enviar", command=send_message_trigger)
send_button.pack(padx=10, pady=5)


def receive_messages(sock):
    global root, CLIENT_STATE, RECV_BUFFER

    while True:
        try:
            data_chunk = sock.recv(1024)
            if not data_chunk:
                print("Conexão fechada pelo servidor.")
                break
            
            RECV_BUFFER += data_chunk

            while b'\n' in RECV_BUFFER:
                message_end_index = RECV_BUFFER.find(b'\n')
                full_message = RECV_BUFFER[:message_end_index + 1]
                RECV_BUFFER = RECV_BUFFER[message_end_index + 1:]
                message = full_message.decode().strip()

                if message.startswith("/PROMPT_USER"):
                    CLIENT_STATE = 0 
                    prompt = message.split(" ", 1)[1]
                    root.after(0, display_message, prompt)
                
                elif message.startswith("/PROMPT_PASS"):
                    CLIENT_STATE = 1
                    prompt = message.split(" ", 1)[1]
                    root.after(0, display_message, prompt)

                elif message.startswith("/LOGIN_OK"):
                    CLIENT_STATE = 2
                    info = message.split(" ", 1)[1]
                    root.after(0, display_message, info)

                elif message.startswith("/LOGIN_FAIL"):
                    info = message.split(" ", 1)[1]
                    root.after(0, display_message, info)
                    root.after(2000, root.destroy)

                else:
                    root.after(0, display_message, message) 

        except Exception as e:
            print(f"Erro na thread de recebimento: {e}")
            break

def send_message():
    global sock, message_entry, CLIENT_STATE
    message = message_entry.get()

    if not message:
        return
    
    try:
        sock.send(f"{message}\n".encode())
    except BrokenPipeError:
        print("Erro: Não foi possível enviar. Servidor desconectado.")
        return

    if CLIENT_STATE == 2:
        if message.startswith("/msg "):
            parts = message.split(" ", 2)
            if len(parts) == 3:
                _, dest, content = parts
                display_message(f"Você Para {dest}: {content}")
        
        elif not message.startswith("/"):
            display_message(f"Você: {message}")
        
        if message == "/sair":
            root.after(500, root.destroy) 
            return 
    message_entry.delete(0, tk.END)

def display_message(message):
    global chat_history
    chat_history.config(state=tk.NORMAL)
    chat_history.insert(tk.END, message + "\n")
    chat_history.config(state=tk.DISABLED)
    chat_history.see(tk.END)

thread = threading.Thread(target=receive_messages, args=(sock,))
thread.daemon = True
thread.start()

root.mainloop()

sock.close()