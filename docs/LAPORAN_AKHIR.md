# Laporan Akhir

## 1. Hasil evaluasi
Evaluasi dilakukan menggunakan python evaluate.py terhadap empat file SQL dengan 27 label ground truth. Setiap label memuat nama file, baris awal statement, nama tabel, dan satu operasi CRUD. Label ditentukan berdasarkan aturan dalam SPESIFIKASI.md

Hasil Evaluasi: 
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
Parser menghasilkan 27 label benar tanpa false positive (FP) maupun false negative (FN). Baseline regex menghasilkan 22 label benar, 12 FP, dan 5 FN. Precision menunjukkan ketepatan label yang dihasilkan, recall menunjukkan kelengkapan label yang ditemukan, sedangkan F1 menggabungkan keduanya.


## 2. Tiga kasus di mana regex salah
### 1. Komentar Terbaca Sebagai Perintah
Pada laporan_penjualan.sql baris 2 terdapat komentar:
```
-- DELETE FROM pelanggan. 
```
Regex menganggap teks tersebut sebagai perintah SQL yang sebenarnya, sehingga tabel pelanggan keliru teridentifikasi sebagai D. Hal ini terlihat pada hasil evaluasi berupa label ('laporan_penjualan.sql', 2, 'pelanggan', 'D'), yang termasuk false positive (FP).

Sementara itu, parser dapat mengenalinya dengan benar karena lexer melewati komentar sebelum proses parsing, sehingga teks komentar tidak ikut diproses sebagai token. Perilaku ini sesuai dengan SPESIFIKASI.md bagian 2.3 yang menyatakan bahwa komentar tidak menghasilkan token.

### 2. Teks Dalam String Dianggap Sebagai Nama Tabel
Pada laporan_penjualan.sql baris 6 terdapat string 'FROM rahasia' dalam statement berikut:
```
SELECT p.nama, SUM(o.total) AS omzet
FROM pelanggan p
JOIN pesanan o ON o.pelanggan_id = p.id
WHERE o.status = 'LUNAS' AND o.catatan <> 'FROM rahasia'
GROUP BY p.nama;
```
Regex menganggap kata rahasia sebagai nama tabel yang sedang dibaca, padahal kata tersebut hanya bagian dari isi string. Hal ini terlihat pada hasil evaluasi berupa label ('laporan_penjualan.sql', 2, 'rahasia', 'R'), yang termasuk false positive (FP). Nomor baris 2 tersebut merupakan keluaran regex, sedangkan string sebenarnya berada pada baris 6.

Parser tidak mengalami kesalahan ini karena lexer mengenali seluruh teks tersebut sebagai satu token STRING, sehingga kata FROM di dalamnya tidak dianggap sebagai keyword SQL. Perilaku ini sesuai dengan SPESIFIKASI.md bagian 2.4 dan berkaitan dengan konsep lexing dalam Crafting Interpreters Bab 4, yaitu mengenali literal string sebagai satu token. Karena rahasia tidak menjadi sumber tabel dalam AST, analyzer hanya mencatat pembacaan tabel pelanggan dan pesanan.

### 3. Tabel Setelah Koma Pada FROM Terlewat
Statement pertama pada audit.sql adalah:
```
SELECT p.id, p.nama
FROM pelanggan p, pesanan o
WHERE o.pelanggan_id = p.id
  AND o.tanggal BETWEEN :mulai AND :akhir
  OR p.level = 'gold' AND p.aktif = 1;
```
Regex melewatkan label ('audit.sql', 2, 'pesanan', 'R'), sehingga tabel kedua dalam daftar FROM tidak tercatat sebagai sumber pembacaan. Parser mengikuti grammar FROM table_ref { "," table_ref } pada SPESIFIKASI.md bagian 3. Setiap sumber yang dipisahkan koma dimasukkan ke AST, kemudian analyzer memberikan operasi R kepada kedua tabel sesuai bagian 5.


## 3. Batas pendekatan kami
### 1. Tidak Memiliki Informasi Skema dan Identitas Tabel dari Database
Contoh:
```
SELECT nama FROM pelanggan p, pesanan o;
SELECT id FROM pelanggan;
SELECT id FROM crm.pelanggan;
SELECT * FROM pelanggan;
```
Pada query pertama, kolom nama tidak menunjukkan secara jelas berasal dari tabel mana. Karena query menggunakan dua tabel, yaitu pelanggan dan pesanan, tool tidak dapat memastikan asal kolom tersebut. Sesuai dengan SPESIFIKASI.md bagian 4.3, resolver akan memberikan warning bahwa kolom nama ambigu dan nilai resolved tetap None. Meskipun CRUD Matrix tetap mencatat kedua tabel sebagai R, informasi pada keluaran --kolom menjadi kurang lengkap karena asal kolom nama belum dapat dipastikan.

Pada dua query berikutnya, pelanggan dan crm.pelanggan dianggap sebagai dua nama tabel yang berbeda. Padahal, jika skema default yang digunakan adalah crm, keduanya bisa saja merujuk ke tabel yang sama. Karena tool hanya membaca nama tabel yang tertulis pada query dan tidak memiliki informasi skema database, tabel yang sebenarnya sama bisa tercatat sebagai dua tabel berbeda dalam CRUD Matrix.

Sementara itu, pada query SELECT *, tool tetap mencatat tabel pelanggan sebagai R, tetapi tidak dapat menampilkan nama-nama kolom yang dibaca karena informasi kolom tersebut tidak tersedia.

Untuk mengatasi keterbatasan ini, tool memerlukan informasi tambahan dari database, seperti daftar kolom, identitas tabel, dan aturan skema default. Namun, informasi tersebut belum tersedia karena, sesuai dengan SPESIFIKASI.md bagian 7, tool hanya menganalisis teks query tanpa membaca struktur database secara langsung.

### 2. Tidak Mengetahui Tabel Dasar View dan Efek Trigger
Contoh: 
```
SELECT * FROM v_laporan;
DELETE FROM pelanggan WHERE id = :id;
```
Pada query pertama, tool hanya mencatat v_laporan sebagai tabel yang dibaca (R), tanpa mengetahui tabel yang digunakan dalam definisi view tersebut. Misalnya, jika v_laporan mengambil data dari tabel pelanggan dan pesanan, pembacaan kedua tabel tersebut tidak ikut tercatat dalam CRUD matrix karena tool tidak memiliki definisi view-nya.

Masalah serupa terjadi pada trigger. Jika perintah DELETE pada tabel pelanggan secara otomatis menjalankan trigger yang menambahkan data ke tabel log_penghapusan, tool hanya mencatat D pada pelanggan. Operasi C pada log_penghapusan tidak terdeteksi karena perintah penambahan data tersebut berada dalam trigger, bukan dalam query yang dianalisis.

View dan trigger berada di luar lingkup SPESIFIKASI.md bagian 9. Untuk mengatasi keterbatasan ini, diperlukan definisi view dan trigger dari database, serta pengembangan analisis agar tool dapat menelusuri tabel dan operasi yang digunakan di dalamnya.

### 3. Grammar Hanya Mendukung Subset SQL yang Ditentukan
Contoh: 
```
WITH aktif AS (
    SELECT id FROM pelanggan WHERE aktif = 1
)
SELECT id FROM aktif;

SELECT id FROM pelanggan
UNION
SELECT id FROM pelanggan_arsip;
```
Query yang menggunakan CTE (WITH) dan UNION belum dapat diproses karena strukturnya belum didukung dalam grammar parser. Keduanya berada di luar lingkup SPESIFIKASI.md bagian 9. Akibatnya, statement menghasilkan parse error dan tabel yang terlibat dalam statement tersebut tidak tercatat dalam CRUD matrix, sesuai aturan bagian 5.

Untuk mengatasi keterbatasan ini, diperlukan aturan sintaks CTE dan UNION sebagai dasar pengembangan grammar, AST, resolver, serta analyzer. Pada CTE, tool perlu mengenali bahwa aktif merupakan nama hasil query sementara dan menelusuri tabel sumbernya, yaitu pelanggan. Pada UNION, tool perlu membaca kedua query agar tabel pelanggan dan pelanggan_arsip sama-sama tercatat sebagai R.


## 4. Pembagian kerja
Pengerjaan proyek dilakukan oleh Alia Ardani dan Shahnaz Saskia Putri. Sebelum melakukan perbaikan, kami berdiskusi dan melakukan brainstorming bersama untuk mencari masalah pada program. Kami membandingkan program dengan ketentuan yang ada di SPESIFIKASI.md, kemudian mencatat masalah yang ditemukan, kemungkinan penyebabnya, dan hal-hal yang perlu diperbaiki.

Ketika salah satu dari kami menemukan masalah, temuan tersebut langsung disampaikan kepada diantara kami. Misalnya, ketika Alia menemukan suatu masalah, Alia akan mengabarkannya kepada Shahnaz. Setelah itu, Shahnaz akan memeriksa kembali apakah masalah tersebut memang sesuai dengan spesifikasi dan apakah penyebab yang ditemukan sudah tepat. Jika kami memiliki pemahaman yang sama dan hasil pemeriksaan mendukung temuan tersebut, perbaikan dapat dilanjutkan. Namun, jika masih ada perbedaan pendapat atau penyebabnya belum jelas, kami tidak langsung melakukan perubahan. Kami akan memeriksa kembali kode, spesifikasi, dan hasil pengujian sampai menemukan penjelasan yang sesuai.

Untuk pembagian tanggung jawab dalam pengerjaan proyek adalah sebagai berikut:
| Anggota | Tanggung Jawab Utama |
| :--- | :--- |
| **Alia Ardani** | - T1: Dukungan `INSERT ... SELECT`.<br>- T2: Kolom tanpa qualifier.<br>- Bug 1: Error recovery.<br>- Bug 3: Operator `<>`.<br>- Bug 7: Shadowing.<br>- Bug 8: Presedensi AND/OR.<br>- Bug 9: `LEFT OUTER JOIN`.<br>- Bug 10: Parameter berawalan angka.<br>- Bug 11: Diagnostik resolver antar pemanggilan.<br>- Kasus Tepi 1: Input Kosong Menghasilkan EOF.<br>- Kasus Tepi 2: Input Hanya WhiteSpace.<br>- Kasus Tepi 3: Komentar Tanpa NewLine di Akhir Input. |
| **Shahnaz Saskia Putri** | - T3: Komentar blok.<br>- Bug 2: Keyword tidak peka huruf besar/kecil.<br>- Bug 4: Escape kutip dalam string.<br>- Bug 5: Subquery UPDATE.<br>- Bug 6: Scope DELETE.<br>- Bug 11: Diagnostik resolver antar pemanggilan.<br>- Pelabelan ground truth `audit.sql` dan `pemeliharaan.sql`.<br>- Kasus Tepi 3: Komentar Tanpa NewLine di Akhir Input.<br>- Kasus Tepi 4: Penanda Komentar dalam String.<br>- Kasus Tepi 5: Parameter Titik Dua Tanpa Nama. |

Dalam proses pengerjaan, AI juga digunakan sebagai alat bantu untuk berdiskusi, mencari kemungkinan penyebab masalah, dan memeriksa usulan perbaikan. Namun, setiap hasil yang diperoleh tetap kami periksa kembali dengan mengacu pada spesifikasi dan hasil pengujian.