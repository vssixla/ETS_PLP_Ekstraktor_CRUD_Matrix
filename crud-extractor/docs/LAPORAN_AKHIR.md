# Laporan Akhir

## 1. Hasil evaluasi

Tempel keluaran `python evaluate.py` setelah `data/ground_truth.csv` dilengkapi.

```
Dievaluasi: audit.sql, campuran_error.sql, laporan_penjualan.sql, pemeliharaan.sql (27 triple)

Metode   Precision  Recall     F1
parser        1.00    1.00   1.00
regex         0.65    0.81   0.72

[regex]
  salah ditemukan (FP): ('audit.sql', 16, 'sesi', 'R')
  salah ditemukan (FP): ('campuran_error.sql', 4, 'pesanan', 'R')
  salah ditemukan (FP): ('campuran_error.sql', 8, 'keranjang', 'R')
  salah ditemukan (FP): ('laporan_penjualan.sql', 2, 'pelanggan', 'D')
  salah ditemukan (FP): ('laporan_penjualan.sql', 2, 'pelanggan', 'R')
  salah ditemukan (FP): ('laporan_penjualan.sql', 2, 'pesanan', 'R')
  salah ditemukan (FP): ('laporan_penjualan.sql', 2, 'rahasia', 'R')
  salah ditemukan (FP): ('laporan_penjualan.sql', 15, 'pesanan', 'R')
  salah ditemukan (FP): ('pemeliharaan.sql', 2, 'crm.alamat', 'R')
  salah ditemukan (FP): ('pemeliharaan.sql', 2, 'crm.pelanggan', 'R')
  salah ditemukan (FP): ('pemeliharaan.sql', 2, 'pelanggan_lama', 'U')
  salah ditemukan (FP): ('pemeliharaan.sql', 15, 'crm.alamat', 'R')
  terlewat (FN):       ('audit.sql', 2, 'pesanan', 'R')
  terlewat (FN):       ('laporan_penjualan.sql', 3, 'pelanggan', 'R')
  terlewat (FN):       ('laporan_penjualan.sql', 3, 'pesanan', 'R')
  terlewat (FN):       ('pemeliharaan.sql', 3, 'crm.alamat', 'R')
  terlewat (FN):       ('pemeliharaan.sql', 3, 'crm.pelanggan', 'R')

```

## 2. Tiga kasus di mana regex salah

Untuk tiap kasus: SQL-nya, kesalahan regex, dan mengapa parser benar (kaitkan dengan konsep
lexing, parsing, atau resolusi).

#1. Komentar terbaca sebagai perintah. Pada laporan_penjualan.sql baris 2 terdapat komentar -- DELETE FROM pelanggan. Regex menganggap teks tersebut sebagai perintah SQL yang sebenarnya, sehingga tabel pelanggan keliru teridentifikasi sebagai D. Sementara itu, parser dapat mengenalinya dengan benar karena lexer menghapus komentar sebelum proses parsing, sehingga teks komentar tidak ikut diproses sebagai token.

#2. Teks dalam string dianggap sebagai nama tabel. Pada laporan_penjualan.sql baris 6 terdapat string 'FROM rahasia'. Regex menganggap kata "rahasia" sebagai nama tabel yang sedang dibaca, padahal kata tersebut hanya bagian dari isi string. Parser tidak mengalami kesalahan ini karena lexer mengenali seluruh teks tersebut sebagai satu token STRING, sehingga kata FROM di dalamnya tidak dianggap sebagai keyword SQL.

#3. Subquery dan JOIN tidak terdeteksi dengan tepat. Pada audit.sql baris 2 terdapat perintah FROM pelanggan p, pesanan o, tetapi regex melewatkan tabel kedua, yaitu pesanan, yang ditulis setelah tanda koma. Kesalahan serupa juga terjadi pada laporan_penjualan.sql baris 5, ketika regex tidak menangkap tabel yang ditulis setelah JOIN. Sebaliknya, parser dapat membaca struktur FROM dengan benar karena memprosesnya sebagai daftar sumber tabel, bukan sekadar mencari kata setelah FROM.

## 3. Batas pendekatan kami

Minimal tiga hal yang **tidak bisa** ditangani dengan benar oleh tool ini meskipun semua bug
sudah diperbaiki. Untuk tiap batas: contoh SQL atau situasinya, akibatnya pada CRUD matrix,
dan informasi apa yang dibutuhkan untuk mengatasinya.

1.
2.
3.

## 4. Pembagian kerja

Siapa mengerjakan apa, dan bagaimana kalian memastikan keduanya memahami seluruh kode.
