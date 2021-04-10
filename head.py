class Head:
    '''
    h0: tipo de mensagem
    h1: id do sensor
    h2: id do servidor
    h3: número total de pacotes do arquivo
    h4: número do pacote sendo enviado
    h5: se handshake, id do arquivo / se dados, tamanho do payload
    h6: pacote solicitado para recomeço quando há erro no envio
    h7: último pacote recebido com sucesso
    h8-h9: CRC
    '''

    def __init__(self, h0, h1, h2, h3, h4, h5, h6, h7, h8, h9):
        self.h0 = h0.to_bytes(1, "big")
        self.h1 = h1.to_bytes(1, "big")
        self.h2 = h2.to_bytes(1, "big")
        self.h3 = h3.to_bytes(1, "big")
        self.h4 = h4.to_bytes(1, "big")
        self.h5 = h5.to_bytes(1, "big")
        self.h6 = h6.to_bytes(1, "big")
        self.h7 = h7.to_bytes(1, "big")
        self.h8 = h8.to_bytes(1, "big")
        self.h9 = h9.to_bytes(1, "big")

        self.msg_type = h0
        self.id_sensor = h1
        self.id_server = h2
        self.total_packages = h3
        self.n_package = h4
        self.head_5 = h5
        self.package_error = h6
        self.last_package = h7
        # self.tamanhoPayload = h8
        # self.parabens = h9


    def headToBytes(self):
        h0 = self.h0
        h1 = self.h1
        h2 = self.h2
        h3 = self.h3
        h4 = self.h4
        h5 = self.h5
        h6 = self.h6
        h7 = self.h7
        h8 = self.h8
        h9 = self.h9
        bytes = h0 + h1 + h2 + h3 + h4 + h5 + h6 + h7 + h8 + h9
        return bytes

        



