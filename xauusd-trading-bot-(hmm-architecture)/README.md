# Project Trading Bot XAUUSD

Struktur project ini mengikuti arsitektur sistemik 5 komponen:

1. **Brain**: Deteksi regime market (HMM).
2. **Allocation**: Pengaturan ukuran posisi.
3. **Safety**: Manajemen risiko global.
4. **Broker**: Integrasi MetaTrader 5.
5. **Dashboard**: Visualisasi Streamlit.

## Cara Menjalankan
1. Install dependencies: `pip install -r requirements.txt`
2. Konfigurasi `.env` dengan kredensial MT5.
3. Jalankan bot: `python main.py`
4. Jalankan dashboard: `streamlit run src/dashboard/app.py`
