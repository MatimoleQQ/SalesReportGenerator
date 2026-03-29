# raport_generator.py
from __future__ import print_function
import os.path
import pandas as pd
import json
import matplotlib.pyplot as plt
from fpdf import FPDF
from fpdf.enums import XPos, YPos
import yagmail
from random import randint, choice
from datetime import datetime, timedelta
import base64
import os
from google.oauth2.credentials import Credentials
from google_auth_oauthlib.flow import InstalledAppFlow
from googleapiclient.discovery import build
from email.mime.multipart import MIMEMultipart
from email.mime.base import MIMEBase
from email import encoders
from email.mime.text import MIMEText
from openai import OpenAI
import re


def wyslij_raport(pdf_path, app_password=None):

    # Konfiguracja

    with open("../config/config.json") as json_file:
        config = json.load(json_file)
    sender_email = config["sender_email"]
    receiver_email = config["sender_email"]

    print(sender_email, receiver_email)

    SCOPES = ['https://www.googleapis.com/auth/gmail.send']

    # Plik z Twoim Client ID i Client Secret
    CLIENT_SECRET_FILE = '../secret/client_secret.json'

    creds = None
    # Sprawdź czy istnieje token
    if os.path.exists('../secret/token.json'):
        creds = Credentials.from_authorized_user_file('../secret/token.json', SCOPES)
    # Jeśli brak tokena lub wygasł → logowanie przez przeglądarkę
    if not creds or not creds.valid:
        flow = InstalledAppFlow.from_client_secrets_file(CLIENT_SECRET_FILE, SCOPES)
        creds = flow.run_local_server(port=0)
        with open('../secret/token.json', 'w') as token:
            token.write(creds.to_json())

    # Budowanie serwisu Gmail API
    service = build('gmail', 'v1', credentials=creds)

    # Tworzenie maila
    message = MIMEMultipart()
    message['to'] = receiver_email
    message['subject'] = 'Raport sprzedaży'

    body = MIMEText("Cześć,\n\nW załączniku przesyłam raport sprzedaży.\n\nPozdrawiam", 'plain')
    message.attach(body)

    # Załącznik PDF
    with open(pdf_path, "rb") as f:
        part = MIMEBase('application', 'pdf')
        part.set_payload(f.read())
    encoders.encode_base64(part)
    part.add_header('Content-Disposition', f'attachment; filename="{os.path.basename(pdf_path)}"')
    message.attach(part)

    # Zakodowanie wiadomości
    raw_message = base64.urlsafe_b64encode(message.as_bytes()).decode()

    # Wysłanie maila
    try:
        message = service.users().messages().send(userId="me", body={'raw': raw_message}).execute()
        print(f'Mail wysłany! ID: {message["id"]}')
    except Exception as e:
        print(f'Błąd wysyłki: {e}')


def generuj_pdf(excel_path):
    nazwa_pliku_pdf = "raport_sprzedazy.pdf"
    # # ===== 1. Tworzymy przykładowy plik Excel =====
    # produkty = ['Klawiatura', 'Myszka', 'Router', 'Laptop','Komputer','Pendrive']
    # start_date = datetime(2026, 1, 1)
    # ilosc_wierszy = 50
    # dates = [start_date + timedelta(days=i) for i in range(ilosc_wierszy)]
    #
    # data = []
    # for i in range(ilosc_wierszy):
    #         produkt = choice(produkty)
    #         ilosc = randint(1, 20)
    #         cena = randint(10, 50)
    #         przychod = ilosc * cena
    #         data.append([dates[i].strftime('%Y-%m-%d'), produkt, ilosc, cena, przychod])
    #
    # df = pd.DataFrame(data, columns=['Data', 'Produkt', 'Ilość', 'Cena jedn.', 'Przychód'])
    # df.to_excel('sprzedaz_przyklad.xlsx', index=False)
    # print("Plik Excel 'sprzedaz_przyklad.xlsx' został utworzony.")



    # ===== 2. Wczytanie danych z Excela =====
    df = pd.read_excel(excel_path)
    print("\nPierwsze 5 wierszy danych:")
    print(df.head())

    # ===== 3. Podsumowania =====
    suma_sprzedazy = df['Ilość'].sum()
    srednia_sprzedazy = df['Ilość'].mean()
    suma_przychodu = df['Przychód'].sum()

    # Grupowanie sprzedaży po produktach
    grupa_produkt = df.groupby('Produkt')[['Ilość', 'Przychód']].sum()
    print("\nSprzedaż po produktach:")
    print(grupa_produkt)

    # ===== AI Update Insights =====
    # wczytanie klucza z pliku
    with open("../secret/openAi_api_secret.json") as f:
        config = json.load(f)

    api_key = config["openai_api"]

    # inicjalizacja klienta
    client = OpenAI(api_key=api_key)

    data_summary = df.describe().to_string()

    prompt = f"""
    You are a business analyst.

    Analyze the following sales data summary and provide:
    - 3 key insights
    - trends
    - recommendations

    DATA:
    {data_summary}
    """

    response = client.chat.completions.create(
        model="gpt-3.5-turbo",  # zamiast "gpt-4"
        messages=[{"role": "user", "content": prompt}]
    )

    ai_insights = response.choices[0].message.content
    print(ai_insights)

    # with open("../keyInsights.txt", "r", encoding="utf-8") as f:
    #     ai_insights = f.read()
    #
    # print(ai_insights)




    # ===== 4. Tworzenie wykresu =====
    plt.figure(figsize=(10,6))  # większy wykres
    grupa_produkt['Ilość'].plot(kind='bar', color='skyblue', title='Sprzedaż po produktach')
    plt.xlabel('Produkt')
    plt.ylabel('Ilość sprzedanych sztuk')
    plt.xticks(rotation=0)          # poziome nazwy produktów
    plt.tight_layout(pad=2)         # zwiększa marginesy wewnątrz wykresu
    plt.savefig('wykres_sprzedaz.png')
    plt.close()
    print("\nWykres zapisany jako 'wykres_sprzedaz.png'")

    # ===== 5. Tworzenie PDF =====
    pdf = FPDF()
    pdf.add_page()

    # Dodanie czcionki TrueType (obsługuje polskie znaki)
    # Upewnij się, że masz w folderze "font/" pliki:
    # DejaVuSans.ttf i DejaVuSans-Bold.ttf
    pdf.add_font('DejaVu', '', '../font/DejaVuSans.ttf')
    pdf.add_font('DejaVu', 'B', '../font/DejaVuSans-Bold.ttf')

    # Nagłówek raportu
    pdf.set_font('DejaVu', 'B', 16)
    pdf.cell(0, 10, "Raport Sprzedaży", new_x=XPos.LMARGIN, new_y=YPos.NEXT, align='C')

    # Podsumowania
    pdf.set_font('DejaVu', '', 12)
    pdf.cell(0, 10, f"Suma sprzedanych sztuk: {suma_sprzedazy}", new_x=XPos.LMARGIN, new_y=YPos.NEXT)
    pdf.cell(0, 10, f"Średnia sprzedaż na wpis: {srednia_sprzedazy:.2f}", new_x=XPos.LMARGIN, new_y=YPos.NEXT)
    pdf.cell(0, 10, f"Suma przychodów: {suma_przychodu}", new_x=XPos.LMARGIN, new_y=YPos.NEXT)

    # Pobranie aktualnej pozycji w PDF
    current_y = pdf.get_y()

    # Wstawienie wykresu poniżej podsumowań
    pdf_width = 180     # szerokość wykresu w mm
    pdf_height = 80     # wysokość wykresu w mm
    pdf.image("wykres_sprzedaz.png", x=10, y=current_y + 5, w=pdf_width, h=pdf_height)

    # Ustawienie kursora PDF poniżej wykresu z dodatkowym marginesem
    pdf.set_y(current_y + 5 + pdf_height + 5)

    # ===== Dodanie tabeli sprzedaży po produktach =====
    pdf.set_font('DejaVu', 'B', 12)
    pdf.cell(50, 10, "Produkt", 1)
    pdf.cell(50, 10, "Ilość", 1)
    pdf.cell(50, 10, "Przychód", 1)
    pdf.ln()

    pdf.set_font('DejaVu', '', 12)
    for index, row in grupa_produkt.iterrows():
        pdf.cell(50, 10, str(index), 1)
        pdf.cell(50, 10, str(row['Ilość']), 1)
        pdf.cell(50, 10, str(row['Przychód']), 1)
        pdf.ln()

    #Dodawanie czesci z insightamiAI
    pdf.add_page()

    # 🔹 tytuł główny
    pdf.set_font("helvetica", "B", 18)
    pdf.cell(0, 12, "Wnioski", new_x=XPos.LMARGIN, new_y=YPos.NEXT)
    # 🔹 linia separatora
    pdf.set_draw_color(0, 0, 0)
    pdf.set_line_width(0.5)
    pdf.line(10, pdf.get_y(), 200, pdf.get_y())

    pdf.ln(8)

    # 🔹 wczytanie AI insights z pliku
    with open("../keyInsights.txt", "r", encoding="utf-8") as f:
        ai_insights = f.read()

    # 🔹 podział na linie (żeby zrobić sekcje)
    lines = ai_insights.split("\n")

    # 🔹 styl treści
    pdf.set_font("helvetica", size=12)

    for line in lines:
        line = line.strip()

        if not line:
            pdf.ln(2)
            continue

        # 🔹 czyszczenie
        line = " ".join(line.split())

        # 🔹 nagłówki
        if ":" in line and len(line) < 60:
            pdf.ln(3)
            pdf.set_font("DejaVu", "B", 12)
            pdf.set_x(10)  # 🔥 reset pozycji
            pdf.cell(0, 8, line)
            pdf.ln()
            pdf.set_font("DejaVu", size=12)


        else:
            pdf.set_x(10)  # 🔥 KLUCZOWE
            pdf.multi_cell(0, 8, f"- {line}")

    # Zapis PDF
    pdf.output(nazwa_pliku_pdf)
    print("\nPDF 'raport_sprzedaz.pdf' został wygenerowany!")
    # wyslij_raport("raport_sprzedazy.pdf")
    return nazwa_pliku_pdf
if __name__ == '__main__':
    generuj_pdf("../sprzedaz_przyklad.xlsx")
#   wyslij_raport("../raport_sprzedazy.pdf")