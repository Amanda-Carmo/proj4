'''
Configurações pré-estabelecidas do enunciado
'''
from head import *

payloadSize = 114
eop = b'\xFF\xAA\xFF\xAA' 
timer = 0

# def createHandshake():
#     print("Criando Handshake\n")
#     headHandshake = Head(1, 1, 1, 1, 0, 1, 0, 0, 0, 0).headToBytes()
#     return headHandshake

# handshake = createHandshake()
# print(handshake)
