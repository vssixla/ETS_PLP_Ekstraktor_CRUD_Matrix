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


## Bug 3: Parser Membuang Statement Valid setelah Kesalahan Sintaks

**Ditemukan oleh:** ALIA ARDANI · **Diperbaiki oleh:** ALIA ARDANI

**Gejala.** 
Pada file laporan_penjualan.sql, terdapat kondisi berikut pada baris 6:
WHERE o.status = 'LUNAS' AND o.catatan <> 'FROM rahasia'

Operator <> digunakan untuk menyatakan “tidak sama dengan”. Namun, program menghasilkan pesan:
Baris 6, kolom 41: diharapkan ekspresi, ditemukan '>'

Pesan tersebut muncul karena lexer memecah <> menjadi dua token operator, yaitu < dan >. Parser kemudian menganggap < sebagai operator perbandingan dan mengharapkan ekspresi di sebelah kanannya. Akan tetapi, token berikutnya adalah >, yang tidak dapat menjadi awal ekspresi menurut grammar proyek.

Berdasarkan SPESIFIKASI.md bagian 2.5, lexer harus mengenali <> sebagai satu token bertipe OP dan menerapkan prinsip maximal munch, yaitu mengambil operator terpanjang yang cocok. Operator tersebut juga termasuk operator perbandingan yang diperbolehkan pada grammar bagian 3.

Akibat bug ini, statement SELECT yang sebenarnya valid gagal di-parse dan tidak masuk dalam hasil analisis CRUD.

**Reproduksi minimal.** SQL
SQL sederhana yang memicu bug:
SELECT id FROM t WHERE id <> 10;

Untuk mengisolasi masalah pada lexer, pengujian dapat menggunakan potongan ekspresi:
tokenize("a <> 10")

Perbedaan hasil token sebelum perbaikan dan hasil yang diharapkan adalah:
| Urutan | Hasil kode lama | Hasil yang diharapkan |
|:------:|-----------------|-----------------------|
| 1      | `IDENT`, `"a"`  | `IDENT`, `"a"`        |
| 2      | `OP`, `"<"`     | `OP`, `"<>"`          |
| 3      | `OP`, `">"`     | `NUMBER`, `"10"`      |
| 4      | `NUMBER`, `"10"`| `EOF`, `""`           |
| 5      | `EOF`, `""`     | —                     |

Potongan ekspresi ini digunakan agar kesalahan pembentukan token dapat diamati langsung tanpa melibatkan resolver dan analyzer.

**Akar masalah.**
Kesalahan berada pada fungsi _scan_token() dalam crud/lexer.py, khususnya pada cabang yang menangani karakter <. Kode awalnya adalah:
if ch == "<":
    op = "<=" if self._match("=") else "<"
    self._add(TokenType.OP, op, line, col)
    return

Kode tersebut hanya mempertimbangkan dua kemungkinan: operator <= apabila karakter berikutnya adalah =, atau operator < apabila karakter berikutnya bukan =. Tidak ada pemeriksaan untuk kemungkinan operator <>.

Ketika input mengandung <>, proses pada kode lama berlangsung sebagai berikut:
    1. _advance() membaca karakter <.
    2. _match("=") memeriksa karakter berikutnya, yaitu >.
    3. Karena > tidak sama dengan =, pemeriksaan menghasilkan False. Karakter > belum dikonsumsi.
    4. Lexer langsung menambahkan token operator < dan mengakhiri pemindaian token tersebut.
    5. Pada pemindaian berikutnya, karakter > dibaca dan menghasilkan token operator tersendiri.

Celahnya terletak pada keputusan lexer yang terlalu cepat mengakhiri operator setelah membaca <. Lexer belum memeriksa seluruh kemungkinan operator dua karakter yang dimulai dengan karakter tersebut.

Masalah ini berkaitan dengan konsep lookahead dan maximal munch pada Crafting Interpreters Bab 4, terutama bagian 4.5.2 tentang operator, 4.6 tentang lookahead, dan 4.7 tentang maximal munch. Lexer perlu melihat karakter berikutnya untuk menentukan apakah suatu karakter merupakan operator tunggal atau bagian dari operator yang lebih panjang.

Walaupun gejala akhirnya berupa parse error, akar masalahnya berada pada lexer. Parser menerima urutan token yang sudah salah, sehingga perbaikannya harus dilakukan pada tahap pembentukan token.

**Perbaikan.**
Perubahan dilakukan pada cabang if ch == "<": di fungsi _scan_token() dalam crud/lexer.py. Cabang tersebut diperluas agar menangani tiga kemungkinan operator: <=, <>, dan <.

if ch == "<":
    f self._match("="):
        op = "<="
    elif self._match(">"):
        op = "<>"
    else:
        op = "<"

    self._add(TokenType.OP, op, line, col)
     return

Perbaikan dilakukan pada bagian if ch == "<" dengan menambahkan pemeriksaan self._match(">") untuk mengenali operator <>. Fungsi _match() memeriksa sekaligus mengonsumsi karakter berikutnya apabila sesuai, sehingga < dan > dikenali sebagai satu token OP, bukan dua token terpisah. Sementara itu, percabangan if, elif, dan else tetap mempertahankan dukungan operator <= dan <. Pemanggilan _add() digunakan untuk menyimpan operator yang dikenali sebagai satu token, sedangkan return mengakhiri pemindaian token tersebut. Perubahan dilakukan pada lexer karena pengenalan operator merupakan tanggung jawab lexer.

**Test regresi.**
Test ditambahkan pada tests/test_tambahan.py dengan nama:
test_operator_tidak_sama_dipindai_sebagai_satu_token
Test memeriksa jenis, nilai, urutan, dan jumlah token. Pemeriksaan seluruh daftar token diperlukan untuk memastikan bahwa <> benar-benar menjadi satu token dan tidak meninggalkan token > tambahan.

Sebelum perbaikan, test menghasilkan FAILED dengan perbedaan utama:
At index 1 diff: ... '<' ... != ... '<>'

Setelah perbaikan lengkap diterapkan, test yang sama menghasilkan PASSED tanpa mengubah hasil yang diharapkan.
Test bawaan test_operator_multi_karakter juga dijalankan untuk memeriksa bahwa operator <=, >=, dan != tetap dikenali dengan benar.

Perintah pengujian:
python -m pytest tests/test_tambahan.py::test_operator_tidak_sama_dipindai_sebagai_satu_token tests/test_lexer.py::test_operator_multi_karakter -v

Hasil pengujian terakhir:
2 passed in 0.13s
Dalam proses penerapan perbaikan, pemanggilan _add() dan return sempat belum dimasukkan sehingga muncul LexError untuk karakter <. Setelah kedua baris tersebut dilengkapi dengan indentasi yang benar, kedua test lulus. Kesalahan sementara ini merupakan kekeliruan saat menerapkan perbaikan, bukan akar masalah pada kode awal.

Hasil tersebut membuktikan bahwa kasus <> yang diuji sudah benar dan operator pada test pembanding tetap bekerja. Pengujian ini belum membuktikan bahwa seluruh lexer atau seluruh pipeline bebas dari bug.


**Peran AI.**
AI membantu menghubungkan pesan parse error pada laporan_penjualan.sql dengan kesalahan pembentukan token operator <>. AI juga membantu menyusun test regresi, menjelaskan konsep lookahead dan maximal munch, serta menyarankan perubahan pada fungsi _scan_token().


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
