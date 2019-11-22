# Transmitint bitplanes.

import sounddevice as sd
import numpy as np
import struct
from intercom import Intercom
from intercom_buffer import Intercom_buffer

if __debug__:
    import sys

class Intercom_bitplanes(Intercom_buffer):

    def init(self, args):
        Intercom_buffer.init(self, args)
        self.packet_format = f"!HB{self.frames_per_chunk//8}B"

    def receive_and_buffer(self):
        message, source_address = self.receiving_sock.recvfrom(Intercom.MAX_MESSAGE_SIZE)
        chunk_number, bitplane_number, *bitplane = struct.unpack(self.packet_format, message)
        bitplane = np.asarray(bitplane, dtype=np.uint8)
        bitplane = np.unpackbits(bitplane)
        bitplane = bitplane.astype(np.int16)
        self._buffer[chunk_number % self.cells_in_buffer][:, bitplane_number%self.number_of_channels] |= (bitplane << bitplane_number//self.number_of_channels)
        return chunk_number

    def send(self, indata):
        for bitplane_number in range(self.number_of_channels*16-1, -1, -1):
            bitplane = (indata[:, bitplane_number%self.number_of_channels] >> bitplane_number//self.number_of_channels) & 1
            bitplane = bitplane.astype(np.uint8)
            bitplane = np.packbits(bitplane)
            message = struct.pack(self.packet_format, self.recorded_chunk_number, bitplane_number, *bitplane)
            self.sending_sock.sendto(message, (self.destination_IP_addr, self.destination_port))


#Ahora lo recibe en un paquete UPD, habría que cambiarlo a que se envie
    #fragmentado,cada bit en un paquete, mas signidicativo a menos MSbP
    #el receptor debe reconstruir las muestras antes de reproducirlas
    #Transmita primero los planos de bits de cada canal entrelazándolos
    #(el plano de bits más significativo del canal izquierdo y luego
    #el plano de bits más significativo del canal derecho, y así sucesivamente)


    def init(self, args):
        Intercom.init(self, args)
        
        self.packet_format = f"!HB{self.samples_per_chunk//8}h" #//8 para reducir el
                                                            #tamaño, de 16 a 8
  
    def run(self):

        self.recorded_chunk_number = 0
        self.played_chunk_number = 0
    
 def receive_and_buffer():
            message, source_address = self.receiving_sock.recvfrom(Intercom.MAX_MESSAGE_SIZE)
            chunk_number, *plano = struct.unpack(self.packet_format,message)
        
            planoRecibido = np.unpackbits(np.asarray(plano,np.uint8))#Desempaqueta elementos de una matriz uint8 en una matriz de salida con valores binarios.
                                                                    #Convierta la entrada a una matriz int 8 -128 a 127
            planoEnviado = planoRecibido.astype(np.int16) # int16 Integer -32768 a 32767
               
            self._buffer[chunk_number % self.cells_in_buffer] = #falta
            return chunk_number

    #Cambiar 
     def record_send_and_play(indata, outdata, frames, time, status):
            message = struct.pack(self.packet_format, self.recorded_chunk_number, *(indata.flatten()))
            self.recorded_chunk_number = (self.recorded_chunk_number + 1) % self.MAX_CHUNK_NUMBER
            self.sending_sock.sendto(message, (self.destination_IP_addr, self.destination_port))
            chunk = self._buffer[self.played_chunk_number % self.cells_in_buffer]
            self._buffer[self.played_chunk_number % self.cells_in_buffer] = self.generate_zero_chunk()
            self.played_chunk_number = (self.played_chunk_number + 1) % self.cells_in_buffer
            outdata[:] = chunk


     with sd.Stream(samplerate=self.frames_per_second, blocksize=self.frames_per_chunk, dtype=np.int16, channels=self.number_of_channels, callback=record_send_and_play):
            print("-=- Press CTRL + c to quit -=-")
            first_received_chunk_number = receive_and_buffer()
            self.played_chunk_number = (first_received_chunk_number - self.chunks_to_buffer) % self.cells_in_buffer
            while True:
                receive_and_buffer()
                
        if __name__ == "__main__":
    intercom = Intercom_buffer()
    parser = intercom.add_args()
    args = parser.parse_args()
    intercom.init(args)
    intercom.run()