# Laporan Bug

Salin blok di bawah untuk setiap bug. Bagian **Akar masalah** wajib ditulis dengan kata-kata
sendiri dan memakai konsep dari *Crafting Interpreters* (sebutkan bab). Bagian ini diuji lisan.

---
## Bug 1: Parser Membuang Statement Valid setelah Kesalahan Sintaks

**Ditemukan oleh:** ALIA ARDANI · **Diperbaiki oleh:** ALIA ARDANI

**Gejala.** 
Pada file campuran_error.sql, statement SELECT di baris 4 mengandung kesalahan sintaks. Program melaporkan kesalahan tersebut, tetapi hanya memproses SELECT pertama di baris 2. Statement UPDATE di baris 6 dan DELETE di baris 8 yang valid ikut terlewat.

Pada SPESIFIKASI.md bagian 6, parser seharusnya membuang token sampai dan termasuk tanda ";" berikutnya, kemudian melanjutkan pemrosesan statement setelahnya. Statement rusak menghasilkan tepat satu parse error dan tidak dihitung dalam CRUD matrix.

**Reproduksi minimal.** SQL
```
SELECT id, FROM pesanan;
UPDATE produk SET stok = 1;
```
Pada kode lama, kesalahan pada SELECT menyebabkan UPDATE ikut terlewat. Hasil yang diharapkan adalah satu parse error dan operasi U pada tabel produk.

**Akar masalah.**
Fungsi _synchronize() pada kode lama terus memanggil _advance() selama belum mencapai akhir input. Fungsi tersebut tidak memeriksa tanda titik koma sebagai batas akhir statement rusak. Akibatnya, token dari statement valid setelahnya ikut dibuang hingga akhir file.

Masalah ini berkaitan dengan konsep panic-mode error recovery dalam Crafting Interpreters Bab 6, bagian 6.3.1 dan 6.3.3. Recovery memerlukan titik sinkronisasi agar parser dapat kembali memproses input pada batas statement. Dalam proyek ini, batas tersebut ditetapkan pada tanda ; berikutnya.

**Perbaikan.**
Perubahan dilakukan pada fungsi _synchronize() dalam crud/parser.py. Setiap token yang dilewati diperiksa jenisnya. Jika token tersebut adalah T.SEMICOLON, fungsi langsung selesai sehingga parsing dapat dilanjutkan dari token setelah titik koma.

def _synchronize(self) -> None:
    # Panic-mode recovery: lewati statement rusak sampai termasuk ';'.
    while not self._at_end():
        token = self._advance()
        if token.type == T.SEMICOLON:
            return

Alternatif yang dipertimbangkan adalah menghentikan recovery ketika menemukan keyword awal statement, seperti SELECT. Alternatif ini tidak dipilih karena SELECT juga dapat muncul dalam subquery pada statement yang sedang dibuang. Selain itu, spesifikasi secara tegas menetapkan titik koma sebagai batas recovery.

**Test regresi.**
Test ditambahkan pada tests/test_tambahan.py dengan nama:
test_recovery_memproses_statement_setelah_error

Test menggunakan satu SELECT valid, satu SELECT rusak, kemudian UPDATE dan DELETE valid. Pemeriksaan mencakup tidak adanya lexical error, tepat satu parse error pada baris yang benar, kelanjutan pemrosesan ketiga statement valid, serta kesesuaian CRUD matrix.

Perintah pengujian:
python -m pytest tests/test_tambahan.py::test_recovery_memproses_statement_setelah_error -v
Sebelum perbaikan, test FAILED karena hasil hanya memuat statement SELECT pertama. Setelah perbaikan, test yang sama PASSED tanpa mengubah isi test.

**Peran AI.**
AI membantu saya untuk memvalidasi kalau temuan bug dan perbaikan yang akan temukan itu tepat dan sesuai dengan gejala pada bug ini, AI juga membantu saya melakukan dalam memperbaiki serta memberikan tambahan kode program dalam memperbaiki fungsi _synchronize() dan test_recovery_memproses_statement_setelah_error .


## Bug 2: Keyword Huruf Kecil Tidak Dikenali sebagai KEYWORD

**Ditemukan oleh:** SHAHNAZ SASKIA PUTRI · **Diperbaiki oleh:** SHAHNAZ SASKIA PUTRI

**Gejala.**
Berdasarkan SPESIFIKASI.md bagian 2.2, keyword tidak membedakan huruf besar dan kecil. Jadi, 'select', 'Select', dan 'SELECT' seharusnya dikenali sebagai token KEYWORD dengan nilai huruf kapital. Namun, pada kode lama, lexer mengenali select sebagai token IDENT dengan nilai 'select'. Akibatnya, test test_keyword_huruf_kecil gagal karena token pertama bertipe IDENT, bukan KEYWORD. Hal ini menyebabkan parser tidak dapat memproses query yang menggunakan keyword huruf kecil.


**Reproduksi minimal.** SQL
```
select id from t
```
Seharusnya menghasilkan token KEYWORD 'SELECT', IDENT 'id', KEYWORD 'FROM', dan IDENT 't'. Namun, kode lama mengenali 'select' dan 'from' sebagai IDENT.


**Akar masalah.**
Lexer membaca satu kata utuh kemudian mencocokkannya dengan daftar KEYWORDS yang hanya berisi huruf kapital. Karena kode lama tidak mengubah huruf sebelum melakukan pencocokan, 'select' dianggap berbeda dari 'SELECT' dan akhirnya dikategorikan sebagai IDENT.

Masalah ini berkaitan dengan konsep Reserved Words and Identifiers dalam Crafting Interpreters Bab 4, yaitu pencocokan lexeme dengan daftar keyword. Sesuai spesifikasi proyek, pencocokan harus dilakukan tanpa membedakan huruf besar dan kecil. Kesalahan lexer ini kemudian memengaruhi parser karena parser bergantung pada jenis token yang dihasilkan.


**Perbaikan.**
Perbaikan dilakukan pada file 'crud/lexer.py' tepatnya pada fungsi pembaca kata. Metode '.upper()' digunakan untuk mengubah kata menjadi huruf kapital sebelum dicocokkan dengan KEYWORDS dan saat menentukan nilai token KEYWORD.

Untuk token IDENT, teks asli tetap dipertahankan karena normalisasi nama tabel, alias, dan kolom menjadi huruf kecil merupakan tugas parser sesuai SPESIFIKASI.md bagian 2.2.

Alternatif yang dipertimbangkan adalah menambahkan berbagai variasi huruf keyword ke dalam daftar KEYWORDS. Namun, cara ini tidak dipilih karena akan menghasilkan terlalu banyak kombinasi penulisan. Penggunaan .upper() lebih sederhana dan sesuai dengan spesifikasi.


**Test regresi.**
Test test_keyword_huruf_campuran ditambahkan pada tests/test_tambahan.py untuk memastikan input Select x FrOm t menghasilkan nilai token SELECT dan FROM. Test bawaan test_keyword_huruf_kecil yang sebelumnya gagal karena tipe token IDENT berhasil dilewati setelah perbaikan. Jumlah test yang gagal pada seluruh suite juga berkurang dari 5 menjadi 4, sementara test tambahan berhasil dijalankan.


**Peran AI.**
Proses debugging dilakukan dengan bantuan AI yang memberikan arahan dalam menemukan penyebab bug dan menentukan perbaikannya. Selama proses tersebut, saya juga mempelajari setiap perubahan yang disarankan, kemudian hasil perbaikan diverifikasi dengan menjalankan test.






## Bug 1: (judul singkat)

**Ditemukan oleh:** (nama) · **Diperbaiki oleh:** (nama)

**Gejala.** Input, output yang didapat, dan output yang diharapkan menurut SPESIFIKASI.md
(sebutkan bagiannya).

**Reproduksi minimal.** SQL terpendek yang memicu bug:

```sql

```

**Akar masalah.** Mengapa kode lama salah? Konsep apa yang dilanggar?

**Perbaikan.** File dan fungsi yang diubah, serta alasannya. Sebutkan juga perbaikan
alternatif yang kalian pertimbangkan dan alasan tidak memilihnya.

**Test regresi.** Nama test di `tests/test_tambahan.py` yang gagal sebelum perbaikan dan lulus
sesudahnya.

**Peran AI.** Apakah AI membantu menemukan atau memperbaiki bug ini? Bagaimana kalian
memverifikasinya?

---
