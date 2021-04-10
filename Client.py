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
from head import *
import time
import numpy as np
import os
import io
import subprocess
import logging
import PIL.Image as Image
import sys
import math

logging.basicConfig(filename='client4.log', filemode='w', format='CLIENT: - %(asctime)s - %(message)s', level=logging.INFO)


imageR = input("Digite o path da imagem: ")
assert os.path.exists(imageR), "Imagem não encontrada em "+str(imageR)
print("imagem localizada em: {}".format(imageR))


class Client():
    def __init__(self, imageR):
        logging.info("Iniciando!")
        serialNameT = "COM6"                          # Windows(variacao de)
        self.com1 = enlace(serialNameT)
        self.com1.enable()

        self.payloads = self.create_payloads(imageR)
        self.n_packages = len(self.payloads)          # número de pacotes
        # Head.h3 = self.n_packages

        # self.payload_size = b'\x00'
        self.payload_size = 0
        self.this_package = 1                         # pacode atual

        self.id_sensor = 1
        self.id_server = 2
        self.id_file = 1

        self.last_package = 0

        self.timeout = 1
        self.count = 1
        self.ready = False

        # self.corrige = False


    def divide_img(self, lis, n):
        # fragmentação  
        # em intervalos de n = 114 --> tamanho dos payloads predefinido
        for i in range(0, len(lis), n):
            yield lis[i:i+n]     
        

    def create_payloads(self, imageR):
        with open(imageR, "rb") as img:
            txBuffer = img.read()
        txLen = len(txBuffer)
        payloads = list(self.divide_img(txBuffer, payloadSize)) # coloca pedaços que foram divididos em uma lista
        # print(payloads)
        return payloads 

    def create_handshake(self, payload_size):
        print("Criando Handshake...")
        head_handshake = Head(1, self.id_sensor, self.id_server, self.n_packages, 0, 1, 0, 0, 0, 0).headToBytes()
        # n_packages = self.n_packages.to_bytes(4, 'big')        
        # handshake = n_packages + b'\x00\x00\x00\x00' + b'\x00\x00'
        
        handshake = head_handshake + eop

        print("Handshake is {}".format(handshake))
        print("-----------------------------------------")
        return handshake

    def send_handshake(self):
        # Envia hanshake para o server
        handshake = self.create_handshake(self.payload_size)
        print("---------------------")
        print("Enviando handshake...")
        print("---------------------")

        if handshake[0] == 1:
            print("Tipo de mensagem: {} - Mensagem do handshake".format(handshake[1]))
            self.com1.sendData(handshake)
            logging.info(f"Envio | Tipo de mensagem: T1 | Tamanho: 14")
            print("handshake enviado")
            print("---------------------")
            self.handshake_response()


    def handshake_response(self):
        # recebe resposta do handshake, confirmando recebimento
        
        t_inicial = time.time()
        response = False
        nHandshakeRes = 0

        while response == False:            
            
            if self.com1.rx.getBufferLen() >= 14: 
                handshakeRes, nHandshakeRes = self.com1.getData(14)
                print("Resposta do handshake recebida.")
                print("-------------------------------")

            time_elapsed = time.time() - t_inicial

            if nHandshakeRes > 0 and handshakeRes[0] == 2:    
                logging.info(f"Recebimento | Tipo de mensagem: T2 | Tamanho: 14")
                print("Tipo de mensagem: {} - Servidor ocioso, pronto para receber mensagens".format(handshakeRes[0]))            
                self.ready = True
                print("ready is {}".format(self.ready))
                # if handshakeRes[0] == 2:
                response = True                
                break

            else:
                self.ready = False
                # print("ready is {}".format(self.ready))
            
            if self.count > 4:
                print("________________________________________")
                print("Todas tentativas falharam. Encerrando...")
                logging.info(f"Tentativa de envio | Tipo de mensagem: T5 - tempo de resposta do server excedeu 20s | Tamanho: 14")

                print("Tipo de mensagem: T5 - Espera pelo server excedeu 20s")

                self.com1.disable()
                sys.exit()


            if time_elapsed > 5:
                # try_again = input("Servidor inativo. Tentar novamente? S/N   ")
                # if try_again == "N" or try_again == "n":
                #     self.com1.disable() 
                #     sys.exit()                
                # else:
                response = False
                print(time_elapsed)
                print("____________________________________________________________________________")
                print("Timeout. Nenhuma resposta recebida do servidor. Tentando enviar novamente...")
                print("Tentativa {}".format(self.count))  
                self.count += 1   

                break  


    def create_head(self, n):
        # Cria o head dos pacotes, que informa 
        # quantidade de pacotes, pacote a ser enviado e o id do envio.  
          
        # n_packages = self.n_packages.to_bytes(1, 'big') #Quantidade de pacotes

        # Teste informando tamanho errado do payload
        # len_payloads = len(self.payloads[n-1]) +1

        len_payloads = len(self.payloads[n-1])
        # payload_size = len_payloads.to_bytes(1,'big')
        print("Tamanho do payload: {}".format(len_payloads))

        head = Head(3, self.id_sensor, self.id_server, self.n_packages, n, len_payloads, 0, self.last_package, 0, 0).headToBytes()
        # Head(3, self.id_sensor, self.id_server, self.n_packages, n, len_payloads, 0, self.last_package, 0, 0).print_msg()
        print("HEAD IS: {}".format(head))
        print("Tipo de mensagem: {} - Mensagem de dados".format(head[0]))
        return head

    def create_package(self, head, this_package):
        package = head + self.payloads[this_package-1] + eop
        # print(head[2])
        # print(package)
        return package

    def send_package(self, package):
        self.com1.sendData(package)
        logging.info(f"ENvio | Tipo de mensagem: T3 | Tamanho: 128 | Pacote: {self.this_package} | Total de pacotes: {self.n_packages}")

    def package_response(self):
        # Recebe confirmação do server
        packResponse, nPackResponse = self.com1.getData(14)

        print(packResponse)

        if packResponse[0] == 4:
        # print(packResponse)
            logging.info(f"Recebimento | Tipo de mensagem: T4 | Tamanho: 14 | Pacote: {self.this_package} | Total de pacotes: {self.n_packages}")
            print("----------------------------")
            print("Mensagem recebida: {} - Pacote recebido pelo servidor".format(packResponse[0]))
            print("Resposta do pacote recebida.")
            print("----------------------------")     

        elif packResponse[0] == 6:
            logging.info(f"Recebimento | Tipo de mensagem: T6 | Tamanho: 14")

            print("-------------------------------------------")
            print("Mensagem recebida: {} - mensagem inválida".format(packResponse[0]))
            print("Número correto esperado pelo servidor: {}".format(packResponse[6]))  
            print("Pacote recebido: {}".format(packResponse[4]))
            print("-------------------------------------------")
            
            self.com1.disable()
            sys.exit()

    # def ordem_errada(self):
    #     '''
    #     Cria pacotes na ordem errada
    #     '''
    #     head1 = b'\x03' + self.id_client + self.id_server + b'\x02' + b'\x01' + b'\x00' + b'\x00' + b'\x00' + crc
    #     head2 = b'\x03' + self.id_client + self.id_server + b'\x02' + b'\x03' + b'\x00' + b'\x00' + b'\x00' + crc
    #     pack1 = head1 + eop
    #     pack2 = head2 + eop
    #     list_packages = [pack1, pack2]
    #     return list_packages


    def main(self):
        while not self.ready:
            self.send_handshake()
        t_inicial = time.time()

        while self.this_package <= self.n_packages and self.ready:
            print("Recebendo pacotes...")
            print("--------------------")
            
            # Para o teste de pacotes:

            # if self.corrige == False:

            #     self.this_package = self.this_package + 1
            #     head = self.create_head(self.this_package)

       
            head = self.create_head(self.this_package)
            package = self.create_package(head, self.this_package)

            self.send_package(package)
            print(f"Pacote {self.this_package}/{self.n_packages} enviado")

            response_package = True

            while self.com1.rx.getIsEmpty():
                # print("entrou nesse while")
                time_elapsed = time.time() - t_inicial
                response_package = True
                if time_elapsed > 5:
                    response_package = False
                    break

            if response_package:
                print("resposta do pacote {} recebida".format(self.this_package))
                self.package_response()


                        
                if self.this_package == self.n_packages:
                    self.com1.rx.clearBuffer()
                    print("Todos pacotes enviados")
                    self.com1.disable()
                    sys.exit()

                # if self.corrige == False:
                self.this_package +=1
                print("Pacote atual: {}".format(self.this_package))                     
                     


            elif self.timeout <= 4:
                print("___________________________________________")
                print(" ")
                print("Nenhuma resposta recebida sobre o pacote {}".format(self.this_package))
                print("Tentando novamente...")

                print("Tentativa {}".format(self.timeout))                     
                self.timeout += 1
                self.send_package(package)                      
                print("___________________________________________")

            
            else:
                print(" ")
                print("Timeout! Tentativa de envio falhou 4 vezes.")
                logging.info(f"Envio | Tipo de mensagem: T5 | tamanho: 10 (apenas o head) | Encerrando comunicação.")
                head = Head(5, 0, 0, 0, 0, 0, 0, 0, 0, 0).headToBytes()
                self.send_package(head)  
                self.com1.disable()
                sys.exit()



            t_inicial = time.time()

            # print(self.this_package)

        if self.this_package == self.n_packages:
            self.com1.rx.clearBuffer()
            print("Todos pacotes enviados")
            sys.exit()

client = Client(imageR)
client.main()
                









# create_payloads(imageR)  
# print("Payloads criados com sucesso!")
# print("-----------------------------")
    # def main():
    #     try:
    #         com1 = enlace(serialNameT)
    #         com1.enable()

    #         print("Client TX ativado em: {}".format(serialNameT))
    #         print("Comunicação aberta com sucesso!")
    #         print("---------------------")

            # header = len(txBuffer).to_bytes(2, 'big')
            # header_int = int.from_bytes(header, "big")
            # print("Enviando header")
                
            # print("--------------------")        
            # com1.sendData(np.asarray(header))
            # print("enviado com sucesso!")
            # print("Header: {}".format(header)) 
            # print("Tamanho enviado: {}".format(header_int))
            # print("--------------------")

            # headerR, nHR = com1.getData(2)
            # headerR_int = int.from_bytes(headerR, "big")

            # print("Resposta do header: {}".format(headerR))
            # print("Tamanho recebido: {}".format(headerR_int))
            # print("Recebida resposta do header")
            # print("--------------------")

            # if header_int == headerR_int:

            #     print("iniciando time...")
            #     timeStart = time.time()
            #     print("---------------------")

            #     print("Enviando payload")
            #     print("--------------------")
            #     com1.sendData(np.asarray(txBuffer))

            #     print("Esperando resposta...")
            #     rxBuffer, nRx  = com1.getData(txLen) 
            #     print("Procedimento concluído") 

            #     tempo = time.time() - timeStart
            #     taxa = txLen/tempo
                
            #     print("___________________________________________________")   
            #     print("Tempo gasto para envio e recebimento: {}".format(round(tempo, 3)))
            #     print("Taxa de transmissão (bytes por segundo): {}".format(round(taxa, 3)))
            #     print("___________________________________________________")

            #     print("-------------------------")
            #     print("Comunicação encerrada")
            #     print("-------------------------")
            # com1.disable()

            
#         except Exception as erro:
#             print("ops! :-\\")
#             print(erro)
#             com1.disable()
        

#     #so roda o main quando for executado do terminal ... se for chamado dentro de outro modulo nao roda
# if __name__ == "__main__":
#     main() 