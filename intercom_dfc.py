# Implements a Data-Flow Control algorithm.
#
# The receiver sends back (using piggybacking) the number of received
# bitplanes of the played chunk. The sender sends in the next chunk
# this number of bitplanes plus one. An weighted average is used to
# filter the fast changes in the link bandwidth. Sign-magnitude
# representation is used to minimize the distortion of the partially
# received negative samples.

<<<<<<< HEAD
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

    
=======
import struct
import numpy as np
from intercom import Intercom
from intercom_binaural import Intercom_binaural

if __debug__:
    import sys

class Intercom_DFC(Intercom_binaural):

    def init(self, args):
        Intercom_binaural.init(self, args)
        self.packet_format = f"!HBB{self.frames_per_chunk//8}B"
        self.received_bitplanes_per_chunk = [0]*self.cells_in_buffer
        self.max_NOBPTS = 16*self.number_of_channels  # Maximum Number Of Bitplanes To Send
        self.NOBPTS = self.max_NOBPTS
        self.NORB = self.max_NOBPTS  # Number Of Received Bitplanes

    def receive_and_buffer(self):
        message, source_address = self.receiving_sock.recvfrom(Intercom.MAX_MESSAGE_SIZE)
        received_chunk_number, received_bitplane_number, self.NORB, *bitplane = struct.unpack(self.packet_format, message)
        bitplane = np.asarray(bitplane, dtype=np.uint8)
        bitplane = np.unpackbits(bitplane)
        bitplane = bitplane.astype(np.uint16)
        self._buffer[received_chunk_number % self.cells_in_buffer][:, received_bitplane_number%self.number_of_channels] |= (bitplane << received_bitplane_number//self.number_of_channels)
        self.received_bitplanes_per_chunk[received_chunk_number % self.cells_in_buffer] += 1
        return received_chunk_number

    def send_bitplane(self, indata, bitplane_number):
        bitplane = (indata[:, bitplane_number%self.number_of_channels] >> bitplane_number//self.number_of_channels) & 1
        bitplane = bitplane.astype(np.uint8)
        bitplane = np.packbits(bitplane)
        message = struct.pack(self.packet_format, self.recorded_chunk_number, bitplane_number, self.received_bitplanes_per_chunk[(self.played_chunk_number+1) % self.cells_in_buffer]+1, *bitplane)
        self.sending_sock.sendto(message, (self.destination_IP_addr, self.destination_port))
    
    def send(self, indata):
        signs = indata & 0x8000
        magnitudes = abs(indata)
        indata = signs | magnitudes
        
        self.NOBPTS = int(0.75*self.NOBPTS + 0.25*self.NORB)
        self.NOBPTS += 1
        if self.NOBPTS > self.max_NOBPTS:
            self.NOBPTS = self.max_NOBPTS
        last_BPTS = self.max_NOBPTS - self.NOBPTS - 1
        self.send_bitplane(indata, self.max_NOBPTS-1)
        self.send_bitplane(indata, self.max_NOBPTS-2)
        for bitplane_number in range(self.max_NOBPTS-3, last_BPTS, -1):
            self.send_bitplane(indata, bitplane_number)
        self.recorded_chunk_number = (self.recorded_chunk_number + 1) % self.MAX_CHUNK_NUMBER

    def record_send_and_play_stereo(self, indata, outdata, frames, time, status):
        indata[:,0] -= indata[:,1]
        self.send(indata)
        chunk = self._buffer[self.played_chunk_number % self.cells_in_buffer]
        signs = chunk >> 15
        magnitudes = chunk & 0x7FFF
        #chunk = ((~signs & magnitudes) | ((-magnitudes) & signs))
        chunk = magnitudes + magnitudes*signs*2
        self._buffer[self.played_chunk_number % self.cells_in_buffer]  = chunk
        self._buffer[self.played_chunk_number % self.cells_in_buffer][:,0] += self._buffer[self.played_chunk_number % self.cells_in_buffer][:,1]
        self.play(outdata)
        self.received_bitplanes_per_chunk [self.played_chunk_number % self.cells_in_buffer] = 0
        #print(*self.received_bitplanes_per_chunk)

    def record_send_and_play(self, indata, outdata, frames, time, status):
        self.send(indata)
        chunk = self._buffer[self.played_chunk_number % self.cells_in_buffer]
        signs = chunk >> 15
        magnitudes = chunk & 0x7FFF
        #chunk = ((~signs & magnitudes) | ((-magnitudes) & signs))
        chunk = magnitudes + magnitudes*signs*2
        self._buffer[self.played_chunk_number % self.cells_in_buffer]  = chunk
        self.play(outdata)
        self.received_bitplanes_per_chunk [self.played_chunk_number % self.cells_in_buffer] = 0
        #print(*self.received_bitplanes_per_chunk)
>>>>>>> efa5e546308d4f703e9159318cf4131f522a42c9

if __name__ == "__main__":
    intercom = Intercom_DFC()
    parser = intercom.add_args()
    args = parser.parse_args()
    intercom.init(args)
    intercom.run()

   
