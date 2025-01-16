#Batu Akbay 1231602809
import ssl
import json
from tkinter import *
import sqlite3
from datetime import datetime
import http.client
import matplotlib.pyplot as plt
from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg
from tkinter import messagebox

ssl._create_default_https_context = ssl._create_stdlib_context


conn = http.client.HTTPSConnection("api.collectapi.com")
headers = {
    'content-type': "application/json",
    'authorization': "apikey 0dM4A3SqME8W5oMI3V3kjr:7bMA2ybadEe3CPVJ3HPzWM"
}

currency_rates = {}
gold_rates = {}


def fetch_api_data():
    global currency_rates, gold_rates
    try:

        conn.request("GET", "/economy/currencyToAll?int=10&base=USD", headers=headers)
        res = conn.getresponse()
        data = res.read()
        currency_data = json.loads(data.decode("utf-8"))
        print("Currency Data:", currency_data)

        if isinstance(currency_data, dict) and "result" in currency_data:
            currency_rates = currency_data["result"]
        else:
            print("Unexpected currency data format")


        conn.request("GET", "/economy/goldPrice", headers=headers)
        res = conn.getresponse()
        data = res.read()
        gold_data = json.loads(data.decode("utf-8"))
        print("Gold Data:", gold_data)

        if isinstance(gold_data, dict) and "result" in gold_data:
            gold_rates = gold_data["result"]
        else:
            print("Unexpected gold data format")

    except http.client.HTTPException as e:
        print(f"HTTP Exception: {e}")
    except json.JSONDecodeError as e:
        print(f"JSON Decode Error: {e}")
    except Exception as e:
        print(f"An error occurred: {e}")

class DataBaseOperation:
    def __init__(self):
        self.baglanti = sqlite3.connect("datasForCurrency.db")
        self.cursor = self.baglanti.cursor()
        self.cursor.execute("""
            CREATE TABLE IF NOT EXISTS Currency(
            tarih TEXT,
            dolar REAL,
            euro REAL,
            altin REAL)  
        """)
        self.baglanti.commit()

    def add_data(self, dolar, euro, altin):
        try:
            tarih = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
            self.cursor.execute("INSERT INTO Currency VALUES (?, ?, ?, ?)",
                                (tarih, dolar, euro, altin))
            self.baglanti.commit()
            print("Veriler Kaydedildi. :)")
        except sqlite3.Error as e:
            print(f"SQLite hatası: {e}")

    def update_data(self, dolar, euro, altin):
        try:
            tarih = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
            self.cursor.execute("SELECT dolar, euro, altin FROM Currency WHERE tarih = (SELECT MAX(tarih) FROM Currency)")
            eski_veriler = self.cursor.fetchone()
            if eski_veriler:
                eski_dolar, eski_euro, eski_altin = eski_veriler


                fetch_api_data()

                guncel_dolar_tl = dolar * currency_rates.get("USD", 0)
                guncel_euro_tl = euro * currency_rates.get("EUR", 0)
                guncel_altin_tl = altin * gold_rates.get("GoldPrice", 0)


                eski_dolar_tl = eski_dolar * currency_rates.get("USD", 0)
                eski_euro_tl = eski_euro * currency_rates.get("EUR", 0)
                eski_altin_tl = eski_altin * gold_rates.get("GoldPrice", 0)


                dolar_profit_loss = guncel_dolar_tl - eski_dolar_tl
                euro_profit_loss = guncel_euro_tl - eski_euro_tl
                altin_profit_loss = guncel_altin_tl - eski_altin_tl


                messagebox.showinfo("Kar/Zarar Bilgisi",
                                    f"Dolar Kar/Zararı: {dolar_profit_loss:.2f} TL\nEuro Kar/Zararı: {euro_profit_loss:.2f} TL\nAltın Kar/Zararı: {altin_profit_loss:.2f} TL")

            else:
                messagebox.showwarning("Uyarı", "Eski veri bulunamadı. Kar/Zarar hesaplanamadı.")


            self.cursor.execute("INSERT INTO Currency VALUES (?, ?, ?, ?)", (tarih, dolar, euro, altin))
            self.baglanti.commit()

            print("Veriler Güncellendi ;)")

        except sqlite3.Error as e:
            print(f"SQLite hatası: {e}")

    def get_data(self):
        self.cursor.execute("SELECT * FROM Currency ORDER BY tarih")
        datas = self.cursor.fetchall()
        for data in datas:
            print(f"Tarih: {data[0]}, Dolar: {data[1]}, Euro: {data[2]}, Altın:{data[3]}")

    def calculate_profit_loss(self):
        self.cursor.execute("SELECT * FROM Currency ORDER BY tarih")
        datas = self.cursor.fetchall()

        for i in range(len(datas) - 1):
            dolar_profit_loss = datas[i + 1][1] - datas[i][1]
            euro_profit_loss = datas[i + 1][2] - datas[i][2]
            altin_profit_loss = datas[i + 1][3] - datas[i][3]

            print(f"Tarih Aralığı: {datas[i][0]} - {datas[i + 1][0]}")
            print(f"Dolar Kar/Zararı: {dolar_profit_loss:.2f} TL")
            print(f"Euro Kar/Zararı: {euro_profit_loss:.2f} TL")
            print(f"Altın Kar/Zararı: {altin_profit_loss:.2f} TL")
            print()

        last_index = len(datas) - 1
        dolar_profit_loss = datas[last_index][1] - datas[last_index - 1][1]
        euro_profit_loss = datas[last_index][2] - datas[last_index - 1][2]
        altin_profit_loss = datas[last_index][3] - datas[last_index - 1][3]

        print(f"Tarih Aralığı: {datas[last_index - 1][0]} - {datas[last_index][0]}")
        print(f"Dolar Kar/Zararı: {dolar_profit_loss:.2f} TL")
        print(f"Euro Kar/Zararı: {euro_profit_loss:.2f} TL")
        print(f"Altın Kar/Zararı: {altin_profit_loss:.2f} TL")

    def getTotalAssets(self):
        self.cursor.execute("SELECT SUM(dolar), SUM(euro), SUM(altin) FROM Currency")
        total_assets = self.cursor.fetchone()
        if total_assets is None:
            return (0, 0, 0)
        return tuple(0 if asset is None else asset for asset in total_assets)

    def get_data_for_plotting(self):
        self.cursor.execute("SELECT * FROM Currency ORDER BY tarih")
        datas = self.cursor.fetchall()
        return datas

    def delete_all_data(self):
        try:
            self.cursor.execute("DELETE FROM Currency")
            self.baglanti.commit()
            print("Tüm veriler silindi. Bakiyeler sıfırlandı.")
        except sqlite3.Error as e:
            print(f"SQLite hatası: {e}")

    def close_baglanti(self):
        self.baglanti.close()

class App:
    def __init__(self, mainn):
        self.mainn = mainn
        self.mainn.title("Döviz & Altın Takip Uygulaması")

        self.label_dolar = Label(mainn, text="Dolar", font="Calibri")
        self.label_dolar.pack()
        self.entry_dolar = Entry(mainn)
        self.entry_dolar.pack()

        self.label_euro = Label(mainn, text="Euro", font="Calibri")
        self.label_euro.pack()
        self.entry_euro = Entry(mainn)
        self.entry_euro.pack()

        self.label_gold = Label(mainn, text="Altın", font="Calibri")
        self.label_gold.pack()
        self.entry_gold = Entry(mainn)
        self.entry_gold.pack()

        self.button_kaydet = Button(mainn, text="Kaydet", command=self.save_datas)
        self.button_kaydet.pack()



        self.button_getir = Button(mainn, text="Verileri Getir", command=self.get_datas)
        self.button_getir.pack()

        self.button_karzarar = Button(mainn, text="Kar/Zarar Hesapla", command=self.calculate_profit_loss)
        self.button_karzarar.pack()

        self.label_total_assets = Label(mainn, text="Toplam Varlık: 0.0$  0.0£ 0.0g", font="Calibri")
        self.label_total_assets.pack()

        self.button_plot = Button(mainn, text="Grafik Çiz", command=self.plot_asset_changes)
        self.button_plot.pack()

        self.button_sil = Button(mainn, text="Verileri Sil", command=self.onayla_ve_sil)
        self.button_sil.pack()

        self.veritabani = DataBaseOperation()
        self.update_rates()

    def update_rates(self):
        fetch_api_data()
        try:
            self.entry_dolar.delete(0, END)
            self.entry_dolar.insert(0, currency_rates.get("USD", 0))
            self.entry_euro.delete(0, END)
            self.entry_euro.insert(0, currency_rates.get("EUR", 0))
            self.entry_gold.delete(0, END)
            self.entry_gold.insert(0, "0")
        except AttributeError as e:
            print(f"Hata: {e}")
        except ValueError as e:
            print(f"Hata: {e}")
        except Exception as e:
            print(f"API'den veri alınırken hata oluştu: {e}")

    def save_datas(self):
        dolar_text = self.entry_dolar.get()
        if dolar_text:
            dolar = float(dolar_text)
        else:
            dolar = 0.0

        euro_text = self.entry_euro.get()
        if euro_text:
            euro = float(euro_text)
        else:
            euro = 0.0

        altin_text = self.entry_gold.get()
        if altin_text:
            altin = float(altin_text)
        else:
            altin = 0.0

        self.veritabani.add_data(dolar, euro, altin)
        self.get_total_assets()

    def update_datas(self):
        dolar_text = self.entry_dolar.get()
        if dolar_text:
            dolar = float(dolar_text)
        else:
            dolar = 0.0

        euro_text = self.entry_euro.get()
        if euro_text:
            euro = float(euro_text)
        else:
            euro = 0.0

        altin_text = self.entry_gold.get()
        if altin_text:
            altin = float(altin_text)
        else:
            altin = 0.0

        self.veritabani.update_data(dolar, euro, altin)
        self.get_total_assets()

    def get_datas(self):
        self.veritabani.get_data()

    def calculate_profit_loss(self):
        self.veritabani.calculate_profit_loss()

    def get_total_assets(self):
        total_dolar, total_euro, total_altin = self.veritabani.getTotalAssets()
        self.label_total_assets.config(text=f"Toplam Varlık: {total_dolar:.2f}$, {total_euro:.2f}€, {total_altin:.2f}g")

    def plot_asset_changes(self):
        datas = self.veritabani.get_data_for_plotting()

        dates = [data[0] for data in datas]
        dolar_values = [data[1] for data in datas]
        euro_values = [data[2] for data in datas]
        altin_values = [data[3] for data in datas]

        fig, ax = plt.subplots()
        ax.plot(dates, dolar_values, label='Dolar', color='blue')
        ax.plot(dates, euro_values, label='Euro', color='green')
        ax.plot(dates, altin_values, label='Altın', color='gold')

        ax.set_xlabel('Tarih')
        ax.set_ylabel('Değer')
        ax.set_title('Döviz ve Altın Değerleri')
        ax.legend()

        plt.xticks(rotation=45)
        plt.tight_layout()

        canvas = FigureCanvasTkAgg(fig, master=self.mainn)
        canvas.get_tk_widget().pack()

    def onayla_ve_sil(self):
        onay = messagebox.askyesno(title="Onay", message="Tüm verileri silmek istediğinizden emin misiniz?")
        if onay:
            self.veritabani.delete_all_data()
            self.get_total_assets()

root = Tk()
app = App(root)
root.mainloop()