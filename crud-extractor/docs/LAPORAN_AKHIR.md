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

#1. Kolom tanpa qualifier pada lebih dari satu tabel. Contoh SELECT nama FROM pelanggan p, pesanan o;. Pada query tersebut, kolom nama tidak disertai qualifier/nama tabel yang menunjukkan asal kolomnya. Karena terdapat dua tabel yang digunakan, tool tidak dapat memastikan apakah kolom nama berasal dari tabel pelanggan/pesanan. Ini terjadi karena tool belum memiliki informasi skema database yang dapat digunakan untuk mencocokkan kolom dengan tabelnya. Resolver hanya memberikan warning "ambigu tanpa skema" dan nilai resolved tetap none. Akibatnya CRUD matrix masih bisa mencatat kedua tabel sebagai R tapi informasi kolom yang ditampilkan pada laporan (--kolom) jadi tidak lengkap karena kolom nama tidak berhasil diidentifikasi. Untuk mengatasi masalah ini, diperlukan skema database yang berisi daftar kolom pada setiap tabel.

#2. View, trigger, CTE, dan UNION. Contoh SELECT * FROM v_laporan;. Ketika query tersebut dijalankan, tool hanya mencatat v_laporan sebagai tabel yang dibaca (R) tanpa mengetahui tabel-tabel lain yang sebenarnya digunakan di dalam definisi view tersebut. Akibatnya aktivitas pembacaan terhadap tabel sumber tidak ikut tercatat dalam CRUD matrix. Masalah serupa juga terjadi pada trigger. Jika terdapat trigger yang secara otomatis menulis data ke tabel lain ketika perintah DELETE dijalankan, aktivitas penulisan tersebut tidak dapat terdeteksi oleh tool. Selain itu, query yang menggunakan CTE seperti WITH x AS (...) SELECT ... dan UNION seperti SELECT ... UNION SELECT ... belum dapat diproses karena strukturnya belum didukung dalam grammar parser. Akibatnya statement ditolak dan tabel yang terlibat tidak tercatat dalam matrix. Untuk mengatasi keterbatasan ini diperlukan definisi view dan trigger dari database serta pengembangan grammar parser agar dapat mengenali CTE dan UNION.

#3. *Nama tabel tanpa skema dan penggunaan SELECT . Contoh SELECT id FROM pelanggan; dan SELECT id FROM crm.pelanggan;. Kedua query tersebut dapat merujuk pada tabel yang sama tetapi tool menganggapnya sebagai dua tabel berbeda karena penulisan nama tabel yang satu tidak memakai skema, sedangkan yang lainnya memakai skema crm. Perbedaan penulisan ini menyebabkan data tabel tercatat secara terpisah sehingga baris pada CRUD matrix menjadi terpecah. Selain itu, saat query menggunakan SELECT *, tool hanya tahu bahwa seluruh kolom dalam tabel sedang dibaca tapi tidak dapat merinci nama masing-masing kolom yang digunakan. Untuk mengatasi masalah tersebut, diperlukan skema database agar tool dapat mengenali identitas tabel dan mengetahui kolom-kolom yang tersedia, serta aturan skema default untuk menentukan skema yang digunakan ketika nama tabel ditulis tanpa qualifier.

## 4. Pembagian kerja

Siapa mengerjakan apa, dan bagaimana kalian memastikan keduanya memahami seluruh kode.

Pekerjaan ini dikerjakan berdua oleh Alia Ardani dan Shahnaz Saskia Putri secara bergantian. Sebelum mengubah file, kami saling mengabari supaya tidak terjadi konflik di Git.

#Alia Ardani: T1, T2, bug 1 (error recovery), bug 3 (operator <>), bug 7 (scope dalam menutupi scope luar), bug 8 (presedensi AND/OR), bug 9 (LEFT OUTER JOIN), dan bug 10 (parameter berawalan angka), serta sebagian besar laporan bug.
#Shahnaz Saskia Putri: T3 (komentar blok), bug 2 (keyword huruf kecil), bug 4 (kutip ganda di string), bug 5 (subquery di UPDATE), bug 6 (scope DELETE), label ground truth untuk audit.sql dan pemeliharaan.sql, serta LAPORAN_AKHIR.

Agar saling faham, kami saling menjelaskan bagian yang dikerjakan partner, membaca laporan bug satu sama lain, dan menjalankan python -m crud.cli FILE --ast untuk melihat hasil parsing dan resolusi.