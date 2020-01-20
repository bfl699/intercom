# Using the Discrete Wavelet Transform, convert the chunks of samples
# intro chunks of Wavelet coefficients (coeffs).
#
# The coefficients require more bitplanes than the original samples,
# but most of the energy of the samples of the original chunk tends to
# be into a small number of coefficients that are localized, usually
# in the low-frequency subbands:
#
# (supposing a chunk with 1024 samples)
#
# Amplitude
#     |       +                      *
#     |   *     *                  *
#     | *        *                *
#     |*          *             *
#     |             *       *
#     |                 *
#     +------------------------------- Time
#     0                  ^        1023 
#                |       |       
#               DWT  Inverse DWT 
#                |       |
#                v
# Amplitude
#     |*
#     |
#     | *
#     |  **
#     |    ****
#     |        *******
#     |               *****************
#     +++-+---+------+----------------+ Frequency
#     0                            1023
#     ^^ ^  ^     ^           ^
#     || |  |     |           |
#     || |  |     |           +--- Subband H1 (16N coeffs)
#     || |  |     +--------------- Subband H2 (8N coeffs)
#     || |  +--------------------- Subband H3 (4N coeffs)
#     || +------------------------ Subband H4 (2N coeffs)
#     |+-------------------------- Subband H5 (N coeffs)
#     +--------------------------- Subband L5 (N coeffs)
#
# (each channel must be transformed independently)
#
# This means that the most-significant bitplanes, for most chunks
# (this depends on the content of the chunk), should have only bits
# different of 0 in the coeffs that belongs to the low-frequency
# subbands. This will be exploited in a future issue.
#
# The straighforward implementation of this issue is to transform each
# chun without considering the samples of adjacent
# chunks. Unfortunately this produces an error in the computation of
# the coeffs that are at the beginning and the end of each subband. To
# compute these coeffs correctly, the samples of the adjacent chunks
# i-1 and i+1 should be used when the chunk i is transformed:
#
#   chunk i-1     chunk i     chunk i+1
# +------------+------------+------------+
# |          OO|OOOOOOOOOOOO|OO          |
# +------------+------------+------------+
#
# O = sample
#
# (In this example, only 2 samples are required from adajact chunks)
#
# The number of ajacent samples depends on the Wavelet
# transform. However, considering that usually a chunk has a number of
# samples larger than the number of coefficients of the Wavelet
# filters, we don't need to be aware of this detail if we work with
# chunks.


import struct
import numpy as np
import matplotlib.pyplot as plt
import pywt as wt
from intercom import Intercom
from intercom_empty import Intercom_empty


#Numero de trozos totales
number_of_samples = 1024
levels = 4
# Wavelet used
#wavelet = 'haar'
#wavelet = 'bior1.3'
#wavelet = 'bior1.5'
#wavelet = 'bior3.3'
wavelet = 'bior3.5'
#wavelet = 'rbio1.3'
#wavelet = 'rbio3.5'
#wavelet = "db5"
#wavelet = "coif3"
#wavelet = "dmey"

#padding = "symmetric"
padding = "periodization"

if __debug__:
    import sys

class Intercom_DWT(Intercom_empty):
    

    def init(self, args):
        Intercom_empty.init(self, args)
        
        #Definimos la energia de la señal X //No se tiene en cuenta en esta parte
    def energy(x):
        return np.sum(x*x)/len(x)
        
    def send(self, indata):
        signs = indata & 0x8000
        magnitudes = abs(indata)
        indata = signs | magnitudes
        self.NOBPTS = int(0.75*self.NOBPTS + 0.25*self.NORB)
        self.NOBPTS += self.skipped_bitplanes[(self.played_chunk_number+1) % self.cells_in_buffer]
        self.skipped_bitplanes[(self.played_chunk_number+1) % self.cells_in_buffer] = 0
        self.NOBPTS += 1

        if self.NOBPTS > self.max_NOBPTS:
            self.NOBPTS = self.max_NOBPTS

        #Transformamos para obtener los coeficientes
        self.arr_flat = indata[:,0].flatten()
        self.coeffs = wt.wavedec(self.arr_flat, wavelet=wavelet, level=levels, mode=padding)
        self.arr, self.coeff_slices = wt.coeffs_to_array(self.coeffs)
        #Mandarlo por 1 o los 2 canales?
        #Comprobacion solo 1 canal // ERROR
        last_BPTS = self.max_NOBPTS - self.NOBPTS - 1

        self.send_bitplane(self.arr, self.coeff_slices, self.max_NOBPTS-1, 0)
        self.send_bitplane(self.arr, self.coeff_slices, self.max_NOBPTS-2, 0)
        
        for bitplane_number in range(self.max_NOBPTS-3, last_BPTS, -1):
            self.send_bitplane(self.arr, self.coeffs_slices, bitplane_number, 0)
            
        self.recorded_chunk_number = (self.recorded_chunk_number + 1) % self.MAX_CHUNK_NUMBER

        def send_bitplane(self, indata, indata2, bitplane_number, channel):
            bitplane = (indata[:,] >> bitplane_number//self.number_of_channels) & 1
            if np.any(bitplane): 
                bitplane = bitplane.astype(np.uint8)
                bitplane = np.packbits(bitplane)
                message = struct.pack(self.packet_format, self.recorded_chunk_number, bitplane_number, self.received_bitplanes_per_chunk[(self.played_chunk_number+1) % self.cells_in_buffer]+1, *bitplane)
                self.sending_sock.sendto(message, (self.destination_IP_addr, self.destination_port))
            else:
                self.skipped_bitplanes[self.recorded_chunk_number % self.cells_in_buffer] += 1

    def receive_and_buffer(self):
        message, source_address = self.receiving_sock.recvfrom(Intercom.MAX_MESSAGE_SIZE)
        received_chunk_number, received_bitplane_number, self.NORB, *bitplane = struct.unpack(self.packet_format, message) #añadir channel?
        bitplane = np.asarray(bitplane, dtype=np.uint8)
        bitplane = np.unpackbits(bitplane)
        bitplane = bitplane.astype(np.uint16)
        bitplane= bitplane.flatten()
        
        #Recibir arrays de coeficientes
        
        coeffs_from_arr = wt.array_to_coeffs(arr1, arr2, output_format="wavedec") #reacemos los coeficientes de la forma original del array
        #samples = wt.waverec(coeffs_from_arr, wavelet=wavelet, mode=padding)
        coeffs_from_arr = wt.astype(np.uint32)
        self._buffer[received_chunk_number % self.cells_in_buffer][:, channel] |= (bitplane << received_bitplane_number//self.number_of_channels)
        return received_chunk_number
    

if __name__ == "__main__":
    intercom = Intercom_DWT()
    parser = intercom.add_args()
    args = parser.parse_args()
    intercom.init(args)
    intercom.run()
