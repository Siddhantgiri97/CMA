from channels.generic.websocket import WebsocketConsumer
import json
from .models import *
from asgiref.sync import sync_to_async, async_to_sync


class OrderProgress(WebsocketConsumer):
    def connect(self):
        self.room_name = self.scope['url_route']['kwargs']['order_id']
        self.room_group_name = 'order_%s' % self.room_name
        print("Connect")
        async_to_sync(self.channel_layer.group_add)(
            self.room_group_name, self.channel_name)
        self.accept()
        order = Order.give_order_details(self.room_name)
        print(order)
        self.send(text_data=json.dumps({
            'payload': order
        }))

    def disconnect(self, close_code):
        async_to_sync(self.channel_layer.group_discard)(
            self.room_group_name, self.channel_name)

    def recieve(self, text_data):
        async_to_sync(self.channel_layer.group_send)(
            self.room_group_name, {'type': 'order_status', 'payload': text_data})

    def order_status(self, event):
        print(event)
        order = json.loads(event['value'])
        self.send(text_data=json.dumps({
            'payload': order
        }))
