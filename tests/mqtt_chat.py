from multiprocessing.dummy import Process
import sys

import paho.mqtt.client as mqtt


def on_connect(client, userdata, flags, rc):
    print("Connected with result code " + str(rc))
    client.subscribe('/chat')


def on_message(client, userdata, msg):
    print(msg.payload)


client = mqtt.Client()
client.on_connect = on_connect
client.on_message = on_message
client.connect('test.mosquitto.org')

subscriber = Process(target=client.loop_forever)

subscriber.start()
reply = True
try:
    while reply:
        reply = raw_input('> ')
        client.publish('/chat', reply)
except EOFError, e:
    sys.exit(0)
