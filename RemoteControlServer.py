import socket
import threading
import pickle
import cv2
import numpy as np
import time
from collections import deque
import queue

class RemoteControlClient:
    def __init__(self, server_ip, screen_port=9999, input_port=10000):
        self.server_ip = server_ip
        self.screen_port = screen_port
        self.input_port = input_port
        self.input_sock = socket.socket()
        self.screen_sock = socket.socket()
        self.input_queue = queue.Queue()

    def receive_screen(self):
        print("[Client] Screen receiver started.")
        try:
            while True:
                size_data = self.screen_sock.recv(4)
                if not size_data:
                    break
                size = int.from_bytes(size_data, 'big')
                data = b''
                while len(data) < size:
                    packet = self.screen_sock.recv(size - len(data))
                    if not packet:
                        break
                    data += packet
                img = pickle.loads(data)
                frame = np.array(img)
                cv2.imshow("Remote Desktop", frame)
                if cv2.waitKey(1) == ord('q'):
                    break
        except Exception as e:
            print(f"[Client] Screen receiver error: {e}")
        finally:
            self.screen_sock.close()
            cv2.destroyAllWindows()

    def input_sender(self):
        try:
            while True:
                actions = []
                try:
                    while True:
                        actions.append(self.input_queue.get_nowait())
                except queue.Empty:
                    pass

                for action in actions:
                    self.input_sock.sendall(pickle.dumps(action))
                time.sleep(0.01)
        except Exception as e:
            print(f"[Client] Input sender error: {e}")
        finally:
            self.input_sock.close()

    def enqueue_input(self, action):
        if action['type'] == 'move':
            with self.input_queue.mutex:
                self.input_queue.queue = deque(a for a in self.input_queue.queue if a['type'] != 'move')
        self.input_queue.put_nowait(action)

    def start(self):
        print("[Client] Connecting to server...")
        self.screen_sock.connect((self.server_ip, self.screen_port))
        self.input_sock.connect((self.server_ip, self.input_port))
        print("[Client] Connected to server.")

        threading.Thread(target=self.receive_screen, daemon=True).start()
        threading.Thread(target=self.input_sender, daemon=True).start()

        print("[Client] Press ESC to exit input sending")
        try:
            import pynput.mouse as pm
            import pynput.keyboard as pk

            def on_move(x, y):
                self.enqueue_input({"type": "move", "x": x, "y": y})

            def on_click(x, y, button, pressed):
                if pressed:
                    self.enqueue_input({"type": "click", "button": str(button).split('.')[-1]})

            def on_press(key):
                try:
                    self.enqueue_input({"type": "key", "key": key.char})
                except AttributeError:
                    self.enqueue_input({"type":"key","key":str(key)})

            mouse_listener = pm.Listener(on_move=on_move, on_click=on_click)
            keyboard_listener = pk.Listener(on_press=on_press)
            mouse_listener.start()
            keyboard_listener.start()
            mouse_listener.join()
            keyboard_listener.join()
        except KeyboardInterrupt:
            print("[Client] Keyboard interrupt received. Closing input socket.")
            self.input_sock.close()

if __name__ == '__main__':
    client = RemoteControlClient("192.168.1.248")
    client.start()
    while True:
        time.sleep(0.5)


