# core/osc.py

from pythonosc import udp_client

class OSCManager:
    def __init__(self, ip="127.0.0.1", port=9000):
        self.client = udp_client.SimpleUDPClient(ip, port)
    
    def send_chat_message(self, text, typing=True):
        self.client.send_message("/chatbox/input", [text, True, False])
        self.client.send_message("/chatbox/typing", typing)
    
    def send_click(self, press):
        self.client.send_message("/input/UseRight", 1 if press else 0)

