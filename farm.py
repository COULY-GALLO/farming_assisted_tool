import tkinter as tk
from tkinter import simpledialog, messagebox, scrolledtext
import pyautogui
import keyboard
import time
import threading

root = tk.Tk()
root.title("Detector de cambio de píxel")

# Configuración
retardo_comando = 0.5
retardo_tecla = 0.05

repetir_para_siempre = tk.BooleanVar()
solo_si_cambia = tk.BooleanVar()
veces_a_repetir = tk.IntVar(value=1)

zonas = []
bucles = []
monitoreando = False
hilo_monitoreo = None


def log(msg):
    consola.insert(tk.END, f"{msg}\n")
    consola.see(tk.END)


def seleccionar_pixel():
    log("Posicioná el mouse y presioná ENTER.")
    messagebox.showinfo("Instrucciones", "Ubicá el mouse sobre el píxel y presioná ENTER.")
    keyboard.wait('enter')
    pos = pyautogui.position()
    color_original = pyautogui.pixel(pos.x, pos.y)

    usar_color_actual = messagebox.askyesno("Color objetivo", f"¿Usar el color actual {color_original} como objetivo?")
    if usar_color_actual:
        color_objetivo = color_original
    else:
        r = simpledialog.askinteger("Rojo", "R (0-255):", minvalue=0, maxvalue=255)
        g = simpledialog.askinteger("Verde", "G (0-255):", minvalue=0, maxvalue=255)
        b = simpledialog.askinteger("Azul", "B (0-255):", minvalue=0, maxvalue=255)
        color_objetivo = (r, g, b)

    comandos = []
    while True:
        comando = simpledialog.askstring("Comando", "Agregá un comando (secuencia de teclas, Enter vacío para terminar):")
        if not comando:
            break
        comandos.append(comando)

    zona = {
        "x": pos.x,
        "y": pos.y,
        "color_objetivo": color_objetivo,
        "color_original": color_original,
        "estado_anterior": color_original,
        "comandos": comandos
    }
    zonas.append(zona)
    lista_zonas.insert(tk.END, f"Zona ({pos.x},{pos.y}) OBJ:{color_objetivo} | CMDs:{len(comandos)}")
    log(f"✅ Zona agregada: ({pos.x},{pos.y}) color={color_objetivo} comandos={len(comandos)}")


def agregar_zona_bucle():
    log("Posicioná el mouse para bucle y presioná ENTER.")
    messagebox.showinfo("Instrucciones", "Ubicá el mouse sobre el píxel y presioná ENTER.")
    keyboard.wait('enter')
    pos = pyautogui.position()
    color_objetivo = pyautogui.pixel(pos.x, pos.y)

    delay_entre_acciones = simpledialog.askfloat("Delay", "Delay entre comandos (segundos):", minvalue=0.01, initialvalue=1.0)
    if delay_entre_acciones is None:
        return

    # Pedir comandos en una ventana de texto multilinea
    ventana_cmd = tk.Toplevel(root)
    ventana_cmd.title("Comandos en bucle")
    tk.Label(ventana_cmd, text="Ingresá un comando por línea.").pack()
    txt_comandos = tk.Text(ventana_cmd, height=10, width=40)
    txt_comandos.pack()

    resultado = []

    def confirmar():
        texto = txt_comandos.get("1.0", tk.END).strip()
        if texto:
            resultado.extend([line.strip() for line in texto.splitlines() if line.strip()])
        ventana_cmd.destroy()

    tk.Button(ventana_cmd, text="Aceptar", command=confirmar).pack(pady=5)
    ventana_cmd.transient(root)
    ventana_cmd.grab_set()
    root.wait_window(ventana_cmd)

    if not resultado:
        log("⚠️ No se agregaron comandos al bucle.")
        return

    comandos = resultado

    bucle = {
        "x": pos.x,
        "y": pos.y,
        "color_objetivo": color_objetivo,
        "comandos": comandos,
        "delay": delay_entre_acciones,
        "activo": False
    }
    bucles.append(bucle)
    lista_zonas.insert(tk.END, f"Bucle ({pos.x},{pos.y}) mientras {color_objetivo} | CMDs:{len(comandos)}")
    log(f"🔁 Bucle agregado: ({pos.x},{pos.y}) color={color_objetivo} delay={delay_entre_acciones:.2f}s comandos={len(comandos)}")


def establecer_retardos():
    global retardo_comando, retardo_tecla
    rc = simpledialog.askfloat("Retardo entre comandos", "Segundos entre comandos completos:", minvalue=0.01, initialvalue=retardo_comando)
    rt = simpledialog.askfloat("Retardo entre teclas", "Segundos entre teclas individuales:", minvalue=0.01, initialvalue=retardo_tecla)
    if rc: retardo_comando = rc
    if rt: retardo_tecla = rt
    lbl_retardos.config(text=f"⏱️ Comando: {retardo_comando:.2f}s | Tecla: {retardo_tecla:.2f}s")
    log(f"🛠️ Nuevo retardo: comando={retardo_comando:.2f}s tecla={retardo_tecla:.2f}s")


def escribir_como_teclado(texto):
    for c in texto:
        keyboard.press(c)
        time.sleep(0.01)
        keyboard.release(c)
        time.sleep(retardo_tecla)


def ejecutar_automatizacion():
    global monitoreando, hilo_monitoreo
    if monitoreando:
        log("⚠️ Ya está ejecutándose.")
        return

    def run():
        global monitoreando
        monitoreando = True
        repeticiones = veces_a_repetir.get()
        contador = 0
        log("▶️ Monitoreo iniciado.")
        while monitoreando and (repetir_para_siempre.get() or contador < repeticiones):
            for zona in zonas:
                x, y = zona["x"], zona["y"]
                color_actual = pyautogui.pixel(x, y)
                if solo_si_cambia.get():
                    if color_actual != zona["estado_anterior"]:
                        log(f"🌀 Cambio en ({x},{y}) de {zona['estado_anterior']} → {color_actual}")
                        if color_actual == zona["color_objetivo"]:
                            for cmd in zona["comandos"]:
                                log(f"⌨️ Ejecutando comando (cambio): {cmd}")
                                escribir_como_teclado(cmd)
                                time.sleep(retardo_comando)
                            contador += 1
                        zona["estado_anterior"] = color_actual
                else:
                    if color_actual == zona["color_objetivo"]:
                        for cmd in zona["comandos"]:
                            log(f"⌨️ Ejecutando comando (igualdad): {cmd}")
                            escribir_como_teclado(cmd)
                            time.sleep(retardo_comando)
                        contador += 1

            for bucle in bucles:
                x, y = bucle["x"], bucle["y"]
                color_actual = pyautogui.pixel(x, y)
                if color_actual == bucle["color_objetivo"]:
                    if not bucle["activo"]:
                        log(f"🔁 Bucle iniciado en ({x},{y})")
                        bucle["activo"] = True
                    for cmd in bucle["comandos"]:
                        log(f"🔂 Ejecutando comando (bucle): {cmd}")
                        escribir_como_teclado(cmd)
                        time.sleep(bucle["delay"])
                else:
                    if bucle["activo"]:
                        log(f"⏹️ Bucle detenido en ({x},{y})")
                        bucle["activo"] = False

            if not repetir_para_siempre.get() and contador >= repeticiones:
                break
            time.sleep(0.1)
        monitoreando = False
        log("🛑 Monitoreo finalizado.")

    hilo_monitoreo = threading.Thread(target=run, daemon=True)
    hilo_monitoreo.start()


def detener():
    global monitoreando
    monitoreando = False
    log("🛑 Stop solicitado.")

# GUI
btn_zona = tk.Button(root, text="Agregar zona de píxel", command=seleccionar_pixel)
btn_zona.pack(pady=5)

btn_bucle = tk.Button(root, text="Agregar zona en bucle mientras color", command=agregar_zona_bucle)
btn_bucle.pack(pady=5)

lista_zonas = tk.Listbox(root, width=70)
lista_zonas.pack(pady=5)

btn_retardo = tk.Button(root, text="Establecer retardos", command=establecer_retardos)
btn_retardo.pack(pady=5)

lbl_retardos = tk.Label(root, text=f"⏱️ Comando: {retardo_comando:.2f}s | Tecla: {retardo_tecla:.2f}s")
lbl_retardos.pack()

frame_opts = tk.Frame(root)
frame_opts.pack(pady=5)

chk_inf = tk.Checkbutton(frame_opts, text="Repetir para siempre", variable=repetir_para_siempre)
chk_inf.pack(side=tk.LEFT)

lbl_veces = tk.Label(frame_opts, text="Veces:")
lbl_veces.pack(side=tk.LEFT, padx=5)

entry_veces = tk.Entry(frame_opts, textvariable=veces_a_repetir, width=5)
entry_veces.pack(side=tk.LEFT)

chk_cambio = tk.Checkbutton(frame_opts, text="Solo al detectar cambio", variable=solo_si_cambia)
chk_cambio.pack(side=tk.LEFT, padx=10)

btn_ejecutar = tk.Button(root, text="▶️ Iniciar monitoreo", command=ejecutar_automatizacion)
btn_ejecutar.pack(pady=5)

btn_stop = tk.Button(root, text="🛑 Detener", fg="white", bg="red", command=detener)
btn_stop.pack(pady=5)

consola = scrolledtext.ScrolledText(root, height=10, width=80)
consola.pack(pady=10)
consola.insert(tk.END, "📋 Consola iniciada...\n")

root.mainloop()
