import socket
import threading
import pickle
from PIL import ImageGrab
from pynput.mouse import Controller as MouseController, Button
from pynput.keyboard import Controller as KeyboardController
from pynput.keyboard import Key
import time

class RemoteControlServer:
    def __init__(self, host='0.0.0.0', screen_port=9999, input_port=10000):
        self.host = host
        self.screen_port = screen_port
        self.input_port = input_port
        self.mouse = MouseController()
        self.keyboard = KeyboardController()

    def handle_screen(self, conn):
        print("[Server] Screen thread started.")
        while True:
            try:
                screen = ImageGrab.grab()
                data = pickle.dumps(screen)
                size = len(data).to_bytes(4, 'big')
                conn.sendall(size + data)
                print(f"[Server] Sent screen data ({len(data)} bytes)")
            except Exception as e:
                print(f"[Server] Screen thread error: {e}")
                break

    def handle_input(self, conn):
        print("[Server] Input thread started.")
        while True:
            try:
                data = conn.recv(4096)
                if not data:
                    print("[Server] No input data received.")
                    break
                action = pickle.loads(data)
                print(f"[Server] Received action: {action}")
                if action['type'] == 'move':
                    self.mouse.position = (action['x'], action['y'])
                elif action['type'] == 'click':
                    self.mouse.click(Button.left if action['button'] == 'left' else Button.right)
                elif action['type'] == 'key':
                  try:  
                    self.keyboard.press(action['key'])
                    self.keyboard.release(action['key'])
                  except:
                      key_enum = getattr(Key,action['key'].split('.')[1])
                      self.keyboard.press(key_enum)
                      self.keyboard.release(key_enum)
            except Exception as e:
                print(f"[Server] Input thread error: {e}")
                break

    def start(self):
        screen_sock = socket.socket()
        screen_sock.bind((self.host, self.screen_port))
        screen_sock.listen(1)
        print(f"[+] Waiting for screen connection on port {self.screen_port}...")
        screen_conn, _ = screen_sock.accept()
        print("[+] Screen client connected.")

        input_sock = socket.socket()
        input_sock.bind((self.host, self.input_port))
        input_sock.listen(1)
        print(f"[+] Waiting for input connection on port {self.input_port}...")
        input_conn, _ = input_sock.accept()
        print("[+] Input client connected.")

        #threading.Thread(target=self.handle_screen, args=(screen_conn,), daemon=True).start()
        threading.Thread(target=self.handle_input, args=(input_conn,), daemon=True).start()

if __name__ == '__main__':
    server = RemoteControlServer()
    server.start()
    while True:
        time.sleep(0.5)  # Keep main thread alive