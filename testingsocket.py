from selectsocket import ServerKeeper
import time

serverKeeper = ServerKeeper(2005)

for i in range(1, 10000):
    serverKeeper.tellClients(str(i)+','+str(i))
    print i
    time.sleep(0.1)
