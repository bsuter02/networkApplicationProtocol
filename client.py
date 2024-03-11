import socket
import threading
import hashlib

# This can be changed for cross-device communication, but I'm keeping this simple
host = "127.0.0.1"
port = 12345


# This function creates the header and encodes the checksum, applies it to the data, to create a packet
def packet_create(pkt_type, username, data):
    # Encodes data (the actual message) into a hash, used for checksum
    checksum = hashlib.md5(data.encode()).hexdigest()
    # Header structure: Packet Type, Username, Length of following Data, Checksum Hash
    header = f"{pkt_type}:{username}:{len(data)}:{checksum}"
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


# This function listens for a broadcast by the server and prints the chat
def rec_pkt(client):
    while True:
        try:
            pkt = client.recv(1024)
            pkt_content = pkt.decode("utf-8")

            # Extract and print only the message content
            split_header = pkt_content.split(":")
            if len(split_header) > 3:
                print(format_output(pkt_content))
            else:
                print(f"{pkt_content}")

        except:
            print("Connection closed.")
            break


# This function takes the client's input to the console, build the packet, and sends it to the server
def send_pkt(client, username):
    while True:
        data = input()
        if data.lower() == "exit":
            client.close()
            break
        try:
            client.send(packet_create("message", username, data).encode("utf-8"))
        except:
            print("Connection error.")
            break


# This serves as the main function for the client
def client_main():
    client = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    client.connect((host, port))

    # Client enters chosen username (prompt sent by server)
    chosen_name = client.recv(1024).decode("utf-8")
    print(chosen_name, end="")

    # Username is sent to the server
    usr = input()
    client.send(usr.encode("utf-8"))

    # Starts two threads to manage the sending and receiving of chats
    rec_thr = threading.Thread(target=rec_pkt, args=(client,))
    send_thr = threading.Thread(target=send_pkt, args=(client, usr))

    rec_thr.start()
    send_thr.start()


client_main()
