import socket
import hashlib
import json
import threading
import os

class N_file():
    def __init__(self) -> None:
        self.name=""
        self.spread=1
        self.size_kb=0
        self.own_hash = None
        

ownfiles:list[N_file]=[]
size_left_kb = 0

with open("./data/config.json") as confile:
    text = confile.read()

setings = json.loads(text)
print(setings)

for keys, val in setings.items():
    print(f"{keys}: {val}")

exit()

PORT = 50000
BROADCAST_IP = "255.255.255.255"

ssock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
ssock.bind(('', PORT))  # Listen on all interfaces


def listener():
    recv_sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    recv_sock.bind(("", PORT))
    print(f"Listening on {PORT}...")
    while True:
        #data, addr = recv_sock.recvfrom(1024)
        #recv_sock.sendto(b"", addr)

        data, addr = recv_sock.recvfrom(1024)

        datarr = data.decode().lower().split(",",2)

        match datarr[0]:
            case 1:
                #ping
                #reply whit 1
                recv_sock.sendto(b"1", addr)


                pass
            case 2:
                #file exists
                #look for the filename in ownfiles and if we have it reply whit 1
                for i in range(len(ownfiles)):
                    if ownfiles[i].name == datarr[1]:
                        recv_sock.sendto(b"1", addr)
                        break

            case 3:
                #list of files
                #send ownfiles
                
                file_list_text = json.dumps(ownfiles)
                recv_sock.sendto(file_list_text.encode(), addr)

            case 4:
                #upload
                #reply whit 1 if we can safe it and then when the uploader replies we go to downloading the file
                pass
            case 5:
                #delet network wide
                #if we have the file delet it and remove
                #ahh yes very good idea but idk how to auth that
                del_file = datarr[1]
                for file in ownfiles:
                    if file.name == del_file:
                        try:
                            os.remove(f"data/{del_file}")

                            ownfiles.remove(file)

                        except:
                            print(f"failed to delet file: {del_file}")
                        break

            case 6:
                #recive dowload conformation
                dow_file = datarr[1]
                for file in ownfiles:
                    if file.name == del_file:
                        file.spread+=1
                        break


                        


            case 7:
                #hash request
                #if we have the file we hash and send it

                file_to_hash = datarr[1]
                for search_file in ownfiles:
                    if search_file.name == file_to_hash:
                        with open(f"data/{file_to_hash}","r") as raw_file:
                            file_content = raw_file.read()

                        recv_sock.sendto(hashlib.sha256(file_content.encode()).hexdigest().encode(), addr)
                        break
                        


# Start listener thread
threading.Thread(target=listener, daemon=True).start()

# Send broadcasts
send_sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
send_sock.setsockopt(socket.SOL_SOCKET, socket.SO_BROADCAST, 1)

while True:
    send_sock.sendto(b"helo", (BROADCAST_IP, PORT))
    print("Broadcast sent.")

            


