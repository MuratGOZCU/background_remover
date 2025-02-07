import tkinter as tk
from tkinter import ttk, scrolledtext
import openai
import json
import os
from pathlib import Path
from pygments import lex
from pygments.lexers import PythonLexer

os.environ['TK_SILENCE_DEPRECATION'] = '1'

class AICodeEditor:
    def __init__(self, root):
        self.root = root
        self.root.title("AI Kod Editörü")
        
        # Ana pencere yapılandırması
        self.setup_ui()
        
        # OpenAI API anahtarını güvenli bir şekilde yükle
        self.api_key = os.getenv('OPENAI_API_KEY')
        
    def setup_ui(self):
        # Ana düzen
        self.main_frame = ttk.PanedWindow(self.root, orient=tk.HORIZONTAL)
        self.main_frame.pack(fill=tk.BOTH, expand=True)
        
        # Kod editörü
        self.editor_frame = ttk.Frame(self.main_frame)
        self.code_editor = scrolledtext.ScrolledText(
            self.editor_frame,
            wrap=tk.WORD,
            width=80,
            height=30,
            font=('Consolas', 11)
        )
        self.code_editor.pack(fill=tk.BOTH, expand=True)
        
        # AI Sohbet paneli
        self.chat_frame = ttk.Frame(self.main_frame)
        self.chat_area = scrolledtext.ScrolledText(
            self.chat_frame,
            wrap=tk.WORD,
            width=40,
            height=25,
            font=('Arial', 10)
        )
        self.chat_area.pack(fill=tk.BOTH, expand=True)
        
        # Sohbet girişi
        self.input_frame = ttk.Frame(self.chat_frame)
        self.input_frame.pack(fill=tk.X, pady=5)
        
        self.chat_input = ttk.Entry(self.input_frame)
        self.chat_input.pack(side=tk.LEFT, fill=tk.X, expand=True)
        
        self.send_button = ttk.Button(
            self.input_frame,
            text="Gönder",
            command=self.send_message
        )
        self.send_button.pack(side=tk.RIGHT)
        
        # Panelleri ana pencereye ekle
        self.main_frame.add(self.editor_frame)
        self.main_frame.add(self.chat_frame)
        
    def send_message(self):
        user_message = self.chat_input.get()
        if user_message:
            # Kullanıcı mesajını göster
            self.chat_area.insert(tk.END, f"Sen: {user_message}\n\n")
            
            # AI yanıtını al
            try:
                ai_response = self.get_ai_response(user_message)
                self.chat_area.insert(tk.END, f"AI: {ai_response}\n\n")
            except Exception as e:
                self.chat_area.insert(tk.END, f"Hata: {str(e)}\n\n")
            
            # Input alanını temizle
            self.chat_input.delete(0, tk.END)
            
            # Sohbeti en alta kaydır
            self.chat_area.see(tk.END)
    
    def get_ai_response(self, message):
        # OpenAI API entegrasyonu
        try:
            response = openai.ChatCompletion.create(
                model="gpt-3.5-turbo",
                messages=[
                    {"role": "system", "content": "Sen bir kod asistanısın."},
                    {"role": "user", "content": message}
                ]
            )
            return response.choices[0].message.content
        except Exception as e:
            return f"API hatası: {str(e)}"

    def add_file_menu(self):
        menubar = tk.Menu(self.root)
        file_menu = tk.Menu(menubar, tearoff=0)
        file_menu.add_command(label="Yeni", command=self.new_file)
        file_menu.add_command(label="Aç", command=self.open_file)
        file_menu.add_command(label="Kaydet", command=self.save_file)
        menubar.add_cascade(label="Dosya", menu=file_menu)
        self.root.config(menu=menubar)

    def highlight_syntax(self):
        code = self.code_editor.get("1.0", tk.END)
        for token, content in lex(code, PythonLexer()):
            # Token tipine göre renklendirme
            pass

def main():
    root = tk.Tk()
    app = AICodeEditor(root)
    root.mainloop()

if __name__ == "__main__":
    main() 