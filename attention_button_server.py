import socket
import time
import sys

while True:
    manage_to_send =False
    response = ""

    try:

        def send():
            room = b"Kitchen(button)"
            message = b"PlaySound:" + room
            TCP_IP = "192.168.1.20"
            TCP_PORT = 8080
            s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            s.settimeout(0.5)

            manage_to_send = False

            try:
                s.connect((TCP_IP, TCP_PORT))
                print("send to client")
                s.send(message)
                data = s.recv(1024).decode()
                print("received from client:", data) 
                if data == "PlaySound:Kitchen(button)":
                    manage_to_send = True
                    print("success from client")
            except socket.timeout:
                print("timeout from client")
           
            s.close()


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
            print('Listening on port %s ...' % SERVER_PORT)

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
                    send()

                # Send HTTP response
                if manage_to_send:
                    print("send200")
                    response = 'HTTP/1.0 200 OK\r\n\r\nHello World'
                    client_connection.sendall(response.encode())

                else:
                    print("send404")
                    response = "HTTP/1.0 404 Error\r\n\r\n"
                    client_connection.sendall(response.encode())
                client_connection.close()


        print ("send.py in main")

        webserver()
    except Exception as e:
        print(str(e))

 
    time.sleep(4)
    print("RESPAWN")


