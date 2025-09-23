import socket
import hashlib
import json
import threading
import os
import time
import schedule     #needs a pip install 
from datetime import datetime, timedelta


class N_file():
    def __init__(self) -> None:
        self.name=""
        self.spread= 1
        self.size_b= 0
        self.own_hash = None

    def __str__(self) -> str:
        return f"Name:{self.name}, Spread:{self.spread}, Size:{self.size_b}, Hash:{self.own_hash}"
    
    def __repr__(self) -> str:
        return f"Name:{self.name}, Spread:{self.spread}, Size:{self.size_b}, Hash:{self.own_hash}"

        

ownfiles:dict[str,N_file] = {}


alocated_size = 0   #in bytes
used_size = 0       #in bytes
size_left = 0       #in bytes

hosts_up= 0
any_up = False
setings= {}
version=  "0.1.0"
prog_start = datetime.now()


verhelp=("-------\n"
        f"Prisma Torrent {version}\n"
        "--------\n"
        "help: display this\n"
        "ls:list files on this machine\n"
        "nls: network ls list all files on all machines\n"
        "get\n"
        "set\n"
        "index: drop you current ownfile list and load new from folder\n"
        "upcheck: print the number of other prismas online in the network\n"
        "exit/shutdown: ends the program"
        "stat/info: prints infos"
        ""
        )



PORT = 49999
BROADCAST_IP = "255.255.255.255"


def listener():
    recv_sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    recv_sock.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
    print(f"Listening on {PORT}...")
    
    while True:
        #data, addr = recv_sock.recvfrom(1024)
        #recv_sock.sendto(b"", addr)

        global used_size, size_left, any_up, hosts_up

        sock, addr = recv_sock.accept()

        datate = sock.recv(1024)

        datarr = datate.decode().split(",",2)

        print(f"got data: {datarr}")

        match int(datarr[0]):

            case 1:
                #ping
                #reply whit 1
                recv_sock.sendall(b"1")
                any_up= True

            case 2:
                #file exists
                #look for the file_idame in ownfiles and if we have it reply whit 1

                if datarr[1] in ownfiles.keys():
                    recv_sock.sendall(b"1")

            case 3:
                #list of files
                #send ownfiles
                
                recv_sock.sendall(json.dumps(ownfiles).encode())

            case 4:
                #download
                #reply whit 1 if we can safe it and then when the uploader replies we go to downloading the file
                fsize= int(datarr[2])
                file_id=datarr[1]
                if file_id not in ownfiles.keys() and size_left > fsize:
                    recv_sock.send(b"1")

                    serv = socket.socket(socket.AF_INET, socket.SOCK_STREAM)

                    serv.bind(("0.0.0.0",50055))

                    serv.listen(1)

                    sock, serv_addr = serv.accept()


                    datarr: list[str] = sock.recv(1024).decode().split(",",2)

                    rec_file_name: str = datarr[0]
                    filesize :int= int(datarr[1])


                    recived = 0
                    dat=""
                    with open(f"files/{rec_file_name}","ab") as file:

                        while recived != filesize:
                            
                            try:
                                dat = sock.recv(min(1024,filesize-recived))
                            except:
                                break
                            if not dat:
                                break
                            file.write(dat)
                            recived+= len(dat)

                    ownfiles[rec_file_name] = N_file()

                    ownfiles[rec_file_name].own_hash = hashlib.sha256(file_content).hexdigest()  # type: ignore

                    ownfiles[rec_file_name].size_b= os.stat(f"files/{rec_file_name}").st_size

                    sock.settimeout(1)
                    sock.sendto(f"2,{file_id}".encode(), (BROADCAST_IP, PORT))

                    try:
                        while True:
                            if b"1"==sock.recv(10):
                                ownfiles[rec_file_name].spread+= 1

                    except socket.timeout:
                        pass




                    #open up a listening TCP socket and the other one should start sending the file



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
                        with open(f"data/{file_to_hash}","rb") as raw_file:
                            file_content = raw_file.read()

                        recv_sock.sendto(hashlib.sha256(file_content).hexdigest().encode(), addr)
                    except Exception as e:
                        print(f"failed to open or send hash: {e}")

def start_up(se_sock:socket.socket) -> None:

    global used_size, size_left,any_up,hosts_up



    with open("./data/config.json") as confile:
        text = confile.read()

    setings = json.loads(text)
    print("setings:")
    for keys, val in setings.items():
        print(f"{keys}: {val}")


    alocated_size = setings["space_allocated"]




    thingo = os.scandir("./files")
    fnum=0

    # get size
    for ele in thingo:
        used_size+=os.stat(ele).st_size
        fnum+=1

    print(f"files stored: {fnum}")
    print("folder size: ",end="")
    print(used_size)

    size_left = alocated_size - used_size


    hosts_up= 0
    any_up= False

    any_up_check(se_sock)
    
    if not any_up:
        print("no other host are up.\nonly listening pasevly")
    
    index(se_sock)

def shutdown():
    print("shuting down")
    exit()

def get_uptime() -> timedelta:
    return datetime.now()-prog_start
    
            
def index(se_sock:socket.socket):
    global ownfiles
    ownfiles={}
    filesl = os.listdir("./files")
    for file_id in filesl:
        ownfiles[file_id]= N_file()
        ownfiles[file_id].name= file_id
        
        with open(f"files/{file_id}","rb") as raw_file:
            file_content: bytes = raw_file.read()

        ownfiles[file_id].own_hash = hashlib.sha256(file_content).hexdigest()  # type: ignore

        se_sock.settimeout(1)
        se_sock.sendto(f"2,{file_id}".encode(), (BROADCAST_IP, PORT))

        try:
            while True:
                data, acaddr = se_sock.recvfrom(10)
                if data==b"1":
                   ownfiles[file_id].spread+= 1

        except socket.timeout:
            pass

        ownfiles[file_id].size_b= os.stat(f"files/{file_id}").st_size

    print("\nindexed:")

def test_job():
    print("working") 

def any_up_check(se_sock:socket.socket) -> None:
    global hosts_up, any_up
    hosts_up= 0
    any_up= False

    se_sock.settimeout(1)
    se_sock.sendto(b"1", (BROADCAST_IP, PORT))

    try:
        while True:
            data, acaddr = se_sock.recvfrom(10)
            if data==b"1":
                hosts_up+= 1

    except socket.timeout:
        any_up = (hosts_up > 0)
           

    

def treadscheduler():
    while True:
        schedule.run_pending()
        time.sleep(2)

def pstats():
    print("Stats: "
          f"uptime: {get_uptime()}\n"
          f"hosts up: {hosts_up}\n"
          f"files stored: {len(ownfiles)}\n"
          f"alocated bytes: {alocated_size}\n"
          f"used bytes: {used_size}\n"
          f"bytes left: {size_left}\n"
          ""
          )


# Start listener thread
threading.Thread(target=listener, daemon=True).start()
threading.Thread(target=treadscheduler, daemon=True).start()





# Send broadcasts
send_sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
send_sock.setsockopt(socket.SOL_SOCKET, socket.SO_BROADCAST, 1)
print(f"sending on {PORT}")

start_up(send_sock)

#schedule.every(10).seconds.do(test_job)
schedule.every().minute.do(any_up_check,se_sock= send_sock)


print("shell:")
try:
    while True: #comand line like thingy
        line = input(">").strip().split(" ")
        op = line[0].lower()

        match op:
            case "ls":
                print('files in the files folder:')
                if(len(line) > 1 and line[1] == "-a"):
                    for nama, dictor in ownfiles.items():
                        print(f"{nama}: {dictor}")
                else:
                    for file in os.listdir("./files"):
                        print(file)

            case "nls":
                otherlist :list[dict[str,N_file]]= []
                tmp_dict :dict[str,N_file]= {}


                send_sock.sendto(b"3", (BROADCAST_IP, PORT))

                try:
                    while True:
                        data, caaddr = send_sock.recvfrom(1024)
                        otherlist.append(json.loads(data.decode()))
                        

                except socket.timeout:
                    print(f"Done Fetching File lists:")


                for dicta in otherlist:
                    tmp_dict.update(dicta)      #kinda ok solution

                print(ownfiles)
                tmp_dict.update(ownfiles)
                
                if(len(line) > 1 and line[1] == "-a"):
                    for nama, dictor in ownfiles.items():
                        print(f"{nama}: {dictor}")
                else:
                    for file in tmp_dict.values():
                        print(file.name)
                    
            case "help":
                print(verhelp)

            case "index":
                index(send_sock)
                for nama, dictor in ownfiles.items():
                    print(f"{nama}: {dictor}")

            case "upcheck":
                any_up_check(send_sock)
                if any_up:
                    print(f"{hosts_up} are up")
                else:
                    print("no other hosts were found on the network")

            case "info":
                pstats()

            case "stat":
                pstats()


            case "shutdown":
                shutdown()

            case "exit":
                shutdown()

            case _:
                print(f"comand {op} not found.\nuse help to get a list of comands")
except Exception as e:
    if e is not KeyboardInterrupt:
        print(f"an exeption acoured: {e}")
    shutdown()

