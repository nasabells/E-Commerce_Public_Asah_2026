# Proyek Analisis Data: E-Commerce Public Dataset

Analisis data transaksi e-commerce Olist (Brasil) periode 2017-2018 dan dashboard interaktif menggunakan Streamlit.

## Pertanyaan Bisnis
1. Kategori produk apa saja yang termasuk 10 besar berdasarkan total revenue dan jumlah item terjual, dan kategori mana yang hanya unggul di salah satu metrik?
2. Bagaimana tren jumlah order dan total revenue per bulan (Januari 2017 - Agustus 2018), dan pada bulan apa keduanya mencapai puncak?
3. Berapa persentase order *delivered* yang terlambat dari estimasi, dan berapa selisih rata-rata skor review antara order terlambat dan tepat waktu?
4. State mana yang memiliki pelanggan unik terbanyak, dan berapa kontribusi 5 state teratas terhadap total order?

## Struktur Folder
```
├── dashboard/
│   ├── dashboard.py
│   └── main_data.csv
├── data/                     # dataset mentah (CSV)
├── notebook.ipynb
├── requirements.txt
└── README.md
```

## Setup Environment
```
pip install -r requirements.txt
```

## Menjalankan Dashboard
```
cd dashboard
python -m streamlit run dashboard.py
```

## Sumber Data
E-Commerce Public Dataset (Olist) dari Kaggle.