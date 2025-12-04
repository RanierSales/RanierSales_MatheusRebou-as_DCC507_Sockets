# Sistema de Mensagens com Persistência

## Visão Geral

Este projeto implementa um **Sistema de Mensagens** básico, simulando as funcionalidades essenciais de plataformas como WhatsApp ou Telegram, com foco especial na **persistência de dados** (usuários, histórico e mensagens offline).

O sistema é composto por um **servidor** (`server.py`) multi-threaded que gerencia as conexões e a lógica de mensagens, e um **cliente** (`client.py`) com interface gráfica simples (usando `tkinter`).

## Funcionalidades

O sistema atende aos seguintes requisitos:

  * **Registro de Usuários:** Novas contas são criadas automaticamente no primeiro acesso se o nome de usuário não existir. Os dados de login são armazenados no arquivo `usuarios.txt`.
  * **Mensagens Diretas:** Permite o envio de mensagens ponto a ponto entre usuários logados através do comando `/msg`.
  * **Mensagens Offline (Persistência):** Mensagens enviadas a usuários que não estão conectados são salvas no arquivo `mensagens.txt` e entregues assim que o destinatário realizar o login.
  * **Histórico de Conversas:** O histórico de todas as mensagens enviadas/recebidas por um usuário é armazenado em arquivos dedicados (`historico/history_{username}.txt`) e pode ser visualizado através do comando `/history`.

## Tecnologias Utilizadas

  * **Linguagem:** Python 3
  * **Módulos Nativos:**
      * `socket`: Para a comunicação de rede (TCP).
      * `threading`: Para lidar com múltiplos clientes simultaneamente no servidor.
      * `tkinter`: Para a interface gráfica simples do cliente.
      * `os` / `datetime`: Para manipulação de arquivos e registro de tempo.

## Estrutura de Arquivos

O projeto utiliza os seguintes arquivos e diretórios para persistência:

| Arquivo/Diretório | Descrição |
| :--- | :--- |
| `server.py` | O código principal do servidor, responsável pela lógica de conexão, autenticação e mensagens. |
| `client.py` | O código principal do cliente, com a interface gráfica para interação. |
| `usuarios.txt` | Armazena o registro de **usuários** no formato `username;password`. |
| `mensagens.txt` | Armazena **mensagens offline** que precisam ser entregues no formato `sender;receiver;content;timestamp;delivered`. |
| `historico/` | Diretório que armazena os **históricos de conversas** em arquivos individuais por usuário (ex: `historico/history_joao.txt`). |

## Como Executar o Projeto

Certifique-se de ter o **Python 3** instalado em sua máquina.

### 1\. Iniciar o Servidor

O servidor precisa estar rodando antes de qualquer cliente se conectar.

1.  Abra um terminal na pasta do projeto.

2.  Execute o arquivo do servidor:

    ```bash
    python server.py
    ```

    O servidor será iniciado e exibirá a mensagem `[SERVIDOR] Aguardando conexões...`.

### 2\. Iniciar o Cliente

Você pode iniciar múltiplos clientes para testar a comunicação entre usuários.

1.  Abra um **novo** terminal na pasta do projeto.

2.  Execute o arquivo do cliente:

    ```bash
    python client.py
    ```

    Uma janela do **Tkinter** será aberta, solicitando o login.

## Comandos de Uso

Após realizar o login com sucesso, os seguintes comandos estão disponíveis para serem digitados no campo de mensagem do cliente:

| Comando | Descrição | Exemplo de Uso |
| :--- | :--- | :--- |
| **`/msg`** | Envia uma mensagem para o usuário especificado. | `/msg maria ola, tudo bem?` |
| **`/history`** | Exibe o histórico de mensagens do usuário logado. | `/history` |
| **`/sair`** | Desconecta o cliente do servidor e fecha a aplicação. | `/sair` |

## Autenticação

Ao iniciar o cliente:

1.  Digite o **usuário**.
      * Se o usuário **não existir**, ele será criado com a próxima senha fornecida.
      * Se o usuário **existir**, o sistema prossegue para a senha.
2.  Digite a **senha**.
      * Se o login for bem-sucedido, o cliente se conecta e as mensagens offline (se houver) são entregues.



