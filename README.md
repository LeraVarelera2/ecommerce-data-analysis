# E-Commerce Data Analysis

## Deskripsi Proyek

Proyek ini merupakan analisis data E-Commerce Public Dataset dari Olist untuk memahami performa penjualan produk, keterlambatan pengiriman, dan segmentasi pelanggan.

Analisis dilakukan menggunakan Python, Pandas, Matplotlib, Seaborn, dan Plotly. Hasil analisis disajikan melalui notebook Jupyter dan dashboard interaktif menggunakan Streamlit.

## Pertanyaan Bisnis

1. Bagaimana tren total nilai penjualan produk setiap bulan berdasarkan kategori produk selama periode September 2016–Agustus 2018, dan kategori produk apa yang memberikan kontribusi penjualan terbesar?
2. Bagaimana persentase keterlambatan pengiriman berdasarkan bulan pembelian pesanan selama periode September 2016–Agustus 2018, dan pada periode kapan keterlambatan paling tinggi terjadi?

## Hasil Analisis

### 1. Penjualan Produk

- Total nilai penjualan produk: R$13.221.498,11.
- Kategori dengan nilai penjualan terbesar: Health Beauty.
- Nilai penjualan Health Beauty: R$1.233.131,72.

### 2. Keterlambatan Pengiriman

- Jumlah pesanan yang dianalisis: 96.470.
- Rata-rata persentase keterlambatan bulanan: 10,52%.
- Keterlambatan tertinggi terjadi pada Maret 2018 sebesar 21,36%.

### 3. Segmentasi Pelanggan (RFM)

Analisis RFM digunakan untuk mengelompokkan pelanggan berdasarkan:

- **Recency:** jarak waktu sejak transaksi terakhir.
- **Frequency:** frekuensi transaksi.
- **Monetary:** nilai pembelian produk.

Segmentasi dilakukan menggunakan aturan pengelompokan berbasis skor RFM untuk mengidentifikasi karakteristik pelanggan.

## Teknologi yang Digunakan

- Python 3.10
- Pandas
- Matplotlib
- Seaborn
- Plotly
- Streamlit
- Jupyter Notebook / Google Colab

## Struktur Proyek

```text
ecommerce_dashboard/
├── data/
│   ├── orders_dataset.csv
│   ├── order_items_dataset.csv
│   ├── order_payments_dataset.csv
│   ├── order_reviews_dataset.csv
│   ├── customers_dataset.csv
│   ├── products_dataset.csv
│   ├── product_category_name_translation.csv
│   ├── sellers_dataset.csv
│   ├── geolocation_dataset.csv
│   ├── category_sales.csv
│   ├── monthly_delivery.csv
│   ├── monthly_sales.csv
│   └── segment_summary.csv
├── dashboard.py
├── notebook.ipynb
├── README.md
├── requirements.txt
└── url.txt
```

## Cara Menjalankan Dashboard

1. Pastikan Python sudah terpasang.
2. Buka terminal pada folder proyek.
3. Buat virtual environment:

```bash
python -m venv venv
```

4. Aktifkan virtual environment pada Windows:

```bash
.\venv\Scripts\Activate.ps1
```

5. Instal library:

```bash
pip install -r requirements.txt
```

6. Jalankan dashboard:

```bash
streamlit run dashboard.py
```

Dashboard akan terbuka melalui browser secara lokal.

## Catatan Pengolahan Data

- Nilai penjualan dihitung berdasarkan harga produk (`price`), tidak termasuk biaya pengiriman (`freight_value`).
- Analisis penjualan menggunakan transaksi dengan status pesanan terkirim (`delivered`).
- Analisis keterlambatan hanya menggunakan pesanan terkirim yang memiliki tanggal pengiriman aktual dan estimasi.
- Analisis RFM menggunakan data transaksi yang telah terkirim.
- Nilai Monetary pada analisis RFM menggunakan harga produk, tidak termasuk biaya pengiriman.
- Mata uang pada dataset adalah Brazilian Real (R$).
