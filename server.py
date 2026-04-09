import socket
import threading

# server info
HOST = '127.0.0.1'
PORT = 7777

running = True
clients = {}       # addr -> socket
client_names = {}  # addr -> name
clients_lock = threading.Lock()


def broadcast(msg, sender_addr=None):
    dead_clients = []

    with clients_lock:
        for addr, conn in clients.items():
            if sender_addr is not None and addr == sender_addr:
                continue
            try:
                conn.sendall(msg)
            except socket.error:
                dead_clients.append(addr)

        for addr in dead_clients:
            try:
                clients[addr].close()
            except:
                pass

            if addr in clients:
                del clients[addr]
            if addr in client_names:
                del client_names[addr]


def handle_client(conn, addr):
    print("%s has connected" % (addr,))

    leave_name = str(addr)

    try:
        # first message = username
        name_data = conn.recv(1024)
        if not name_data:
            conn.close()
            return

        name = name_data.decode('utf-8', 'replace').strip()
        if not name:
            name = 'Anon'

        leave_name = name

        with clients_lock:
            clients[addr] = conn
            client_names[addr] = name

        print("%s is known as %s" % (addr, name))

        join_msg = "%s has joined the chat.\n" % name
        broadcast(join_msg)

        while True:
            try:
                data = conn.recv(2560)
                if not data:
                    break

                msg = data.decode('utf-8', 'replace').strip()
                if not msg:
                    continue

                full_msg = "%s: %s\n" % (name, msg)
                print(full_msg.strip())
                broadcast(full_msg, addr)

            except socket.error:
                break

    finally:
        with clients_lock:
            if addr in clients:
                del clients[addr]
            if addr in client_names:
                leave_name = client_names[addr]
                del client_names[addr]

        try:
            conn.close()
        except:
            pass

        print("%s has disconnected" % leave_name)
        leave_msg = "%s has disconnected from chat.\n" % leave_name
        broadcast(leave_msg)


def server_start():
    global running

    srv = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    srv.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
    srv.bind((HOST, PORT))
    srv.listen(100)
    srv.settimeout(1.0)

    print("Server listening on %s:%d" % (HOST, PORT))

    try:
        while running:
            try:
                conn, addr = srv.accept()
                t = threading.Thread(target=handle_client, args=(conn, addr))
                t.daemon = True
                t.start()
            except socket.timeout:
                continue
    except KeyboardInterrupt:
        print("\nServer shutting down...")
        running = False
    finally:
        with clients_lock:
            for conn in clients.values():
                try:
                    conn.close()
                except:
                    pass

            clients.clear()
            client_names.clear()

        try:
            srv.close()
        except:
            pass

        print("Server closed.")


if __name__ == "__main__":
    server_start()