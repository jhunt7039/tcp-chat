#Authors: Duncan Kolbusz, Josh Hunt
import socket
import threading

# Server info
HOST = "0.0.0.0"
PORT = 7777

running = True
clients = {}       # addr -> socket
client_names = {}  # addr -> name
clients_lock = threading.Lock()


def broadcast(msg, sender_addr=None):
    dead_clients = []

    with clients_lock:
        for addr, conn in list(clients.items()):
            if sender_addr is not None and addr == sender_addr:
                continue
            try:
                conn.sendall(msg)
            except OSError:
                dead_clients.append(addr)

        for addr in dead_clients:#dead connections handling
            try:
                clients[addr].close()
            except OSError:
                pass

            clients.pop(addr, None)
            client_names.pop(addr, None)


def handle_client(conn, addr):
    print("%s has connected" % (addr,))
    leave_name = str(addr)

    try:#conn handling

        name_data = conn.recv(1024)#grab the name for storage
        if not name_data:
            conn.close()
            return

        name = name_data.decode("utf-8", errors="replace").strip()
        if not name:
            name = "Anon"

        leave_name = name #needed for leave msg

        with clients_lock:
            clients[addr] = conn
            client_names[addr] = name

        print("%s is known as %s" % (addr, name))

        join_msg = ("%s has joined the chat.\n" % name).encode("utf-8")
        broadcast(join_msg)

        while True:#msg handling
            try:
                data = conn.recv(2560)#i think this is 2 lines
                if not data:
                    break

                msg = data.decode("utf-8", errors="replace").strip()
                if not msg:
                    continue

                full_msg = "%s: %s" % (name, msg)
                print(full_msg.strip())
                broadcast(full_msg.encode("utf-8"), addr)

            except OSError:
                break

    finally:#dc handling
        with clients_lock:
            clients.pop(addr, None)
            leave_name = client_names.pop(addr, leave_name)

        try:
            conn.close()#boot losers
        except OSError:
            pass

        print("%s has disconnected" % leave_name)
        leave_msg = ("%s has disconnected from chat.\n" % leave_name).encode("utf-8")
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
                t = threading.Thread(target=handle_client, args=(conn, addr), daemon=True)
                t.start()
            except socket.timeout:
                continue
    except KeyboardInterrupt:
        print("\nServer shutting down...")
        running = False
    finally:
        with clients_lock:
            for conn in list(clients.values()):
                try:
                    conn.close()
                except OSError:
                    pass

            clients.clear()
            client_names.clear()

        try:
            srv.close()
        except OSError:
            pass

        print("Server closed.")


if __name__ == "__main__":
    server_start()