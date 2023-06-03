import time
import datetime
import tkinter as tk
from tkinter import ttk
from modules import configModule, controllerModule

global root, input_entry, send_button, chat_canvas, message_style, response_style, controller_current_section, chat_y, blank_text, chat_file


def send_message():
    global input_entry, controller_current_section, chat_file

    disable_button_entry()
    message = input_entry.get()

    if message is not None and message.strip():
        chat_canvas.yview_moveto(1.0)
        add_message(message)

        if controller_current_section == controllerModule.READ_SECTION:
            response, controller_current_section = controllerModule.process_input_home(message)
        else:
            response, controller_current_section = controllerModule.process_input_qa(message)

        add_response(response)

    enable_button_entry()
    input_entry.delete(0, tk.END)

    if controller_current_section == controllerModule.EXIT:
        time.sleep(1)

        now = datetime.datetime.now()
        file = open(chat_file, "a", encoding='utf-8')
        file.write('\n' + now.strftime(configModule.DATE_FORMAT) + " - Chat terminata.")
        file.close()

        exit()


def disable_button_entry():
    global input_entry, send_button

    send_button.configure(state="disabled")
    input_entry.configure(state="disabled")
    input_entry.unbind("<Return>")


def enable_button_entry():
    global input_entry, send_button

    send_button.configure(state="normal")
    input_entry.configure(state="normal")
    input_entry.bind("<Return>", handle_enter)


def update_chat_canvas(chat_canvas_item):
    global chat_canvas, chat_y, blank_text

    chat_canvas.delete(blank_text)

    if chat_canvas_item.type == "message":
        x = chat_canvas.winfo_width()
        anchor = tk.NE
    else:
        x = 0
        anchor = tk.NW
    chat_canvas.create_window((x, chat_y), window=chat_canvas_item, anchor=anchor)
    chat_canvas_item.update_idletasks()

    chat_y += chat_canvas_item.winfo_height() + 5

    # Aggiungi uno spazio vuoto come margine inferiore
    blank_text = chat_canvas.create_text(5, chat_y - 14, anchor=tk.NW)
    chat_canvas.configure(scrollregion=chat_canvas.bbox("all"))

    # Scroll automatico alla posizione inferiore
    chat_canvas.yview_moveto(1.0)


def add_message_to_chat(message, tag, mess_type):
    global chat_canvas

    frame = tk.Frame(chat_canvas, bg=tag["background"], bd=1, highlightthickness=1, relief="flat",
                     highlightbackground="white")

    # Creazione Label per il testo del messaggio
    text_widget = ttk.Label(frame, text=message, wraplength=300, **tag)
    text_widget.pack(padx=5, pady=2, anchor=tk.W)

    # Creazione Label per l'orario del messaggio
    anc_time = tk.SW
    if mess_type == "message":
        anc_time = tk.SE

    now = datetime.datetime.now()
    formatted_date = now.strftime(configModule.config.chat_date_format)
    time_label = ttk.Label(frame, text=formatted_date, font=(configModule.config.font, 8), foreground="gray", background=tag["background"])
    time_label.pack(padx=0, pady=0, anchor=anc_time)

    frame.update()

    frame_width = frame.winfo_width()
    frame.configure(width=frame_width)
    frame.type = mess_type  # Aggiunta dell'attributo type

    update_chat_canvas(frame)


def add_message(message):
    global chat_file

    add_message_to_chat(message, message_style, "message")
    update_scrollbar()

    file = open(chat_file, "a", encoding='utf-8')
    now = datetime.datetime.now()
    file.write("\n" + now.strftime(configModule.config.chat_date_format) + " - YOU - " + message)
    file.close()


def add_response(response):
    global chat_file

    add_message_to_chat(response, response_style, "response")
    update_scrollbar()

    file = open(chat_file, "a", encoding='utf-8')
    now = datetime.datetime.now()
    file.write("\n" + now.strftime(configModule.config.chat_date_format) + " - BOT - " + response)
    file.close()


def handle_enter(event):
    send_message()  # Simula il clic del pulsante


def update_scrollbar():
    global chat_canvas

    chat_canvas.unbind_all("<MouseWheel>")
    if chat_canvas.winfo_height() < chat_canvas.bbox("all")[3]:
        chat_canvas.bind_all("<MouseWheel>",
                             lambda event: chat_canvas.yview_scroll(int(-1 * (event.delta / 120)), "units"))


def init():
    global root, input_entry, send_button, chat_canvas, message_style, response_style, controller_current_section, chat_y, blank_text, chat_file

    # Creazione della finestra principale
    root = tk.Tk()
    root.title("doQA")
    root.resizable(False, False)
    root.configure(relief="flat", bg=configModule.config.background_color)

    # Calcola le dimensioni dello schermo
    screen_width = root.winfo_screenwidth()
    screen_height = root.winfo_screenheight()

    # Calcola le nuove dimensioni della finestra
    new_width = int(screen_width / 3)
    new_height = int(screen_height / 1.5)

    # Imposta le nuove dimensioni e la posizione della finestra
    root.geometry(f"{new_width}x{new_height}+{int((screen_width - new_width) / 2)}+{int((screen_height - new_height) / 2)}")

    # Creazione del componente Frame per contenere il Canvas e la Scrollbar
    chat_frame = tk.Frame(root, bg=configModule.config.background_color)
    chat_frame.pack(fill=tk.BOTH, expand=True)

    # Creazione del componente Canvas
    chat_canvas = tk.Canvas(chat_frame, bg=configModule.config.background_color, highlightthickness=0)
    chat_canvas.pack(side=tk.LEFT, fill=tk.BOTH, expand=True, padx=10, pady=10)

    # Creazione del componente Scrollbar
    scrollbar = tk.Scrollbar(chat_frame, orient=tk.VERTICAL, command=chat_canvas.yview, relief="flat")
    scrollbar.configure(command=chat_canvas.yview)
    scrollbar.pack(side=tk.RIGHT, fill=tk.Y)

    # Configurazione della Scrollbar
    chat_canvas.configure(yscrollcommand=scrollbar.set)

    # Creazione dello stile per l'allineamento a destra delle risposte
    message_style = {"justify": "right", "background": configModule.config.messages_background_color, "foreground": configModule.config.messages_text_color, "font": (configModule.config.font, 11)}
    response_style = {"justify": "left", "background": configModule.config.response_background_color, "foreground": configModule.config.response_text_color, "font": (configModule.config.font, 11)}

    # Creazione dell'entry per inserire i messaggi
    input_entry = tk.Entry(root, relief="flat", background=configModule.config.entry_background_color, foreground=configModule.config.entry_text_color, font=(configModule.config.font, 11))
    input_entry.pack(side=tk.LEFT, fill=tk.X, expand=True, padx=10, pady=10, ipady=5, ipadx=5)
    input_entry.bind("<Return>", handle_enter)
    input_entry.focus_set()

    # Creazione del pulsante per inviare il messaggio
    send_button = tk.Button(root, text="Ask", command=send_message, relief="flat", bg=configModule.config.send_background_color,
                            activebackground=configModule.config.send_active_background_color, highlightthickness=1,
                            highlightbackground="white", fg=configModule.config.send_text_color, font=(configModule.config.font, 11))
    send_button.pack(side=tk.RIGHT, padx=(0, 10), pady=(10, 10))

    controller_current_section = controllerModule.READ_SECTION
    chat_y = 5
    blank_text = chat_canvas.create_text(5, chat_y - 14, anchor=tk.NW)

    now = datetime.datetime.now()
    formatted_date_chat = now.strftime(configModule.config.output_date_format)
    chat_file = configModule.config.output_path + "chat_" + formatted_date_chat + ".txt"
    file = open(chat_file, "w", encoding='utf-8')
    file.write(now.strftime(configModule.DATE_FORMAT) + " - Chat avviata.")
    file.close()


def init_controller():
    text = controllerModule.init()
    add_response(text)


def start():
    global root

    init_controller()

    root.mainloop()
