import time
from selectsocket import ServerKeeper

serverKeeper = ServerKeeper(2006)

for i in range(1, 10000):
    serverKeeper.tellClients(str(i)+','+str(i))
    print i
    time.sleep(0.1)
