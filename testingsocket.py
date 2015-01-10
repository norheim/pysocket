from selectsocket import ServerKeeper
import time

serverKeeper = ServerKeeper(2005)

def responseFunc():
    for i in range(1, 10000):
        serverKeeper.tellClients(str(i/20.0)+','+str(i/20.0))
        print i
        time.sleep(0.1)

serverKeeper.waitForConnection(responseFunc)