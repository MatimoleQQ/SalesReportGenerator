import os
import pandas as pd
import tkinter as tk
from tkinter import messagebox, filedialog
from tkinterdnd2 import DND_FILES, TkinterDnD
from src.raport_generator import generuj_pdf

# ===== Funkcje =====
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
        messagebox.showinfo("Sukces", f"PDF wygenerowany: {pdf_name}")
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
