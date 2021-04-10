#####################################################
# Camada Física da Computação
#Carareto
#11/08/2020
#Aplicação
####################################################


#esta é a camada superior, de aplicação do seu software de comunicação serial UART.
#para acompanhar a execução e identificar erros, construa prints ao longo do código! 


from enlace import *
from testes import *
import time
import numpy as np
import os
import io
import subprocess
import logging
import PIL.Image as Image
import sys
import time

imageW = './img/imgCopia.jpg'
logging.basicConfig(filename='server4.log', filemode='w', format='Server - %(asctime)s - %(message)s', level=logging.INFO)

class Server():
    def __init__(self):
        serialNameR = "COM3"                  # Windows(variacao de)
        self.com2 = enlace(serialNameR)
        self.com2.enable()
        print('comunicação aberta com sucesso')
        print("Server Rx habilitado em: {}".format(serialNameR))
        print("---------------------")

        self. n_packages = 0
        self.size = None
        self.nthis_package = 0
        self.eop = b'\xFF\xAA\xFF\xAA' 
        self.ready = False

        self.id_sensor = 1
        self.id_server = 2

        self.order_ok = True
        self.msg = None


    def receive_handshake(self):
        t_inicial = time.time()
        timer = 1

        if self.ready == False:
            print("Handshake é: {}".format(self.ready))
            while self.com2.rx.getIsEmpty():
                time_elapsed = time.time() - t_inicial
                if time_elapsed > 5:
                    print("Nenhuma mensagem recebida do client.")
                    print("Tentando novamente...")
                    print("---------------------")
                    logging.info(f"Time out {timer}/4")
                    timer += 1
                    t_inicial = time.time()
                
                if timer > 4:
                    print("=( ")
                    print("Tentativas falharam. Encerrando...")
                    print("--------------------")
                    self.com2.fisica.flush()
                    self.com2.disable()
                    sys.exit()
                    break

        print("Servidor pronto para receber mensagens.")
        print("---------------------------------------")

        handshake, nHandshake = self.com2.getData(14) #pegando um pacote inteiro (tamanho total de 14 bytes!)

        print(handshake)
        logging.info(f"Recebimento | Tipo de mensagem: T1 | Tamanho: 14")
        # self.size = int.from_bytes(handshake[3], "big")

        if handshake[0] == 1:
            self.size = handshake[5]         
            print("tamanho do pacote é: {}".format(self.size))

            self.n_packages = handshake[3]
            print("Total de pacotes: {}".format(self.n_packages))

            # print('tipo de mensagem: {}'.format(handshake[0]))
            self.ready = True   

    
    def create_handshakeResponse(self):
        # self.n_packages = self.n_packages.to_bytes(4, "big")
        handshake = Head(2, self.id_sensor, self.id_server, self.n_packages, 0, 1, 0, 0, 0, 0).headToBytes()
        handshake = handshake + eop
        # print("Tipo de mensagem:{} - Servidor ocioso. Pronto para receber mensagens".format(handshake[0]))
        print("Resposta do handshake é: {}".format(handshake))
        print("resposta do handshake criada")
        print("----------------------------")
        return handshake

    def send_handshakeResponse(self):
        logging.info(f"Envio | Tipo de mensagem: T2 | Tamanho: 14")
        handshake = self.create_handshakeResponse()

        #Teste 3 - Transmissão com ausência de resposta de handshake, por mais de 20 segundos 
        self.com2.sendData(handshake)
        print("Resposta do handshake enviada.")
        print("------------------------------")
        # self.n_packages = 1


    def send_packageResponse(self):
        logging.info(f"Envio | Tipo de mensagem: T4 | Tamanho: 14")

        n_packagesbyte = self.n_packages.to_bytes(4, 'big')
        head_response = Head(4, self.id_sensor, self.id_server, self.n_packages, self.nthis_package, 0, 0, 0, 0, 0).headToBytes()
        response = head_response + eop

        print("Mensagem enviada: {} - Pacote recebido pelo servidor". format(head_response[0]))

        # int_package = int.to_bytes(self.n_packages, 'big')   
             
        # print(self.nthis_package)
        # print(self.n_packages)

        # if self.nthis_package - 1 <= self.n_packages:
        #     self.com2.sendData(response)

        if self.nthis_package - 1 <= self.n_packages:
            self.com2.sendData(response)

            # ####################################### verificar:
            # if self.nthis_package - 1 == self.n_packages:
            #     self.com2.rx.clearBuffer()
            #     self.com2.disable()
            #     sys.exit()   
    
    
    def check_eop(self, head, eop):
        if eop == self.eop:
            print("eop correto")
            #Só enviará a resposta se o eop estievr correto
            if self.order_ok == True:
                print("------------------------------")
                print("Enviando resposta do pacote...")
                self.send_packageResponse()
                print("Resposta do pacote enviada")
                print("------------------------------")
            else:
                print("erro na ordem dos pacotes.")
        else:
            print("eop veio errado")
            print(eop)
            self.sendError_msg(self.nthis_package)
        pass

    def sendError_msg(self, error_pkg):
        logging.info(f"Envio | Tipo de mensagem: T6 | Tamanho: 14")
        head_error = Head(6, self.id_sensor, self.id_server, self.n_packages, error_pkg, 0, self.nthis_package, 0, 0, 0).headToBytes()
        error_package = head_error + eop
        print(error_package)

        self.com2.sendData(error_package)
        print("Mensagem de erro enviada.")
        self.com2.disable()
        sys.exit()

    def check_order(self, head):
        # Verificar se o número do pacote é um a mais do que o anterior.
        print("-----------------------------------")
        print("Checando a ordem")

        head_nPack = head[4]
        # print(head_nPack)
        # print(self.nthis_package)          

        if head_nPack == self.nthis_package:
            print("-------------")
            print("tudo em ordem")
            print("-------------")
            self.order_ok == True
            self.timer = time.time()
            # self.t_inicial = time.time()
            print(self.nthis_package)
            print(head_nPack)
            self.nthis_package += 1
        
        else:
            self.order_ok = False
            head_thisPack = head[4]
            print("Pacote {} fora de ordem. Enviando mensagem de erro...".format(head_thisPack))
            self.sendError_msg(head[4])
            


    def add_package(self, payload):
        # Adiciona o payload recebido ao existente.
        if self.msg == None or len(self.msg) == 0:
            self.msg = payload
            print("------------------------------------")
            print("Condição da mensagem antes como None")
            # print("msg is: {}".format(self.msg))
            print("------------------------------------")
            print("tamanho da msg: {}".format(len(self.msg)))
        else:
            self.msg += payload
            # print("msg is: {}".format(self.msg))  


    #________________RECEBENDO_PACOTES________________#


    def receive_package(self):
        # counter_data = 0
        print("----------------------------------------------")
        print("Iniciando processo para recepção do pacote....")
        print("----------------------------------------------")
        t_inicial = time.time()
        timer = 1

        while self.com2.rx.getIsEmpty():
            time_elapsed = time.time() - t_inicial
            if time_elapsed > 5:
                print("---------------------------")
                print("Nenhuma mensagem recebida.")
                print("Tentando novamente...")
                print("Tentativa {}".format(timer))
                print("---------------------------")
                timer += 1
                t_inicial = time.time()

            if timer > 4:
                logging.info("ENVIO | TIPO: T5 (TIMEOUT 20s) | ENCERRANDO...")
                print("Tentativas falharam. Encerrando...")
                self.com2.fisica.flush()
                self.com2.disable()
                sys.exit()
                break

        head = self.com2.rx.getNData(10)  
        logging.info(f"Recebimento | Tipo de mensagem: T3 | Tamanho: {head[5] + 14} | Pacote: {head[4]}/{head[3]}")         

        
        print("head is {}".format(head))
        
        self.check_order(head)

        head_idFile = head[5]



        if head[0] == 3:

            print("Mensagem recebida: {} - Mensagem de dados. Recebendo dados".format(head[0]))

            payload, nPayload = self.com2.getData(head_idFile)
        
            # Para teste com tamanho do payload não correspondente ao que foi informado
            # no header.
            # payload, nPayload = self.com2.getData(head_idFile + 1)

            if head[5] == nPayload: 
                # print("número de pacotes a serem recebidos: {}".format(head[9])
                print("------------------------------------------------------------------")
                print("ordem_ok is: {}".format(self.order_ok))

                if self.order_ok == True:
                    self.add_package(payload)
                    print(self.msg)
                    
                eop, nEop = self.com2.getData(4)
                self.check_eop(head, eop)
                print(eop)
                time.sleep(1)

                if self.nthis_package > self.n_packages:
                    print("todos os pacotes recebidos! Encerrando...")
                    print("-----------------------------------------")   
                    self.com2.disable()
                    sys.exit()  

            else: 
                print("-------------------------------------------------------------------------")
                print("Tamanho real do payload do pacote não corresponde ao informado pelo head.")
                print("-------------------------------------------------------------------------")
                self.com2.disable()
                sys.exit()
        


    #_______________________Main______________________#


    def main(self):
        while not self.ready:
            self.receive_handshake()
            time.sleep(1)
            self.send_handshakeResponse()

        self.nthis_package = 1
        # int_npackages = int.from_bytes(self.n_packages, 'big')
        print("Número dos pacotes: {}".format(self.n_packages))

        while self.nthis_package <= self.n_packages:
            self.t_inicial = time.time()
            self.timer = time.time()
            self.receive_package()

        f = open(imageW, 'wb')
        f.write(self.msg)
        self.com2.disable()

        sys.exit()

server = Server()
server.main()

    


        





            







# def getHandshake(com):
#     handshake, nHandshake = com.getData(14)
#     print("----------------------------------")
#     print("get do hanshake feito com sucesso!")
#     print("----------------------------------")
#     time.sleep(0.1)

    



# def main():
#     try:
#         #declaramos um objeto do tipo enlace com o nome "com". Essa é a camada inferior à aplicação. Observe que um parametro
#         #para declarar esse objeto é o nome da porta.
#         print("A recepção vai começar")        
        
#         com2 = enlace(serialNameR)

#         # Ativa comunicacao. Inicia os threads e a comunicação seiral 
#         com2.enable()

#         imageW = './img/' + input('Nomeie a imagem que vai receber! ') + 'Copia.jpg'

#         #Se chegamos até aqui, a comunicação foi aberta com sucesso. Faça um print para informar.
#         print('comunicação aberta com sucesso')
#         print("Server Rx habilitado em: {}".format(serialNameR))
#         print("---------------------")

#         print("local da imagem a ser salva: {}".format(imageW))
#         print("---------------------")        

#         print("Esperando Header...")
        
#         header, nHr = com2.getData(2)      
        
#         print("---------------------")
#         print("Header recebido com sucesso!")
#         print("---------------------")
#         time.sleep(1)


#         print("Enviando resposta do header para o cliente...")  
#         com2.sendData(np.asarray(header))
#         print("---------------------")

#         HeadR = int.from_bytes(header, "big")

#         print("Esperando dados do payload do cliente...")
#         print("--------------------")    

#         rxBuffer, nRx = com2.getData(HeadR)     

#         print("Payload recebido!")
#         print("--------------------")

#         print("Pasasando os dados para o cliente...")
#         com2.sendData(np.asarray(rxBuffer))
#         time.sleep(1)
#         print("--------------------")             
              

#         print("Salvando imagem em: {}".format(imageW))   
#         print(" - {}".format(imageW))


#         f = open(imageW, 'wb')
#         f.write(rxBuffer)

       
#         print("-------------------------")
#         print("Comunicação encerrada")
#         print("-------------------------")
#         com2.disable()

        
#     except Exception as erro:
#         print("ops! :-\\")
#         print(erro)
#         com2.disable()
        

#     #so roda o main quando for executado do terminal ... se for chamado dentro de outro modulo nao roda
# if __name__ == "__main__":
#     main()
