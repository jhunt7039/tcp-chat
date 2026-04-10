import tkinter as tk
from tkinter import simpledialog as dialog
import threading
import socket
import queue

class App:
    def __init__(self, master):
        self.master = master
        master.title("Chat Room")
        master.geometry("700x500")

        # name entry
        self.name = dialog.askstring("Name", "Enter your username:")
        if not self.name:
            self.master.destroy()
            return

        # crap
        self.data_queue = queue.Queue()
        self.running = True
        self.client_socket = None

        # master frame area
        self.master_frame = tk.Frame(self.master)
        self.master_frame.pack(fill="both", expand=True)

        # chat display area
        self.chat_frame = tk.Frame(self.master_frame)
        self.chat_frame.pack(fill="both", expand=True, padx=(6, 6), pady=(4, 1))

        self.chat_display = tk.Text(self.chat_frame, state="disabled", wrap="word")
        self.chat_display.pack(fill="both", expand=True)

        # message input area
        self.input_frame = tk.Frame(self.master_frame)
        self.input_frame.pack(fill="x", padx=(6, 6), pady=(1, 4))

        self.message_input = tk.Text(self.input_frame, height=2, wrap="word")
        self.message_input.pack(side="left", fill="x", expand=True
                                )
        self.send_button = tk.Button(self.input_frame,
                                     text="Send",
                                     command=self.send_message,
                                     activebackground="green",
                                     activeforeground="white",
                                     anchor="center",
                                     bd=3,
                                     bg="lightgray",
                                     fg="black",
                                     height=2,
                                     width=6,
                                     )
        self.send_button.pack(side="right")

        # socket crap
        self.socket_thread = threading.Thread(target=self.read_socket)
        self.socket_thread.daemon = True  # Allow program to exit even if thread is running
        self.socket_thread.start()

        self.update_gui()

    def read_socket(self):
        host = '127.0.0.1'  # Or "localhost"
        port = 7777         # Replace with your port

        try:
            self.client_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            self.client_socket.connect((host, port))
            self.client_socket.sendall(self.name.encode())

            while self.running:
                data = self.client_socket.recv(1024)

                if not data:
                    self.data_queue.put("The server has been terminated. Please exit.")
                    self.running = False
                    self.client_socket.close()
                    self.client_socket = None
                    break

                self.data_queue.put(data.decode())

        except Exception:
            self.data_queue.put("The server has been terminated. Please exit.")
            self.running = False
            if self.client_socket is not None:
                self.client_socket.close()

    def update_gui(self):
        try:
            while True:
                data = self.data_queue.get_nowait()
                self.chat_helper(data)

        except queue.Empty:
            pass  # No data yet, ignore

        if self.running:
            self.master.after(100, self.update_gui) # Check every 100 ms

    def chat_helper(self, message):
        self.chat_display.config(state="normal")
        self.chat_display.insert(tk.END, message + "\n")
        self.chat_display.config(state="disabled")
        self.chat_display.see(tk.END)

    def close(self):
        self.running = False
        self.client_socket.close()
        self.master.destroy()

    def send_message(self):
        message = self.message_input.get("1.0", tk.END).strip()
        if not message:
            return

        if self.client_socket is None:
            self.chat_helper("Not connected to server.")
            return

        try:
            self.client_socket.sendall(message.encode())
            self.chat_helper(f"{self.name}: {message}")
            self.message_input.delete("1.0", tk.END)
        except Exception:
            self.data_queue.put("The server has been terminated. Please exit.")
            self.running = False
            if self.client_socket is not None:
                self.client_socket.close()


root = tk.Tk()
app = App(root)
root.protocol("WM_DELETE_WINDOW", app.close) # Handle window close event
root.mainloop()
