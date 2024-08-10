import socket
import selectors
import types

sel = selectors.DefaultSelector()

class ServerManager:
    def __init__(self, gui_reference):
        self.gui_reference = gui_reference
        self.host, self.port = '192.168.1.1', 10000

    def setup_server(self):
        lsock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        lsock.bind((self.host, self.port))
        lsock.listen()
        print(f"Listening on {(self.host, self.port)}")
        lsock.setblocking(False)
        sel.register(lsock, selectors.EVENT_READ, data=None)

        try:
            while True:
                events = sel.select(timeout=None)
                for key, mask in events:
                    if key.data is None:
                        self.accept_wrapper(key.fileobj)
                    else:
                        self.service_connection(key, mask)
        except KeyboardInterrupt:
            print("Caught keyboard interrupt, exiting")
        finally:
            sel.close()

    def accept_wrapper(self, sock):
        conn, addr = sock.accept()
        print(f"Accepted connection from {addr}")
        conn.setblocking(False)
        data = types.SimpleNamespace(addr=addr, inb=b"", outb=b"")
        events = selectors.EVENT_READ | selectors.EVENT_WRITE
        sel.register(conn, events, data=data)
        self.gui_reference.connection_state = True

    def service_connection(self, key, mask):
        sock = key.fileobj
        data = key.data
        if mask & selectors.EVENT_READ:
            recv_data = sock.recv(1024)
            if recv_data:
                data.outb += recv_data
                self.gui_reference.process_received_data(recv_data.decode())
            else:
                print(f"Closing connection to {data.addr}")
                sel.unregister(sock)
                sock.close()
                self.gui_reference.connection_state = False
        if mask & selectors.EVENT_WRITE:
            if data.outb:
                print(f"Echoing {data.outb!r} to {data.addr}")
                try:
                    sent = sock.send(data.outb)
                    data.outb = data.outb[sent:]
                except Exception as e:
                    print(f"Error sending data to {data.addr}: {e}")
                    self.gui_reference.connection_state = False

    def send_data(self, message):
        if self.gui_reference.connection_state:
            for key in sel.get_map().values():
                if key.data is not None:
                    conn = key.fileobj
                    try:
                        conn.send(message.encode())
                        print(f"Sent data: {message} to {key.data.addr}")
                    except Exception as e:
                        print(f"Error sending data to {key.data.addr}: {e}")
                        self.gui_reference.connection_state = False
        else:
            print("Cannot send data. No active connection.")

    def shutdown_server(self):
        print("Shutting down server...")
        sel.close()
