import socket
import hashlib
import base64
import threading
import select
import time


class ServerKeeper(threading.Thread):
    LOCK = threading.Lock()
    MAGIC = '258EAFA5-E914-47DA-95CA-C5AB0DC85B11'
    HSHAKE_RESP = 'HTTP/1.1 101 Switching Protocols\r\n' + \
                  'Upgrade: websocket\r\n' + \
                  'Connection: Upgrade\r\n' + \
                  'Sec-WebSocket-Accept: %s\r\n' + \
                  '\r\n'

    def __init__(self, port):
        self.port = port
        self.s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self.s.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
        self.alive = True
        self.new_connection = False
        self.client_list = []

        threading.Thread.__init__(self)
        self.start()

    def run(self):
        self.s.bind(('', 2005))
        self.s.listen(5)
        print "Listening on port 2005"

        read_list = [self.s]
        while self.alive:
            print 'looping'
            readable, writable, error_ed = select.select(read_list, [], [], 1)
            for s in readable:
                if s is self.s:
                    client_socket, address = self.s.accept()
                    print "Connection from", address

                    if self.__handshake(client_socket):
                        read_list.append(client_socket)
                        self.client_list.append(client_socket)
                        self.new_connection = True
                        print "Handshake successful, Connection accepted"
                    else:
                        print "Handshake unsuccessful, Connection not accepted"
                else:
                    try:
                        data = self.__receive_data(s);
                    except Exception as e:
                        print("Exception %s" % (str(e)))
                        s.close()
                        read_list.remove(s)
                        self.client_list.remove(s)

        print 'escaped while loop'

    def close(self):
        self.alive = False

    def waitForConnection(self, func):
        self.new_connection = False
        while not self.new_connection:
            pass

        func()
        return

    def tellClients(self, message):
        encoded_message = bytearray([0b10000001, len(message)])
        # append the data bytes
        for d in bytearray(message):
            encoded_message.append(d)

        self.LOCK.acquire()
        for client in self.client_list:
            client.send(encoded_message)
        self.LOCK.release()

    def __handshake(self, connection):
        data = connection.recv(2048)

        headers = {}
        lines = data.splitlines()
        for l in lines:
            parts = l.split(": ", 1)
            if len(parts) == 2:
                headers[parts[0]] = parts[1]
        headers['code'] = lines[len(lines) - 1]

        key = headers['Sec-WebSocket-Key']
        resp_data = self.HSHAKE_RESP % (base64.b64encode(hashlib.sha1(key + self.MAGIC).digest()),)

        connection.send(resp_data)
        return True

    def __receive_data(self, client):
        # as a simple server, we expect to receive:
        # - all data at one go and one frame
        # - one frame at a time
        #    - text protocol
        #    - no ping pong messages
        data = bytearray(client.recv(512))

        if len(data) < 6:
            raise Exception("Error reading data")

        # FIN bit must be set to indicate end of frame
        assert (0x1 == (0xFF & data[0]) >> 7)
        # data must be a text frame
        # 0x8 check if client is still connected
        assert (0x1 == (0xF & data[0]))
        # assert that data is masked
        assert (0x1 == (0xFF & data[1]) >> 7)
        datalen = (0x7F & data[1])

        str_data = ''
        if datalen > 0:
            mask_key = data[2:6]
            masked_data = data[6:(6 + datalen)]
            unmasked_data = [masked_data[i] ^ mask_key[i % 4] for i in range(len(masked_data))]
            str_data = str(bytearray(unmasked_data))

        return str_data

serverKeeper = ServerKeeper(2005)

def responseFunc():
    for i in range(1, 10000):
        serverKeeper.tellClients(str(i/20.0)+','+str(i/20.0))
        print i
        time.sleep(0.1)

serverKeeper.waitForConnection(responseFunc)