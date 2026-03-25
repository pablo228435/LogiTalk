import base64
import io
import threading
import os
from socket import socket, AF_INET, SOCK_STREAM
from customtkinter import *
from tkinter import filedialog, END
from PIL import Image


class MainWindow(CTk):
    def __init__(self):
        super().__init__()
        self.geometry('900x600')
        self.title("Pro Chat Client")
       
        # 1. СТАТИЧНІ ПАРАМЕТРИ
        self.username = "Artem"
        self.sock = None


        # 2. ЖОРСТКА СТРУКТУРА: Два вікна в одному
        # ЛІВИЙ БЛОК (Профіль) - завжди видимий [cite: 133-135]
        self.profile_side = CTkFrame(self, width=220, corner_radius=0)
        self.profile_side.pack(side="left", fill="y")
        self.profile_side.pack_propagate(False)


        # ПРАВИЙ БЛОК (Чат) - займає все інше місце [cite: 140-142]
        self.chat_side = CTkFrame(self, fg_color="transparent")
        self.chat_side.pack(side="right", fill="both", expand=True)


        # --- НАПОВНЕННЯ ЛІВОГО БЛОКУ (Профіль) --- [cite: 172-179]
        CTkLabel(self.profile_side, text='НАЛАШТУВАННЯ', font=('Arial', 16, 'bold'), text_color='white').pack(pady=(40, 20))
       
        CTkLabel(self.profile_side, text='Ваш нікнейм:', font=('Arial', 12), text_color='white').pack(pady=(10, 5))
        self.new_nick_entry = CTkEntry(self.profile_side, placeholder_text="Введіть новий нік")
        self.new_nick_entry.pack(pady=5, padx=20, fill="x")
       
        self.save_btn = CTkButton(self.profile_side, text="Зберегти нік", command=self.save_name)
        self.save_btn.pack(pady=20, padx=20)


        # --- НАПОВНЕННЯ ПРАВОГО БЛОКУ (Чат) ---
        # Поле повідомлень [cite: 141-142]
        self.chat_field = CTkScrollableFrame(self.chat_side)
        self.chat_field.pack(side="top", padx=15, pady=(15, 5), fill="both", expand=True)


        # Нижня панель (введення) [cite: 143-149]
        self.input_area = CTkFrame(self.chat_side, height=80, fg_color="transparent")
        self.input_area.pack(side="bottom", fill="x", padx=15, pady=10)


        self.message_entry = CTkEntry(self.input_area, placeholder_text='Напишіть повідомлення...', height=45)
        self.message_entry.pack(side="left", fill="x", expand=True, padx=(0, 10))
        self.message_entry.bind("<Return>", lambda e: self.send_message())


        self.send_btn = CTkButton(self.input_area, text='>', width=55, height=45, command=self.send_message)
        self.send_btn.pack(side="right")


        self.img_btn = CTkButton(self.input_area, text='📂', width=55, height=45, command=self.open_image)
        self.img_btn.pack(side="right", padx=5)


        # 3. ЗАПУСК
        self.update()
        self.add_message("[СИСТЕМА] Чат активований. Текст тепер білий!")
        threading.Thread(target=self.connect_to_server, daemon=True).start()


    def save_name(self):
        """Оновлює нікнейм [cite: 192-196]"""
        name = self.new_nick_entry.get().strip()
        if name:
            self.username = name
            self.add_message(f"[СИСТЕМА] Ви змінили нік на: {self.username}")


    def add_message(self, text, img=None):
        """Додає повідомлення з білим кольором тексту [cite: 208-218]"""
        frame = CTkFrame(self.chat_field, fg_color="#2b2b2b")
        frame.pack(pady=8, padx=15, anchor='w', fill='x')
       
        # Встановлюємо text_color='white' для чіткості
        wrap = self.chat_field.winfo_width() - 60
        lbl = CTkLabel(frame, text=text, wraplength=max(200, wrap),
                       justify='left', image=img, compound='top', text_color='white')
        lbl.pack(padx=15, pady=10)
       
        # Автопрокрутка
        self.chat_field.after(10, lambda: self.chat_field._parent_canvas.yview_moveto(1.0))


    def send_message(self):
        """[cite: 219-228]"""
        msg = self.message_entry.get().strip()
        if msg and self.sock:
            self.add_message(f"Я: {msg}")
            try:
                self.sock.sendall(f"TEXT@{self.username}@{msg}\n".encode('utf-8'))
            except: pass
            self.message_entry.delete(0, END)


    def open_image(self):
        """[cite: 267-280]"""
        path = filedialog.askopenfilename(filetypes=[("Зображення", "*.png *.jpg")])
        if path and self.sock:
            try:
                with open(path, "rb") as f:
                    b64 = base64.b64encode(f.read()).decode()
                self.sock.sendall(f"IMAGE@{self.username}@{os.path.basename(path)}@{b64}\n".encode())
                img = CTkImage(Image.open(path), size=(250, 250))
                self.add_message("Ви надіслали фото:", img)
            except: pass


    def connect_to_server(self):
        """[cite: 153-157]"""
        try:
            self.sock = socket(AF_INET, SOCK_STREAM)
            self.sock.connect(('192.168.1.242', 8080))
            self.sock.send(f"TEXT@{self.username}@[SYSTEM] {self.username} онлайн!\n".encode('utf-8'))
            self.recv_message()
        except:
            self.after(0, lambda: self.add_message("[ПОМИЛКА] Сервер не відповідає."))


    def recv_message(self):
        """[cite: 229-242]"""
        buffer = ""
        while True:
            try:
                data = self.sock.recv(1024*1024).decode('utf-8', errors='ignore')
                if not data: break
                buffer += data
                while "\n" in buffer:
                    line, buffer = buffer.split("\n", 1)
                    self.handle_line(line)
            except: break


    def handle_line(self, line):
        """[cite: 243-266]"""
        parts = line.split("@", 3)
        if len(parts) < 3: return
        t, auth, cont = parts[0], parts[1], parts[2]
        if t == "TEXT":
            self.after(0, lambda: self.add_message(f"{auth}: {cont}"))
        elif t == "IMAGE" and len(parts) == 4:
            try:
                img = CTkImage(Image.open(io.BytesIO(base64.b64decode(parts[3]))), size=(250, 250))
                self.after(0, lambda: self.add_message(f"{auth} надіслав фото:", img))
            except: pass


if __name__ == "__main__":
    app = MainWindow()
    app.mainloop()

