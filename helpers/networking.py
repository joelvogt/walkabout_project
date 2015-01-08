#-*- coding:utf-8 -*-
__author__ = u'Joël Vogt'


from SimpleXMLRPCServer import SimpleXMLRPCServer
import socket

import helpers
import time
import math
import sys


GRP_SYN = 'SYN'
GRP_ACK = 'ACK'
TRANSMISSION_ERROR = 'ERR'
INIT_GROUP_SIZE = 30
MAX_SEND_DELAY = 24
MIN_SEND_DELAY = 4


class UDP_Node(object):
    def __init__(self, hostname, port, buffer_size):
        self._buffer_size = buffer_size
        self._hostname = hostname
        self._port = port
        self._udpSerSock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        sys.stdout.flush()
        self._peer_address = None
        self._message_group_size = 0
        self._messages_transmitted = 0


    def onStart(self):
        self._udpSerSock.bind((self._hostname,self._port))
        # self._udpSerSock.settimeout(10)

    def receive(self):
        while True:
            sys.stdin.flush()
            datagram, client_address = self._udpSerSock.recvfrom(self._buffer_size)
            if len(datagram.split('@')) == 2:
                counter, datagram = datagram.split('@')
                print('received nr %s' % counter)
            else:
                print('no conter')
            if not self._peer_address:
                self._peer_address = client_address
            if datagram[:3] == GRP_SYN:
                self._message_group_size = int(datagram[3:])
                continue
            elif datagram[:3] == TRANSMISSION_ERROR:
                sys.stdout.flush()
                print('error retransmit from %d' % self._messages_transmitted)
                self._udpSerSock.sendto('%s%d'% (TRANSMISSION_ERROR, self._messages_transmitted), self._peer_address)
                sys.stdout.flush()
                continue
            if self._message_group_size:
                self._messages_transmitted += 1
                if self._message_group_size == self._messages_transmitted:
                    sys.stdout.flush()
                    self._udpSerSock.sendto(GRP_ACK, self._peer_address)
                    sys.stdout.flush()
                    self._message_group_size = 0
                    self._messages_transmitted = 0
            return datagram

    def send(self, message):
        if self._peer_address is None:
            self._peer_address = (self._hostname, self._port)
        if self._message_group_size:
            self._message_group_size = 0
            self._messages_transmitted = 0
        if len(message) > self._buffer_size:

            group_size = INIT_GROUP_SIZE#  - int(math.log(len(message), 2))
            sys.stdout.flush()
            self._udpSerSock.sendto('%s%d' % (GRP_SYN, group_size), self._peer_address)
            sys.stdout.flush()
            group_cache = []
            for msg_c, x in enumerate(helpers.slice_evenly(message, self._buffer_size)):
                group_cache.append(x)
                sys.stdout.flush()
                self._udpSerSock.sendto('%d@%s' % (msg_c,x), self._peer_address)
                sys.stdout.flush()
                sleep_delay = MAX_SEND_DELAY - int(math.log10(len(message)))
                time.sleep(1.0/10**(sleep_delay if sleep_delay >= MIN_SEND_DELAY else MIN_SEND_DELAY))

                if group_size == len(group_cache):

                    self._udpSerSock.settimeout(0.1)
                    while True:
                        try:
                            sys.stdin.flush()
                            datagram, addr = self._udpSerSock.recvfrom(self._buffer_size)
                        except socket.timeout:
                            sys.stdout.flush()
                            self._udpSerSock.sendto(TRANSMISSION_ERROR, self._peer_address)
                            sys.stdout.flush()
                            self._udpSerSock.settimeout(5)
                            continue
                        if datagram == GRP_ACK:
                            sys.stdout.flush()
                            self._udpSerSock.sendto('%s%d' % (GRP_SYN, int(group_size)), self._peer_address)
                            sys.stdout.flush()
                            group_cache = []
                        elif datagram[:3] == TRANSMISSION_ERROR:

                            resend_from = int(datagram[3:])
                            for x in group_cache[resend_from:]:
                                print(x)
                                sys.stdout.flush()
                                self._udpSerSock.sendto(x, self._peer_address)
                                sys.stdout.flush()
                            # map(lambda x: self._udpSerSock.sendto(x, self._peer_address), group_cache)
                            continue
                        else:
                            print('Transmission error')
                        self._udpSerSock.settimeout(None)

                        break

        else:
            sys.stdout.flush()
            self._udpSerSock.sendto(message, self._peer_address)
            sys.stdout.flush()

    def __del__(self):
        print('calling del for networking')

        if self._peer_address is None or self._peer_address == (self._hostname, self._port):
            sys.stdout.flush()
            self._udpSerSock.sendto('-1', (self._hostname, self._port))
        sys.stdout.flush()
        sys.stdin.flush()
        self._udpSerSock.close()



class TCP_Server_Node(object):
    def __init__(self, hostname, port, buffer_size):
        self._buffer_size = buffer_size
        self._hostname = hostname
        self._port = port
        self._tcpSerSock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self._peer_address = None


    def onStart(self):
        self._tcpSerSock.bind((self._hostname, self._port))
        self._tcpSerSock.listen(5)

    def receive(self):
        datagram, client_address = self._tcpSerSock.accept()
        return datagram

    def send(self, message):
        if self._peer_address is None:
            self._peer_address = (self._hostname, self._port)
        if self._message_group_size:
            self._message_group_size = 0
            self._messages_transmitted = 0
        if len(message) > self._buffer_size:

            group_size = INIT_GROUP_SIZE#  - int(math.log(len(message), 2))
            sys.stdout.flush()
            self._udpSerSock.sendto('%s%d' % (GRP_SYN, group_size), self._peer_address)
            sys.stdout.flush()
            group_cache = []
            for msg_c, x in enumerate(helpers.slice_evenly(message, self._buffer_size)):
                group_cache.append(x)
                sys.stdout.flush()
                self._udpSerSock.sendto('%d@%s' % (msg_c,x), self._peer_address)
                sys.stdout.flush()
                sleep_delay = MAX_SEND_DELAY - int(math.log10(len(message)))
                time.sleep(1.0/10**(sleep_delay if sleep_delay >= MIN_SEND_DELAY else MIN_SEND_DELAY))

                if group_size == len(group_cache):

                    self._udpSerSock.settimeout(0.1)
                    while True:
                        try:
                            sys.stdin.flush()
                            datagram, addr = self._udpSerSock.recvfrom(self._buffer_size)
                        except socket.timeout:
                            sys.stdout.flush()
                            self._udpSerSock.sendto(TRANSMISSION_ERROR, self._peer_address)
                            sys.stdout.flush()
                            self._udpSerSock.settimeout(5)
                            continue
                        if datagram == GRP_ACK:
                            sys.stdout.flush()
                            self._udpSerSock.sendto('%s%d' % (GRP_SYN, int(group_size)), self._peer_address)
                            sys.stdout.flush()
                            group_cache = []
                        elif datagram[:3] == TRANSMISSION_ERROR:

                            resend_from = int(datagram[3:])
                            for x in group_cache[resend_from:]:
                                print(x)
                                sys.stdout.flush()
                                self._udpSerSock.sendto(x, self._peer_address)
                                sys.stdout.flush()
                            # map(lambda x: self._udpSerSock.sendto(x, self._peer_address), group_cache)
                            continue
                        else:
                            print('Transmission error')
                        self._udpSerSock.settimeout(None)

                        break

        else:
            sys.stdout.flush()
            self._udpSerSock.sendto(message, self._peer_address)
            sys.stdout.flush()

    def __del__(self):
        print('calling del for networking')

        if self._peer_address is None or self._peer_address == (self._hostname, self._port):
            sys.stdout.flush()
            self._udpSerSock.sendto('-1', (self._hostname, self._port))
        sys.stdout.flush()
        sys.stdin.flush()
        self._udpSerSock.close()
