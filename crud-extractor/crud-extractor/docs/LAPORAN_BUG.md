# Laporan Bug

Salin blok di bawah untuk setiap bug. Bagian **Akar masalah** wajib ditulis dengan kata-kata
sendiri dan memakai konsep dari *Crafting Interpreters* (sebutkan bab). Bagian ini diuji lisan.

---

## TODO T1: Melengkapi Dukungan INSERT ... SELECT
Ditemukan oleh: ALIA ARDANI, berdasarkan penanda TODO(T1) pada kode awal · Diperbaiki oleh: ALIA ARDANI

**Gejala.** 
Program belum dapat memproses perintah INSERT yang mengambil data dari hasil query SELECT. Ketika menerima bentuk tersebut, parser menghasilkan pesan:
INSERT ... SELECT belum didukung, ditemukan 'SELECT'

Padahal, grammar pada SPESIFIKASI.md bagian 3 mengizinkan sumber data INSERT berupa VALUES maupun query SELECT. Berdasarkan aturan CRUD pada bagian 5, tabel tujuan INSERT mendapatkan operasi C, sedangkan tabel yang dibaca oleh SELECT mendapatkan operasi R. 

Akibat fitur ini belum diimplementasikan, statement INSERT SELECT yang valid dianggap mengalami kesalahan parsing dan tidak dapat dianalisis sebagaimana mestinya.

**Reproduksi minimal.**
INSERT INTO arsip SELECT id FROM pesanan;
Pada kode awal, parser menolak statement tersebut ketika mencapai keyword SELECT.

Hasil yang diharapkan adalah satu statement INSERT yang memiliki query SELECT sebagai sumber data, tanpa parse error. CRUD matrix yang diharapkan:
| Tabel     | Operasi |
|-------    |---------|
| `arsip`   | C       |
| `pesanan` | R       |

**Akar masalah.**
Fungsi _insert() dalam crud/parser.py sudah membaca keyword INSERT, tabel tujuan, dan daftar kolom tujuan jika tersedia. Fungsi tersebut juga sudah memiliki implementasi untuk sumber data berbentuk VALUES.

Namun, cabang yang mendeteksi keyword SELECT langsung menjalankan:
raise ParseError("INSERT ... SELECT belum didukung", self._peek())

Dengan demikian, parser sebenarnya sudah mengenali awal bentuk INSERT SELECT, tetapi belum melanjutkan pembacaan query tersebut. Ini merupakan bagian implementasi yang belum selesai, sesuai penanda TODO(T1).

Masalah ini berkaitan dengan konsep recursive descent parsing pada Crafting Interpreters Bab 6. Setiap aturan grammar diterjemahkan menjadi fungsi parser. Ketika aturan INSERT mengandung aturan SELECT, fungsi parser INSERT dapat memanggil fungsi parser SELECT yang sudah tersedia.

Keterkaitannya dengan Bab 5 adalah representasi sintaks dalam AST. Statement INSERT SELECT perlu direpresentasikan sebagai node INSERT yang menyimpan node SELECT di dalam field query. Jika query tersebut tidak dibentuk dan disimpan, tahap berikutnya tidak memiliki struktur yang diperlukan untuk menelusuri sumber data INSERT.

**Perbaikan.**
Perubahan dilakukan pada fungsi _insert() dalam crud/parser.py. Cabang yang sebelumnya menolak SELECT diganti dengan pemanggilan _select(), kemudian hasilnya disimpan dalam node ast.Insert:
if self._check_kw("SELECT"):
    query = self._select()
    return ast.Insert(
        table=table,
        columns=columns,
        values=[],
        query=query,
        line=start.line,
    )
raise ParseError("diharapkan VALUES atau SELECT", self._peek())

Perubahan ini memungkinkan INSERT menggunakan query SELECT sebagai sumber data. 
Fungsi _select() digunakan kembali untuk membaca query dan membentuk AST, sedangkan table dan columns mempertahankan informasi tabel tujuan serta kolom yang akan diisi. Atribut values=[] menunjukkan bahwa data tidak berasal dari klausa VALUES, sementara query=query menyimpan hasil parsing SELECT. Keyword SELECT tidak dikonsumsi terlebih dahulu karena pembacaannya sudah ditangani oleh _select(). 

Perbaikan ini juga mempertahankan dukungan INSERT ... VALUES yang sudah tersedia tanpa menduplikasi logika parsing SELECT.

**Test regresi.**
Test tambahan dibuat dalam tests/test_tambahan.py dengan nama:
test_insert_select_membentuk_ast_dan_crud

Input yang digunakan:
INSERT INTO arsip (id) SELECT id FROM pesanan;

Test memeriksa bahwa:
    1. Parsing selesai tanpa parse error dan menghasilkan satu statement.
    2. Statement tersebut merupakan node ast.Insert.
    3. Tabel tujuan adalah arsip dan kolom tujuannya adalah id.
    4. Field values kosong dan field query berisi node ast.Select.
    5. Query SELECT memiliki tabel sumber pesanan.
    6. Analisis menghasilkan operasi C untuk arsip dan R untuk pesanan.

Pengujian dilakukan bersama test bawaan:
python -m pytest tests/test_parser.py::test_insert_select tests/test_parser.py::test_insert_values tests/test_tambahan.py::test_insert_select_membentuk_ast_dan_crud -v

Hasil: 
3 passed in 0.18s
Sebelum perbaikan, test bawaan test_insert_select telah terbukti gagal dengan pesan bahwa INSERT SELECT belum didukung. Setelah perbaikan, test bawaan tersebut lulus.

**Peran AI.**
AI membantu menjelaskan tujuan TODO(T1), menyarankan pemanggilan _select() dari _insert(), memberikan contoh pembentukan node AST INSERT. AI juga membantu memperbaiki kesalahan saat penyusunan kode, terutama kesalahan ppercabangan if pada "if self._check_kw("SELECT"):" dan membantu validasi kode program untuk test TODO T1 dengan memberikan rekomendasi tambahan kode program untuk test ini.


## TODO T3: Dukungan Komentar Blok
Ditemukan oleh: SHAHNAZ SASKIA PUTRI, berdasarkan penanda TODO(T3) pada kode awal · Diperbaiki oleh: SHAHNAZ SASKIA PUTRI

**Gejala.** 
Berdasarkan SPESIFIKASI.md bagian 2.3, komentar blok /* ... */ dapat terdiri dari beberapa baris, boleh mengandung karakter *, tidak boleh bersarang, tidak menghasilkan token, dan harus menghasilkan LexError jika tidak ditutup.
Namun, pada kode awal, lexer langsung menghasilkan LexError: komentar blok belum didukung ketika menemukan /*. Akibatnya, test bawaan test_komentar_blok gagal dan file pemeliharaan.sql yang diawali komentar blok tidak dapat dianalisis karena terjadi LEX ERROR: Baris 1, kolom 1.

**Akar masalah.**
Lexer belum memiliki implementasi untuk membaca komentar blok. Ketika menemukan /*, proses pemindaian langsung dihentikan dengan LexError tanpa memeriksa isi maupun penutup komentar.
Masalah ini berkaitan dengan konsep Longer Lexemes pada Crafting Interpreters Bab 4 bagian 4.6. Scanner perlu terus membaca karakter hingga menemukan penanda akhir, kemudian mengabaikan isi komentar. Untuk komentar blok, penanda akhirnya adalah */, sehingga diperlukan lookahead /peek untuk memeriksa karakter berikutnya sebelum menentukan apakah komentar sudah berakhir.

**Perbaikan.**
Perubahan dilakukan pada fungsi _scan_token di file crud/lexer.py. Ketika menemukan karakter / yang diikuti *, lexer akan membaca isi komentar hingga menemukan pasangan */. Jika penutup ditemukan, komentar diabaikan tanpa menghasilkan token. Namun, jika input berakhir sebelum penutup ditemukan, lexer akan menghasilkan LexError("komentar blok tidak ditutup", line, col) dengan posisi awal komentar.
Alternatifnya menghapus komentar menggunakan pencarian teks sebelum proses pemindaian dimulai. Tapi cara tersebut tidak dipilih karena posisi baris dan kolom harus dihitung ulang secara manual. Dengan menggunakan _advance(), posisi baris dan kolom dapat diperbarui secara otomatis.

**Test regresi.**
Dua test tambahan dibuat pada tests/test_tambahan.py, yaitu test_komentar_blok_berisi_bintang untuk memastikan karakter ** tidak membuat komentar berhenti terlalu awal, dan test_komentar_blok_tidak_ditutup untuk memastikan komentar tanpa penutup menghasilkan LexError.

Sebelum perbaikan, test bawaan test_komentar_blok gagal dengan pesan LexError: komentar blok belum didukung. Setelah perbaikan, test tersebut berhasil dilewati. Jumlah test yang gagal pada seluruh suite juga berkurang dari 4 menjadi 3.

**Peran AI.**
AI membantu memberikan arahan mengenai proses pemindaian komentar blok serta menyarankan contoh kode ketika saya mengalami kesulitan dalam implementasinya. Selama proses tersebut, saya juga mempelajari perubahan yang disarankan agar memahami cara kerja perbaikannya. Setelah itu, saya menjalankan test bawaan, menambahkan test tambahan, dan menguji seluruh test suite untuk memastikan perbaikan berjalan dengan baik.


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


## Bug 4: Kutip Ganda di Dalam String Memecah Satu String Menjadi Dua Token

**Ditemukan oleh:** SHAHNAZ SASKIA PUTRI · **Diperbaiki oleh:** SHAHNAZ SASKIA PUTRI

**Gejala.**
Berdasarkan SPESIFIKASI.md bagian 2.4, dua kutip tunggal berurutan ('') di dalam string harus dianggap sebagai satu karakter kutip. Contoh 'O''Brien' seharusnya menghasilkan satu token STRING dengan nilai O'Brien.
Namun, pada kode lama lexer malah menghasilkan dua token STRING terpisah, yaitu O dan Brien. Test yang dibuat gagal dengan pesan assert 3 == 2 karena menghasilkan tiga token yaitu STRING O, STRING Brien, dan EOF. Akibatnya, parser menganggap query yang sebenarnya valid sebagai kesalahan sintaks.

**Reproduksi minimal.** SQL
```
SELECT id FROM pelanggan WHERE nama = 'O''Brien';
```
Hasil yang diharapkan adalah satu token STRING dengan nilai O'Brien pada bagian kondisi WHERE.

**Akar masalah.**
Masalah terdapat pada fungsi _string yang langsung mengakhiri pembacaan string ketika menemukan kutip tunggal pertama. Fungsi tersebut tidak memeriksa apakah kutip tersebut diikuti oleh kutip tunggal lainnya. Akibatnya, pasangan '' dianggap sebagai penutup string sekaligus pembuka string baru, sehingga satu string terpecah menjadi dua token.
Masalah ini berkaitan dengan konsep pemindaian string literal dalam Crafting Interpreters Bab 4 bagian 4.6.1. Scanner perlu menggunakan lookahead/peek untuk memeriksa karakter berikutnya sebelum menentukan apakah string tersebut sudah berakhir. 

**Perbaikan.**
Perbaikan dilakukan pada fungsi _string di file crud/lexer.py. Ketika menemukan kutip tunggal, fungsi akan memeriksa karakter berikutnya menggunakan self._peek(). Jika karakter berikutnya juga kutip tunggal, kutip dibaca sebagai bagian dari isi string dan proses pemindaian dilanjutkan. Jika tidak, kutip dianggap sebagai penutup string.
Alternatifnya menggabungkan dua token STRING melalui parser. Namun, cara ini tidak dipilih karena spesifikasi menetapkan bahwa '' harus ditangani sebagai satu token pada tahap lexer, juga penggabungan di parser berisiko mengganggu informasi baris dan kolom token.

**Test regresi.**
Test test_string_kutip_ganda_menjadi_satu_token ditambahkan pada tests/test_tambahan.py. Test ini memastikan bahwa 'O''Brien' menghasilkan dua token yaitu satu STRING dan EOF, dengan nilai token pertama O'Brien.
Sebelum perbaikan, test gagal dengan pesan assert 3 == 2. Setelah perbaikan, test berhasil dilewati dan jumlah test yang gagal pada seluruh suite berkurang dari 4 menjadi 3.

**Peran AI.**
AI membantu memberikan arahan dalam memperbaiki fungsi _string serta menyarankan bentuk test untuk menguji bug. Saya mengikuti arahan tersebut sambil mempelajari cara kerja dan memahami perubahan yang dilakukan.






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
