import socket
import hashlib
import json
import threading
import os
import time 
import schedule     #needs a pip install 

class N_file():
    def __init__(self) -> None:
        self.name=""
        self.spread=1
        self.size_kb=0
        self.own_hash = None
        

ownfiles:dict[str,N_file] = {}


alocated_size = 0   #in bytes
used_size = 0       #in bytes
size_left = 0       #in bytes

hosts_up= 0
settings= {}



PORT = 50000
BROADCAST_IP = "255.255.255.255"


def listener():
    recv_sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    recv_sock.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
    print(f"Listening on {PORT}...")
    
    while True:
        #data, addr = recv_sock.recvfrom(1024)
        #recv_sock.sendto(b"", addr)

        data, addr = recv_sock.recvfrom(1024)

        datarr = data.decode().split(",",2)

        print(f"got data: {datarr}")

        match int(datarr[0]):

            case 1:
                #ping
                #reply whit 1
                recv_sock.sendto(b"1", addr)

            case 2:
                #file exists
                #look for the filename in ownfiles and if we have it reply whit 1

                if datarr[1] in ownfiles.keys():
                    recv_sock.sendto(b"1", addr)

            case 3:
                #list of files
                #send ownfiles
                
                recv_sock.sendto(json.dumps(ownfiles).encode(), addr)

            case 4:
                #download
                #reply whit 1 if we can safe it and then when the uploader replies we go to downloading the file


                pass
            case 5:
                #delet network wide
                #if we have the file delet it and remove
                #ahh yes very good idea but idk how to auth that
                del_file = datarr[1]

                if del_file in ownfiles.keys():
                    try:
                        os.remove(f"files/{del_file}")

                        ownfiles.pop(del_file)

                    except:
                        print(f"failed to delet file: {del_file}")

            case 6:
                #recive dowload conformation
                dow_file = datarr[1]

                if dow_file in ownfiles.keys():
                    ownfiles[dow_file].spread+=1
                

            case 7:
                #hash request
                #if we have the file we hash and send it

                file_to_hash = datarr[1]

                if file_to_hash in ownfiles.keys():
                    try:
                        with open(f"data/{file_to_hash}","r") as raw_file:
                            file_content = raw_file.read()

                        recv_sock.sendto(hashlib.sha256(file_content.encode()).hexdigest().encode(), addr)
                    except Exception as e:
                        print(f"failed to open or send hash: {e}")

def start_up(se_sock:socket.socket) -> None:


    with open("./data/config.json") as confile:
        text = confile.read()

    setings = json.loads(text)
    print("settings:")
    for keys, val in setings.items():
        print(f"{keys}: {val}")

    with open("./data/varstore.json") as varfile:
        vartext = varfile.read()

    varstore :dict[str,N_file]= json.loads(vartext)

    global used_size, size_left

    # get size
    for ele in os.scandir("./files"):
        used_size+=os.stat(ele).st_size

    print("folder size: ",end="")
    print(used_size)

    size_left = alocated_size - used_size


    hosts_up= 0
    other_up= False

    se_sock.settimeout(1)
    se_sock.sendto(b"1", (BROADCAST_IP, PORT))

    try:
        while True:
            data, addr = se_sock.recvfrom(1024)
            hosts_up+= 1
    except socket.timeout:
        print(f"Done collecting responses: {hosts_up}")
    
    if hosts_up  < 1:
        print("no other host are up.\nonly listening pasevly")
    else:
        other_up = True     

    if varstore !={}:
        print("varstore:")
        for file in varstore.values():
            print(f"{file.name}")
    else:
        if other_up:
            otherlist :list[dict[str,N_file]]= []

            se_sock.sendto(b"3", (BROADCAST_IP, PORT))

            try:
                while True:
                    data, addr = se_sock.recvfrom(1024)
                    otherlist.append(json.loads(data.decode()))
                    

            except socket.timeout:
                print(f"Done Fetching File lists:")

            for dicta in otherlist:
                varstore.update(dicta)      #kinda ok solution  #replace whit something that will also detect problems/diferences
            
            for file in varstore.values():
                print(f"{file.name}")
    
            
        else:
            print(f"no others are up to fetch file list from defaulting to {{}}")



def test_job():
    print("working") 
    

def treadscheduler():
    while True:
        schedule.run_pending()
        time.sleep(2)




# Start listener thread
threading.Thread(target=listener, daemon=True).start()
threading.Thread(target=treadscheduler, daemon=True).start()





# Send broadcasts
send_sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
send_sock.setsockopt(socket.SOL_SOCKET, socket.SO_BROADCAST, 1)
print(f"sending on {PORT}")

start_up(send_sock)

schedule.every(10).seconds.do(test_job)


print("shell:")
while True: #comand line like thingy
    line = input(">").strip().split(" ")
    op= line[0]

    match op:
        case "":
            pass
        case "ls":
            print('files in the files folder:')
            for file in os.listdir("./files"):
                print(file)