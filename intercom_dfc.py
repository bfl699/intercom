# Implementing a Data-Flow Control algorithm.

import sounddevice as sd
import numpy as np
import struct

from intercom_binaural import Intercom_binaural

class Intercom_dfc(Intercom_binaural):
    

    def init(self, args):
        Intercom_binaural.init(self, args)
        self.packet_format = f"!HB{self.frames_per_chunk//8}B"
        #Transmitimos bitplanes 
        
        self.number_bitplanes_send = 16*self.number_of_channels
        self.received_bitplanes = dict([])
        for i in range(self.cells_buffer):
            self.received_bitplanes[i] = self.number_bitplanes_send

     def receive_and_buffer(self):
        message, source_address = self.receiving_sock.recvfrom(Intercom.MAX_MESSAGE_SIZE)
        chunk_number, bitplane_number,number_bitplanes_send,*bitplane = struct.unpack(self.packet_format, message) #Añadimos el numero de bitplanes al formato del paquete
        bitplane = np.asarray(bitplane, dtype=np.uint8)
        bitplane = np.unpackbits(bitplane)
        bitplane = bitplane.astype(np.int16)

        #Recibimos siempre un bitplane mas 
        self.received_bitplanes[chunk_number % self.cells_in_buffer]+=1
        
        return chunk_number
        

    def record_send_and_play_stereo(self, indata, outdata, frames, time, status):
        indata[:,0] -= indata[:,1]
        self.record_and_send(indata)
        self._buffer[self.played_chunk_number % self.cells_in_buffer][:,0] += self._buffer[self.played_chunk_number % self.cells_in_buffer][:,1]
        self.play(outdata)

    def record_and_send(self, indata):
        for bitplane_number in range(self.number_of_channels*16-1, -1, -1):
            bitplane = (indata[:, bitplane_number%self.number_of_channels] >> bitplane_number//self.number_of_channels) & 1
            bitplane = bitplane.astype(np.uint8)
            bitplane = np.packbits(bitplane)
            message = struct.pack(self.packet_format, self.recorded_chunk_number, bitplane_number, *bitplane)
            self.sending_sock.sendto(message, (self.destination_IP_addr, self.destination_port))
        self.recorded_chunk_number = (self.recorded_chunk_number + 1) % self.MAX_CHUNK_NUMBER


    def play(self, outdata):
        chunk = self.received_bitplanes[self.played_chunk_number % self.cells_in_buffer]
        
        self._buffer[self.played_chunk_number % self.cells_in_buffer] = self.generate_zero_chunk()
        self.played_chunk_number = (self.played_chunk_number + 1) % self.cells_in_buffer
        outdata[:] = chunk

        #En la reproducción contamos el número de trozos que se han recibido exitosamente
         contador =0
        for i in chunk:
        if self.received_bitplanes[i] >0: #Falta implementación
            contador +=1
            
        if __debug__:
            sys.stderr.write("."); sys.stderr.flush()

    

if __name__ == "__main__":
    intercom = Intercom_dfc()
    parser = intercom.add_args()
    args = parser.parse_args()
    intercom.init(args)
    intercom.run()

   
