import socket
import threading
import hashlib

# This can be changed for cross-device communication, but I'm keeping this simple
host = "127.0.0.1"
port = 12345

clients_list = []
username_list = []

# This function creates the header and encodes the checksum, applies it to the data, to create a packet
def packet_create(data_type, username, data):
    # Encodes data into a hash, used for checksum
    checksum = hashlib.md5(data.encode()).hexdigest()
    # Header structure: Packet Type, Username, Length of following Data, Checksum Hash
    header = f"{data_type}:{username}:{len(data)}:{checksum}"
    return f"{header}|{data}"


# This function extracts the message from the packet
def parse_data(pkt):
    header_split = pkt.split("|")
    if len(header_split) == 2:
        return header_split[1]


# This function extracts the username from the function
def parse_username(pkt):
    split_header = pkt.split(":")
    if len(split_header) >= 2:
        return split_header[1]


# This function formats the output seen in the console by clients
def format_output(pkt):
    return f"{parse_username(pkt)}: {parse_data(pkt)}"


# This function prints to the server console when a new user connects, the username and assigned address
def join_message(addr, user):
    print(f"{user} connected via {addr}. Capacity: {5 - len(clients_list)}")


# Client handler, listens for packets and verifies via checksum before broadcasting to other clients
def handle_client(client, address, username):
    if username in username_list:
        print(f"Username {username} is not unique. Requesting a different username.")
        client.send("Username is already taken. Please use a different one: ".encode("utf-8"))
        new_username = parse_data(client.recv(1024).decode("utf-8"))
        handle_client(client, address, new_username)
        return
    else:
        username_list.append(username)
        join_message(address, username)
        client.send(f"Username accepted. Happy chatting, {username}!".encode("utf-8"))


    exit_cond = False

    try:
        while not exit_cond:
            data = client.recv(1024)
            if not data:
                break

            pkt = data.decode("utf-8")
            print(f"Received message from {username}: {pkt}")

            # Verify checksum before broadcasting
            if checksum_valid(pkt):
                if parse_data(pkt).lower() == "exit":
                    print(f"{username} has left the chat.")
                    exit_cond = True
                else:
                    # Broadcast the message to all clients
                    print_to_chat(format_output(packet_create("message", username, parse_data(pkt))), client)
            else:
                print("Packet Corruption Detected. No message will be put to chat.")

    except:
        pass

    print(f"Connection from {username} closed")
    clients_list.remove(client)
    username_list.remove(username)
    client.close()


# This message send the client's chat to the other users
def print_to_chat(pkt, sndr):
    for cli in clients_list:
        if cli != sndr:
            try:
                cli.send(pkt.encode("utf-8"))
            except:
                print("Client no longer connected.")
                clients_list.remove(cli)


# Parses checksum from header and validates against expected checksum hash
def checksum_valid(pkt):
    # Isolate Checksum
    split_header = pkt.split(":")
    received_checksum = split_header[-1].split("|")[0]
    # Evaluate Checksum, False proves either checksum or message was corrupted
    return received_checksum == hashlib.md5(parse_data(pkt).encode()).hexdigest()


def server_main():
    server = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    server.bind((host, port))
    server.listen(5)

    # Gives address info on server start and capacity remaining
    print(f"Server open on {host}:{port}. Capacity: 5")

    while True:
        client, addr = server.accept()
        clients_list.append(client)

        # Prompt the client for a username
        client.send("Enter your username: ".encode("utf-8"))
        username = client.recv(1024).decode("utf-8")

        # Start a new thread to handle the client
        client_handler = threading.Thread(target=handle_client, args=(client, addr, username))
        client_handler.start()


server_main()
