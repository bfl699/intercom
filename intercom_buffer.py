from intercom import Intercom
import sounddevice as sd                                                        # https://python-sounddevice.readthedocs.io
import numpy                                                                    # https://numpy.org/
import argparse                                                                 # https://docs.python.org/3/library/argparse.html
import socket                                                                   # https://docs.python.org/3/library/socket.html
import queue


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
        

if __name__ == "__main__":
    intercom = Intercom_buffer()
    parser = intercom.add_args()
    args = parser.parse_args()
    intercom.init(args)
    intercom.run()
