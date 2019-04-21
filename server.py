import socket
import threading


# Host Information for server
HOST = ''
PORT = 8080
PAYLOAD = 4096


def main():
    # Store client information (conn, addr)
    clientList = {}
    clientLock = threading.Lock()
    s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    s.bind((HOST, PORT))

    def connectingClient():
        try:
            while True:
                conn, addr = s.accept()
                print('[client] Connected by', addr)
                threading._start_new_thread(receivingData, (conn,))
        except Exception as e:
            print(e)
            print("Disable connecting Client module")

    def receivingData(conn):
        conn_type = conn.recv(PAYLOAD).decode('utf-8')
        clientLock.acquire()
        if conn_type.startswith("text"):
            user_name = conn_type[4:]
            if user_name not in clientList.keys():
                clientList[user_name] = {}
            clientList[user_name]["text"] = conn
        elif conn_type.startswith("voice"):
            user_name = conn_type[5:]
            if user_name not in clientList.keys():
                clientList[user_name] = {}
            clientList[user_name]["voice"] = conn
        else: #user
            user_name = conn_type[4:]
            if user_name not in clientList.keys():
                clientList[user_name] = {}
            clientList[user_name]["user"] = conn
        clientLock.release()        
        if len(clientList[user_name]) == 3:
            threading._start_new_thread(receivingMsg, (clientList[user_name]["text"], user_name))
            threading._start_new_thread(receivingVoice, (clientList[user_name]["voice"], user_name))
            threading._start_new_thread(sendingUsers, ())

    def receivingMsg(conn, user_name):
        connection = True
        while connection:
            try:
                data = conn.recv(1024)
                print(data)
                threading._start_new_thread(sendingMsg, (user_name, data))
            except Exception:
                clientLock.acquire()
                connection = False
                for key in clientList[user_name]:
                    clientList[user_name][key].close()
                print('[%s] Disconnected ' %user_name)
                del clientList[user_name]
                threading._start_new_thread(sendingUsers, ())
                clientLock.release()

    def receivingVoice(conn, user_name):
        connection = True
        # Regard the next received data as message
        while connection:
            try:
                data = conn.recv(PAYLOAD)
                threading._start_new_thread(sendingVoice, (user_name, data))
            except Exception:
                connection = False

    def sendingMsg(rcv_user_name, rcv_data):
        data = '[' + rcv_user_name + '] ' + rcv_data.decode('utf-8')
        data = bytes(data, 'utf-8')
        clientLock.acquire()
        for user_name, conn_list in clientList.items():
            conn_list["text"].send(data)
        clientLock.release()

    def sendingVoice(rcv_user_name, rcv_data):
        try:
            for user_name, conn_list in clientList.items():
                # Send message to other clients
                if rcv_user_name != user_name:
                    conn_list["voice"].send(rcv_data)
        except:
            pass
    def sendingUsers():
        data = ""
        for user_name, conn_list in clientList.items():
            if data == "":
                data = data+user_name
            else:
                data = data + ',' + user_name

        data = bytes(data,'utf-8')
        try:
            for _, conn_list in clientList.items():
                print("User data was sent", data)
                conn_list["user"].send(data)
        except:
            print("Failed")

    try:
        print('Server was activated.')
        s.listen(1)
        threading._start_new_thread(connectingClient, ())
        while True:
            pass
    except:
        s.close()
        print('Server was deactivated.')


if __name__ == "__main__":
    # execute only if run as a script
    main()
