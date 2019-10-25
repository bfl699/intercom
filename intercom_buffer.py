# Adding a buffer.

import sounddevice as sd
import numpy as np
import struct
from intercom import Intercom
import sounddevice as sd                                                        # https://python-sounddevice.readthedocs.io
import numpy                                                                    # https://numpy.org/
import argparse                                                                 # https://docs.python.org/3/library/argparse.html
import socket                                                                   # https://docs.python.org/3/library/socket.html
import queue

<<<<<<< HEAD

if __debug__:
    import sys
    
class Intercom_buffer(Intercom):

    #Definir en init la estructura principal del buffer
    def init(self, args):
        Intercom.init(self, args)
        self.buffer_size=args.buffer_size
        self.buf=[]
        for x in range(self.buffer_size):
            self.list.append([])

        self.num_packet_send=0
        self.num_packet_receive=0
        self.bytes=0

    def run(self):
        sending_sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        receiving_sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        listening_endpoint = ("0.0.0.0", self.listening_port)
        receiving_sock.bind(listening_endpoint)

        
        def receive_and_buffer():
            message, source_address = receiving_sock.recvfrom(Intercom.max_packet_size)
            #falta
            
            time.sleep(0.5)
        
        def record_send_and_play(indata, outdata, frames, time, status):
            sending_sock.sendto(indata, (self.destination_IP_addr, self.destination_port))

            #falta
        
=======
if __debug__:
    import sys

class Intercom_buffer(Intercom):

    MAX_CHUNK_NUMBER = 65536

    def init(self, args):
        Intercom.init(self, args)
        self.chunks_to_buffer = args.chunks_to_buffer
        self.cells_in_buffer = self.chunks_to_buffer * 2
        self._buffer = [self.generate_zero_chunk()] * self.cells_in_buffer
        self.packet_format = f"H{self.samples_per_chunk}h"
        if __debug__:
            print(f"chunks_to_buffer={self.chunks_to_buffer}")

    def run(self):

        self.recorded_chunk_number = 0
        self.played_chunk_number = 0

        def receive_and_buffer():
            message, source_address = self.receiving_sock.recvfrom(Intercom.MAX_MESSAGE_SIZE)
            chunk_number, *chunk = struct.unpack(self.packet_format, message)
            self._buffer[chunk_number % self.cells_in_buffer] = np.asarray(chunk).reshape(self.frames_per_chunk, self.number_of_channels)
            return chunk_number

        def record_send_and_play(indata, outdata, frames, time, status):
            message = struct.pack(self.packet_format, self.recorded_chunk_number, *(indata.flatten()))
            self.recorded_chunk_number = (self.recorded_chunk_number + 1) % self.MAX_CHUNK_NUMBER
            self.sending_sock.sendto(message, (self.destination_IP_addr, self.destination_port))
            chunk = self._buffer[self.played_chunk_number % self.cells_in_buffer]
            self._buffer[self.played_chunk_number % self.cells_in_buffer] = self.generate_zero_chunk()
            self.played_chunk_number = (self.played_chunk_number + 1) % self.cells_in_buffer
            outdata[:] = chunk
            if __debug__:
                sys.stderr.write("."); sys.stderr.flush()

        with sd.Stream(samplerate=self.frames_per_second, blocksize=self.frames_per_chunk, dtype=np.int16, channels=self.number_of_channels, callback=record_send_and_play):
            print("-=- Press CTRL + c to quit -=-")
            first_received_chunk_number = receive_and_buffer()
            self.played_chunk_number = (first_received_chunk_number - self.chunks_to_buffer) % self.cells_in_buffer
            while True:
                receive_and_buffer()

    def add_args(self):
        parser = Intercom.add_args(self)
        parser.add_argument("-cb", "--chunks_to_buffer", help="Number of chunks to buffer", type=int, default=32)
        return parser
>>>>>>> 9e190ef425611ee1cef3a5876b5b2ea23f55d8ff

if __name__ == "__main__":
    intercom = Intercom_buffer()
    parser = intercom.add_args()
    args = parser.parse_args()
    intercom.init(args)
    intercom.run()
