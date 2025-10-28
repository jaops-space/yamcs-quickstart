#!/usr/bin/env python3

import binascii
import io
import socket
import sys
import argparse

from struct import unpack_from
from threading import Thread
from time import sleep


parser = argparse.ArgumentParser(description='Yamcs Dual-Instance Simulator')
parser.add_argument('--testdata', type=str, default='testdata.ccsds', help='simulated testdata.ccsds data')

# telemetry
parser.add_argument('--tm_host', type=str, default='127.0.0.1', help='TM host')
parser.add_argument('--tm_port', type=int, default=10015, help='TM port for first instance')
parser.add_argument('-r', '--rate', type=int, default=1, help='TM playback rate. 1 = 1Hz, 10 = 10Hz, etc.')

# telecommand
parser.add_argument('--tc_host', type=str, default='127.0.0.1', help='TC host')
parser.add_argument('--tc_port', type=int, default=10025, help='TC port for first instance')

args = vars(parser.parse_args())

# telemetry data file
TEST_DATA = args['testdata']

# primary host/port info
TM_SEND_ADDRESS = args['tm_host']
TC_RECEIVE_ADDRESS = args['tc_host']
RATE = args['rate']


def send_tm(simulator):
    """
    Sends telemetry packets to both Yamcs instances
    (Instance1: 10015 / Instance2: 10016)
    """
    tm_socket = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    tm_socket_dual = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)

    with io.open(TEST_DATA, 'rb') as f:
        simulator.tm_counter = 1
        header = bytearray(6)

        while f.readinto(header) == 6:
            (length,) = unpack_from('>H', header, 4)
            packet = bytearray(length + 7)
            f.seek(-6, io.SEEK_CUR)
            f.readinto(packet)

            # send to both Yamcs instances
            tm_socket.sendto(packet, (TM_SEND_ADDRESS, 10015))
            tm_socket_dual.sendto(packet, (TM_SEND_ADDRESS, 10016))

            simulator.tm_counter += 1
            sleep(1 / simulator.rate)


def receive_tc(simulator):
    """
    Listens for telecommands from both Yamcs instances
    (Instance1: 10025 / Instance2: 10026)
    """
    def listener(port):
        sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        sock.bind((TC_RECEIVE_ADDRESS, port))
        while True:
            data, _ = sock.recvfrom(4096)
            simulator.last_tc = data
            simulator.tc_counter += 1

    # Start two TC listeners
    for port in [10025, 10026]:
        t = Thread(target=listener, args=(port,))
        t.daemon = True
        t.start()


class Simulator:
    def __init__(self, rate):
        self.tm_counter = 0
        self.tc_counter = 0
        self.tm_thread = None
        self.tc_thread = None
        self.last_tc = None
        self.rate = rate

    def start(self):
        # Start telemetry sender
        self.tm_thread = Thread(target=send_tm, args=(self,))
        self.tm_thread.daemon = True
        self.tm_thread.start()

        # Start telecommand receiver (dual)
        self.tc_thread = Thread(target=receive_tc, args=(self,))
        self.tc_thread.daemon = True
        self.tc_thread.start()

    def print_status(self):
        cmdhex = None
        if self.last_tc:
            cmdhex = binascii.hexlify(self.last_tc).decode('ascii')
        return 'Sent: {} packets. Received: {} commands. Last command: {}'.format(
            self.tm_counter, self.tc_counter, cmdhex
        )


if __name__ == '__main__':
    simulator = Simulator(RATE)
    simulator.start()

    sys.stdout.write(f'Using playback rate of {RATE}Hz\n')
    sys.stdout.write(f'TM host={TM_SEND_ADDRESS}, TM ports=[10015, 10016]\n')
    sys.stdout.write(f'TC host={TC_RECEIVE_ADDRESS}, TC ports=[10025, 10026]\n')

    try:
        prev_status = None
        while True:
            status = simulator.print_status()
            if status != prev_status:
                sys.stdout.write('\r' + status)
                sys.stdout.flush()
                prev_status = status
            sleep(0.5)
    except KeyboardInterrupt:
        sys.stdout.write('\n')
        sys.stdout.flush()
