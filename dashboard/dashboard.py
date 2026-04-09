import os
import pandas as pd
import tkinter as tk
from tkinter import messagebox, filedialog
from tkinterdnd2 import DND_FILES, TkinterDnD
from src.raport_generator import generuj_pdf,upload_to_s3
import webbrowser
import pyperclip

# ===== Funkcje =====
def show_link_popup(url):
    win = tk.Toplevel(root)
    win.title("Link do pliku")
    win.geometry("420x180")
    win.resizable(False, False)

    tk.Label(win, text="Twój raport jest gotowy!", font=("Arial", 12, "bold")).pack(pady=10)

    tk.Label(win, text="Co chcesz zrobić z linkiem?", font=("Arial", 10)).pack(pady=5)

    def copy_link():
        root.clipboard_clear()
        root.clipboard_append(url)
        root.update()
        tk.Label(win, text="Skopiowano do schowka ✔", fg="green").pack()

    def open_link():
        webbrowser.open(url)

    tk.Button(win, text="📋 Skopiuj link", command=copy_link,
              bg="#4CAF50", fg="white").pack(pady=5)

    tk.Button(win, text="🌐 Otwórz link", command=open_link,
              bg="#2196F3", fg="white").pack(pady=5)

    tk.Button(win, text="❌ Zamknij", command=win.destroy,
              bg="#f44336", fg="white").pack(pady=5)
def pokaz_link():
    # Generowanie presigned URL
    url = upload_to_s3()

    if url:
        # Wyświetlenie linku w messagebox z możliwością skopiowania
        messagebox.showinfo("Link do pliku", f"Presigned URL:\n{url}\n\n(Link można skopiować)")
        pyperclip.copy(url)  # link trafia od razu do schowka
    else:
        messagebox.showerror("Błąd", "Nie udało się wygenerować linku do pliku.")

def pokaz_custom_messagebox(pdf_url):
    win = tk.Toplevel(root)
    win.title("PDF wygenerowany!")
    win.geometry("400x150")
    win.resizable(False, False)

    tk.Label(win, text="PDF został wygenerowany!", font=("Arial", 12)).pack(pady=(20, 10))

    # Przycisk otwierający link
    tk.Button(win, text="Wyświetl link do pliku",
              font=("Arial", 11),
              bg="#2196F3", fg="white",
              command=lambda: webbrowser.open(pdf_url)).pack(pady=5)

    # Przycisk zamykający okno
    tk.Button(win, text="Zamknij",
              font=("Arial", 11),
              command=win.destroy).pack(pady=5)

def ustaw_plik(path):
    entry_file.config(state='normal')
    entry_file.delete(0, tk.END)
    entry_file.insert(0, path)
    entry_file.config(state='disabled')  # blokada ręcznego wpisywania
    aktualizuj_info(path)

def aktualizuj_info(path):
    try:
        df = pd.read_excel(path)
        liczba_wierszy = len(df)
        produkty = df['Produkt'].nunique() if 'Produkt' in df.columns else 0
        suma_sprzedazy = df['Ilość'].sum() if 'Ilość' in df.columns else 0
        suma_przychodu = df['Przychód'].sum() if 'Przychód' in df.columns else 0

        info_text.set(f"Liczba wierszy: {liczba_wierszy}\n"
                      f"Liczba unikalnych produktów: {produkty}\n"
                      f"Suma sprzedanych sztuk: {suma_sprzedazy}\n"
                      f"Suma przychodów: {suma_przychodu}")
    except Exception as e:
        info_text.set("Nie można odczytać pliku!")

def wybierz_plik():
    file_path = filedialog.askopenfilename(filetypes=[("Excel files", "*.xlsx *.xls")])
    if file_path:
        ustaw_plik(file_path)

def drop_file(event):
    files = root.tk.splitlist(event.data)
    if files and files[0].endswith(('.xlsx', '.xls')):
        ustaw_plik(files[0])

def generuj():
    excel_path = entry_file.get()
    if not excel_path or not os.path.exists(excel_path):
        messagebox.showerror("Błąd", "Wybierz poprawny plik Excel!")
        return
    try:
        pdf_name = generuj_pdf(excel_path)
        presigned_url = upload_to_s3()
        show_link_popup(presigned_url)
    except Exception as e:
        messagebox.showerror("Błąd", str(e))

# ===== GUI =====
root = TkinterDnD.Tk()
root.iconbitmap("../logo/logo.ico")
root.title("Generator Raportu Sprzedaży")
root.geometry("550x350")
root.configure(bg="#f0f0f0")

tk.Label(root, text="Wybierz plik Excel lub przeciągnij go tutaj:",
         bg="#f0f0f0", font=("Arial", 12)).pack(pady=(20,5))

# Pole wyświetlające wybrany plik (tylko do odczytu)
entry_file = tk.Entry(root, width=50, font=("Arial", 11), state='disabled')
entry_file.pack(pady=5)

# Przycisk wyboru pliku
tk.Button(root, text="Wybierz plik", command=wybierz_plik,
          bg="#4CAF50", fg="white", font=("Arial", 11)).pack(pady=5)

# Panel info
info_text = tk.StringVar()
info_text.set("Nie wybrano pliku.")
tk.Label(root, textvariable=info_text, justify='left', bg="#f0f0f0",
         font=("Arial", 11), bd=1, relief='sunken', padx=10, pady=10, anchor='w').pack(pady=(10,10), fill='x', padx=20)

# Przycisk generowania PDF
tk.Button(root, text="Generuj PDF", command=generuj,
          bg="#2196F3", fg="white", font=("Arial", 12, "bold")).pack(pady=(5,20))

# ===== Drag & Drop =====
entry_file.drop_target_register(DND_FILES)
entry_file.dnd_bind('<<Drop>>', drop_file)

root.mainloop()
