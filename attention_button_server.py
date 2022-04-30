import socket
import time
import pdpyras
import os
from decouple import config
import traceback

Key = config('APIKEY')
RoutingKey = config('RoutingKEY')


global API_session
global event_session
global myevents

event_session = pdpyras.EventsAPISession(RoutingKey)
API_session = pdpyras.APISession(Key)

while True:
    managed_to_send =False
    response = ""

    try:

        def send():
            global myevents
            global managed_to_send

            print("in send function")
            myevents=API_session.list_all('/incidents',params={'statuses[]':['triggered']})
            print("outstanding events ",len(myevents))

            event_key = event_session.trigger("Leon", "attention-button")
            print(event_key)

            room = b"Kitchen(button)"
            message = b"PlaySound:" + room +b":"+ bytes(event_key,'ascii')
            TCP_IP = "192.168.1.20"
            TCP_PORT = 8080
            s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            s.settimeout(3)

            managed_to_send = False

            try:
                s.connect((TCP_IP, TCP_PORT))
                print("Connected")
                s.send(message)
            except socket.timeout:
                print("connect failed") 
                return
            
            try:
                data = s.recv(1024)
                print("recieved:", data, len(data),len(message))
                print(data.hex())
                print(message.hex())
                if data == message:
                    managed_to_send = True
                else:
                    print("compare failed")
            except socket.timeout:
               pass

            s.close()
            print("return from send, managed_to_send=",managed_to_send)

        #def send_UDP():
        #    message_toSend = "PlaySound"
        #    bytesToSend = str.encode(message_toSend)
    #
        #    ServerAdressPort = ("192.168.1.20", 8080)
    #
        #    UDPclientsocket = socket.socket(family = socket.AF_INET, type = socket.SOCK_DGRAM)
    #
        #    UDPclientsocket.sendto(bytesToSend, ServerAdressPort)

        def webserver():
            SERVER_HOST = '0.0.0.0'
            SERVER_PORT = 8000

            # Create socket
            server_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            server_socket.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
            server_socket.bind((SERVER_HOST, SERVER_PORT))
            server_socket.listen(1)
            #print('Listening on port %s ...' % SERVER_PORT)

            while True:   
                # Wait for client connections
                client_connection, client_address = server_socket.accept()


                # Get the client request
                request = client_connection.recv(1024).decode()
                print("request = %s"  % request)
                Spltrequest = request.split("\n")[0]
                Spltrequest =Spltrequest.split("/")[1]
                print(Spltrequest)
                if Spltrequest == "single HTTP":
                    print("sending")
                    send()
                
                #myevents=API_session.list_all('/incidents',params={'statuses[]':['triggered']})
                print('XXX outstanding=',len(myevents)," managed_to_send=",managed_to_send)
                # Send HTTP response
                if managed_to_send and len(myevents) == 0:
                    print("send button OK")
                    response = 'HTTP/1.0 200 OK\r\nHello World'
                    client_connection.sendall(response.encode())

                else:
                    print("send button ERROR")
                    response = 'HTTP/1.0 300 Error\r\n\r\n'
                    client_connection.sendall(response.encode())
                client_connection.close()



        webserver()
    except Exception as e:
        print("EXCEPTION ",str(e))
        traceback.print_exc()
        f = open("errorlog.txt", "a")
        msg = e
        f.write(str(e))
        f.close()

 
    time.sleep(4)
