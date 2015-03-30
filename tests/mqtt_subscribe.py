import paho.mqtt.client as mqtt

def on_connect(client, userdata, flags, rc):
    print("Connected with result code " + str(rc))
    client.subscribe('experiment/testexp')

def on_message(client, userdata, msg):
    print(msg.payload)
    # reply = raw_input('> {0} '.format(msg.topic))
    # client.publish(msg.topic, reply)

client = mqtt.Client()
client.on_connect = on_connect
client.on_message = on_message
client.connect('test.mosquitto.org')

# client.publish('experiment', "I'm here!")
client.loop_forever()
