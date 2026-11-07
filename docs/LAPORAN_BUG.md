# LAPORAN BUG
## TODO T1: Melengkapi Dukungan INSERT ... SELECT
**Ditemukan oleh:** ALIA ARDANI dan SHAHNAZ SASKIA PUTRI, berdasarkan penanda TODO(T1) pada kode awal 

**Diperbaiki oleh:** ALIA ARDANI

**Gejala.** 
Program belum dapat memproses perintah INSERT yang mengambil data dari hasil query SELECT. Ketika menerima bentuk tersebut, parser menghasilkan pesan:
```
INSERT ... SELECT belum didukung, ditemukan 'SELECT'
```

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
```
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
```

Perubahan ini memungkinkan INSERT menggunakan query SELECT sebagai sumber data. 
Fungsi _select() digunakan kembali untuk membaca query dan membentuk AST, sedangkan table dan columns mempertahankan informasi tabel tujuan serta kolom yang akan diisi. Atribut values=[] menunjukkan bahwa data tidak berasal dari klausa VALUES, sementara query=query menyimpan hasil parsing SELECT. Keyword SELECT tidak dikonsumsi terlebih dahulu karena pembacaannya sudah ditangani oleh _select(). 

Perbaikan ini juga mempertahankan dukungan INSERT ... VALUES yang sudah tersedia tanpa menduplikasi logika parsing SELECT.

**Test regresi.**
Test tambahan dibuat dalam tests/test_tambahan.py dengan nama:
test_insert_select_membentuk_ast_dan_crud

Input yang digunakan:
```
INSERT INTO arsip (id) SELECT id FROM pesanan;
```

Test memeriksa bahwa:
    1. Parsing selesai tanpa parse error dan menghasilkan satu statement.
    2. Statement tersebut merupakan node ast.Insert.
    3. Tabel tujuan adalah arsip dan kolom tujuannya adalah id.
    4. Field values kosong dan field query berisi node ast.Select.
    5. Query SELECT memiliki tabel sumber pesanan.
    6. Analisis menghasilkan operasi C untuk arsip dan R untuk pesanan.

Pengujian dilakukan bersama test bawaan:
```
python -m pytest tests/test_parser.py::test_insert_select tests/test_parser.py::test_insert_values tests/test_tambahan.py::test_insert_select_membentuk_ast_dan_crud -v
```

Hasil: 
3 passed in 0.18s
Sebelum perbaikan, test bawaan test_insert_select telah terbukti gagal dengan pesan bahwa INSERT SELECT belum didukung. Setelah perbaikan, test bawaan tersebut lulus.

**Peran AI.**
AI membantu menjelaskan tujuan TODO(T1), menyarankan pemanggilan _select() dari _insert(), memberikan contoh pembentukan node AST INSERT. AI juga membantu memperbaiki kesalahan saat penyusunan kode, terutama kesalahan percabangan if pada "if self._check_kw("SELECT"):" dan membantu validasi kode program untuk test TODO T1 dengan memberikan rekomendasi tambahan kode program untuk test ini.


## TODO T2: MELENGKAPI RESOLUSI KOLOM TANPA QUALIFIER
**Ditemukan oleh:** ALIA ARDANI dan SHAHNAZ SASKIA PUTRI, berdasarkan penanda TODO(T2) pada kode awal · 

**Diperbaiki oleh:** ALIA ARDANI

**Gejala.** 
Resolver belum dapat menentukan sumber tabel untuk kolom yang ditulis tanpa qualifier. Qualifier adalah nama tabel atau alias yang diletakkan sebelum nama kolom, seperti p pada p.nama. Pada query SELECT nama FROM pelanggan WHERE aktif = 1;, kolom nama dan aktif tidak memiliki qualifier, tetapi query hanya memiliki satu sumber tabel, yaitu pelanggan. Kedua kolom tersebut seharusnya dapat diarahkan ke tabel pelanggan.

Pada kode awal, atribut resolved kedua kolom tetap bernilai None. Kondisi ini terlihat pada kegagalan test bawaan test_kolom_tanpa_qualifier_satu_tabel, yang mengharapkan hasil resolusi {"pelanggan"}, tetapi memperoleh {None}.

Berdasarkan SPESIFIKASI.md bagian 4.3, kolom tanpa qualifier harus diperiksa menggunakan sumber yang terdapat pada scope terdalam. Apabila terdapat tepat satu sumber, kolom diarahkan ke sumber tersebut. Apabila terdapat lebih dari satu sumber, resolver memberikan warning "ambigu tanpa skema". Apabila tidak terdapat sumber, resolver memberikan warning dan membiarkan kolom tidak teresolusi.

**Reproduksi minimal.**
```
SELECT nama FROM pelanggan;
```
Pada kode awal, query tersebut dapat diparsing, tetapi kolom nama tetap memiliki resolved = None setelah melewati resolver. Hasil yang diharapkan adalah resolved = "pelanggan" tanpa diagnostic, karena scope query hanya memiliki satu sumber tabel.

Masalah ini menyangkut informasi keterkaitan kolom dengan sumber tabelnya. Oleh karena itu, pemeriksaan dilakukan langsung terhadap hasil resolusi pada AST. CRUD matrix saja belum cukup untuk membuktikan bahwa fitur ini bekerja, karena tabel pelanggan masih dapat tercatat sebagai sumber pembacaan meskipun kolomnya belum teresolusi.

**Akar masalah.**
Fungsi _column() dalam crud/resolver.py sudah menangani kolom yang memiliki qualifier. Pada cabang tersebut, resolver memanggil _lookup() untuk mencari alias atau nama tabel, kemudian menggunakan _target_of() untuk mengisi atribut resolved.

Namun, ketika kolom tidak memiliki qualifier, fungsi melewati cabang tersebut dan mencapai bagian TODO(T2) yang hanya berisi pass. Pernyataan pass tidak melakukan pemrosesan apa pun. Akibatnya, resolver tidak menghitung sumber pada scope terdalam, tidak menentukan target kolom ketika sumbernya tunggal, dan tidak memberikan warning ketika sumbernya ambigu atau tidak tersedia.

Permasalahan ini berkaitan dengan konsep resolusi nama dan scope dalam Crafting Interpreters Bab 11. Parser membentuk struktur sintaks, sedangkan resolver menghubungkan penggunaan nama dengan lingkungan tempat nama tersebut digunakan. Dalam proyek ini, resolver menghubungkan referensi kolom dengan sumber tabel sesuai aturan spesifikasi.

Untuk kolom tanpa qualifier, pemeriksaan dibatasi pada scope terdalam. Resolver tidak boleh mengambil sumber dari scope luar hanya karena sumber pada scope terdalam tidak tersedia. Selain itu, resolver tidak memiliki informasi skema yang menjelaskan kolom milik setiap tabel. Karena itu, ketika terdapat beberapa sumber, resolver tidak dapat menentukan asal kolom hanya berdasarkan nama kolomnya.

**Perbaikan.**
Perubahan dilakukan pada bagian TODO(T2) dalam fungsi _column() di crud/resolver.py. Bagian pass diganti dengan pengambilan daftar sumber melalui self.scope.entries.values(). Daftar tersebut diambil dari scope terdalam karena, menurut spesifikasi, resolusi kolom tanpa qualifier hanya menggunakan sumber pada scope tersebut. Jika tidak ada scope aktif, daftar sumber dibuat kosong agar program tidak mencoba mengakses atribut entries dari None.

Atribut col.resolved kemudian diatur menjadi None sebagai kondisi awal sebelum sumber kolom ditentukan. Jika terdapat tepat satu entry, atribut tersebut diisi menggunakan _target_of(entries[0]) karena hanya ada satu sumber yang dapat dirujuk. Fungsi _target_of() digunakan kembali agar hasil resolusi mengikuti representasi target yang sudah tersedia dalam program, baik nama tabel maupun penanda subquery.

Jika terdapat lebih dari satu entry, resolver memberikan warning "ambigu tanpa skema" dan membiarkan col.resolved bernilai None. Hal ini dilakukan karena resolver tidak memiliki informasi skema untuk memastikan asal kolom sehingga tidak boleh memilih salah satu sumber secara sembarangan. Jika tidak terdapat entry, resolver memberikan warning "kolom tanpa tabel dalam scope" karena tidak ada sumber yang dapat digunakan untuk menentukan target kolom. Kedua warning menggunakan col.line agar lokasi masalah dapat diketahui dari nomor baris kolom yang diperiksa.

**Test regresi.**
Pengujian tambahan dibuat dalam tests/test_tambahan.py melalui fungsi
test_t2_kolom_tanpa_qualifier dan test_t2_kolom_tanpa_qualifier_scope_kosong.

Test pertama memeriksa dua kondisi menggunakan SQL yang diterima parser. Pada input SELECT nama FROM pelanggan;, kolom harus teresolusi ke pelanggan tanpa diagnostic. Pada input SELECT nama FROM pelanggan p, pesanan o;, kolom harus tetap tidak teresolusi dan menghasilkan satu diagnostic berlevel warning yang memuat pesan "ambigu tanpa skema". Pemeriksaan juga memastikan diagnostic mencatat nomor baris yang sesuai.

Pada penyusunan awal test tambahan, kondisi tanpa sumber diuji menggunakan SELECT nama;. Setelah dijalankan, input tersebut ternyata ditolak parser dengan pesan bahwa keyword FROM diharapkan. Kegagalan terjadi sebelum resolver dijalankan sehingga tidak dapat digunakan untuk menilai perilaku T2. Contoh pengujian tersebut kemudian diperbaiki tanpa mengubah grammar parser maupun test bawaan.

Pengujian scope kosong dipisahkan menjadi unit test resolver. Test memperoleh node kolom dari query valid, kemudian membuat scope luar yang memiliki sumber pelanggan dan scope terdalam yang kosong. Fungsi _column() dipanggil langsung untuk memastikan kolom tetap memiliki resolved = None serta menghasilkan warning. Susunan ini juga memeriksa bahwa resolver tidak mengambil tabel dari scope luar ketika scope terdalam kosong.

Kedua test tambahan dijalankan bersama seluruh test bawaan dalam tests/test_resolver.py menggunakan perintah berikut:
```
python -m pytest tests/test_resolver.py tests/test_tambahan.py::test_t2_kolom_tanpa_qualifier tests/test_tambahan.py::test_t2_kolom_tanpa_qualifier_scope_kosong -v
```

Hasil pengujian menunjukkan 6 passed in 0.23s. Bukti kegagalan sebelum perbaikan tersedia dari test bawaan test_kolom_tanpa_qualifier_satu_tabel, yang sebelumnya memperoleh {None}. Setelah perbaikan, test tersebut dan kedua test tambahan lulus. Hasil ini membuktikan perilaku pada kasus yang diuji, tetapi belum membuktikan bahwa seluruh aturan resolver telah terpenuhi.

**Peran AI.**
AI membantu saya memperbaiki kesalahan kode program fungsi _column() pada bagian TODO(T2) dan program pada test tambahan. Awalnya, saya hanya menambahkan test_t2_kolom_tanpa_qualifier, tetapi contoh input SELECT nama; yang disarankan AI ternyata tidak sesuai dengan grammar proyek karena parser mewajibkan FROM. AI kemudian menyarankan penambahan test_t2_kolom_tanpa_qualifier_scope_kosong untuk menguji kondisi scope kosong secara langsung pada resolver.


## TODO T3: DUKUNGAN KOMENTAR BLOK
**Ditemukan oleh:** SHAHNAZ SASKIA PUTRI dan ALIA ARDANI, berdasarkan penanda TODO(T3) pada kode awal · 

**Diperbaiki oleh:** SHAHNAZ SASKIA PUTRI

**Gejala.** 
Berdasarkan SPESIFIKASI.md bagian 2.3, komentar blok /* ... */ dapat terdiri dari beberapa baris, boleh mengandung karakter *, tidak boleh bersarang, tidak menghasilkan token, dan harus menghasilkan LexError jika tidak ditutup.
Namun, pada kode awal, lexer langsung menghasilkan LexError: komentar blok belum didukung ketika menemukan /*. Akibatnya, test bawaan test_komentar_blok gagal dan file pemeliharaan.sql yang diawali komentar blok tidak dapat dianalisis karena terjadi LEX ERROR: Baris 1, kolom 1.

**Reproduksi minimal.**
```
SELECT id FROM pelanggan;
```
Pada kode awal, lexer menghasilkan LexError karena komentar blok belum didukung. Hasil yang diharapkan adalah komentar dilewati dan statement SELECT dapat diproses

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


## BUG 1: PARSER MEMBUANG STATEMENT VALID SETELAH KESALAHAN SINTAKS
**Ditemukan oleh:** ALIA ARDANI dan SHAHNAZ SASKIA PUTRI ·

**Diperbaiki oleh:** ALIA ARDANI

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
```
def _synchronize(self) -> None:
    # Panic-mode recovery: lewati statement rusak sampai termasuk ';'.
    while not self._at_end():
        token = self._advance()
        if token.type == T.SEMICOLON:
            return
```

Alternatif yang dipertimbangkan adalah menghentikan recovery ketika menemukan keyword awal statement, seperti SELECT. Alternatif ini tidak dipilih karena SELECT juga dapat muncul dalam subquery pada statement yang sedang dibuang. Selain itu, spesifikasi secara tegas menetapkan titik koma sebagai batas recovery.

**Test regresi.**
Test ditambahkan pada tests/test_tambahan.py dengan nama: test_recovery_memproses_statement_setelah_error

Test menggunakan satu SELECT valid, satu SELECT rusak, kemudian UPDATE dan DELETE valid. Pemeriksaan mencakup tidak adanya lexical error, tepat satu parse error pada baris yang benar, kelanjutan pemrosesan ketiga statement valid, serta kesesuaian CRUD matrix.

Perintah pengujian:
```
python -m pytest tests/test_tambahan.py::test_recovery_memproses_statement_setelah_error -v
```
Sebelum perbaikan, test FAILED karena hasil hanya memuat statement SELECT pertama. Setelah perbaikan, test yang sama PASSED tanpa mengubah isi test.

**Peran AI.**
AI membantu saya untuk memvalidasi kalau temuan bug dan perbaikan yang akan temukan itu tepat dan sesuai dengan gejala pada bug ini, AI juga membantu saya melakukan dalam memperbaiki serta memberikan tambahan kode program dalam memperbaiki fungsi _synchronize() dan test_recovery_memproses_statement_setelah_error .


## BUG 2: KEYWORD HURUF KECIL TIDAK DIKENALI SEBAGAI KEYWORD
**Ditemukan oleh:** SHAHNAZ SASKIA PUTRI dan ALIA ARDANI ·

**Diperbaiki oleh:** SHAHNAZ SASKIA PUTRI

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


## BUG 3: OPERATOR TIDAK SAMA DENGAN (<>) DIPECAH MENJADI DUA TOKEN
**Ditemukan oleh:** ALIA ARDANI dan SHAHNAZ SASKIA PUTRI ·

**Diperbaiki oleh:** ALIA ARDANI

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
```
SELECT id FROM t WHERE id <> 10;
```

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
```
if ch == "<":
    op = "<=" if self._match("=") else "<"
    self._add(TokenType.OP, op, line, col)
    return
```

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
```
if ch == "<":
    if self._match("="):
        op = "<="
    elif self._match(">"):
        op = "<>"
    else:
        op = "<"

    self._add(TokenType.OP, op, line, col)
    return
```

Perbaikan dilakukan pada bagian if ch == "<" dengan menambahkan pemeriksaan self._match(">") untuk mengenali operator <>. Fungsi _match() memeriksa sekaligus mengonsumsi karakter berikutnya apabila sesuai, sehingga < dan > dikenali sebagai satu token OP, bukan dua token terpisah. Sementara itu, percabangan if, elif, dan else tetap mempertahankan dukungan operator <= dan <. Pemanggilan _add() digunakan untuk menyimpan operator yang dikenali sebagai satu token, sedangkan return mengakhiri pemindaian token tersebut. Perubahan dilakukan pada lexer karena pengenalan operator merupakan tanggung jawab lexer.

**Test regresi.**
Test ditambahkan pada tests/test_tambahan.py dengan nama: test_operator_tidak_sama_dipindai_sebagai_satu_token
Test memeriksa jenis, nilai, urutan, dan jumlah token. Pemeriksaan seluruh daftar token diperlukan untuk memastikan bahwa <> benar-benar menjadi satu token dan tidak meninggalkan token > tambahan.

Sebelum perbaikan, test menghasilkan FAILED dengan perbedaan utama:
At index 1 diff: ... '<' ... != ... '<>'

Setelah perbaikan lengkap diterapkan, test yang sama menghasilkan PASSED tanpa mengubah hasil yang diharapkan.
Test bawaan test_operator_multi_karakter juga dijalankan untuk memeriksa bahwa operator <=, >=, dan != tetap dikenali dengan benar.

Perintah pengujian:
```
python -m pytest tests/test_tambahan.py::test_operator_tidak_sama_dipindai_sebagai_satu_token tests/test_lexer.py::test_operator_multi_karakter -v
```

Hasil pengujian terakhir:
2 passed in 0.13s
Dalam proses penerapan perbaikan, pemanggilan _add() dan return sempat belum dimasukkan sehingga muncul LexError untuk karakter <. Setelah kedua baris tersebut dilengkapi dengan indentasi yang benar, kedua test lulus. Kesalahan sementara ini merupakan kekeliruan saat menerapkan perbaikan, bukan akar masalah pada kode awal.

Hasil tersebut membuktikan bahwa kasus <> yang diuji sudah benar dan operator pada test pembanding tetap bekerja. Pengujian ini belum membuktikan bahwa seluruh lexer atau seluruh pipeline bebas dari bug.

**Peran AI.**
AI membantu menghubungkan pesan parse error pada laporan_penjualan.sql dengan kesalahan pembentukan token operator <>. AI juga membantu menyusun test regresi, menjelaskan konsep lookahead dan maximal munch, serta menyarankan perubahan pada fungsi _scan_token().


## BUG 4: KUTIP GANDA DI DALAM STRING MEMECAH SATU STRING MENJADI DUA TOKEN 
**Ditemukan oleh:** SHAHNAZ SASKIA PUTRI dan ALIA ARDANI ·

**Diperbaiki oleh:** SHAHNAZ SASKIA PUTRI

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


## BUG 5: TABEL DI SUBQUERY PADA UPDATE SALAH DITANDAI U
**Ditemukan oleh:** SHAHNAZ SASKIA PUTRI dan ALIA ARDANI ·

**Diperbaiki oleh:** SHAHNAZ SASKIA PUTRI dan ALIA ARDANI

**Gejala.**
Menurut SPESIFIKASI.md bagian 5, tabel yang dibaca lewat subquery selalu berstatus R, apa pun jenis statement luarnya, dan hanya tabel target UPDATE yang berstatus U. Pada kode lama, tabel di dalam subquery pada klausa `SET` maupun `WHERE` ikut ditandai U. Test yang saya tulis gagal karena `pesanan` keluar `U`, padahal seharusnya `R`. Test bawaan `test_matrix_laporan_penjualan` juga gagal karena alasan yang sama (`pesanan` keluar `RUD`, seharusnya `RD`).

**Reproduksi minimal.** SQL
```
UPDATE pelanggan SET aktif = 0 WHERE id IN (SELECT pelanggan_id FROM pesanan);
```
Hasil yang diharapkan adalah `pelanggan` bernilai U dan `pesanan` bernilai R. Kode lama menghasilkan `pelanggan` U dan `pesanan` U.

**Akar masalah.**
Pada cabang UPDATE di `analyze_statement`, kode lama menelusuri ekspresi `SET` dan `WHERE` dengan operasi `"U"`, sehingga setiap tabel yang ditemukan di dalam subquery pada ekspresi itu ikut menerima operasi U. Operasi statement luar diturunkan begitu saja ke tabel di dalam subquery, padahal operasi sebuah tabel ditentukan oleh perannya, yaitu target yang diubah atau sumber yang dibaca.

Masalah ini berkaitan dengan penelusuran AST pada Crafting Interpreters Bab 5 (Representing Code). Analyzer bekerja di atas pohon, dan keputusan tiap node bergantung pada posisinya di pohon, bukan pada jenis statement paling luar.

**Perbaikan.**
Perubahan dilakukan pada `crud/analyzer.py`, di cabang UPDATE pada `analyze_statement`. Argumen operasi pada dua pemanggilan `_collect`, yaitu untuk ekspresi `SET` dan untuk `WHERE`, diubah dari `"U"` menjadi `"R"`. Baris yang menandai tabel target UPDATE sebagai `U` tidak diubah.

Alternatif yang dipertimbangkan adalah membiarkan penelusuran seperti semula, lalu membuang status U dari semua tabel selain target setelah analisis selesai. Alternatif ini tidak dipilih karena hanya menambal hasil, sedangkan penyebabnya adalah operasi yang salah diteruskan saat penelusuran.

**Test regresi.**
Test test_subquery_di_update_hanya_dibaca ditambahkan di tests/test_tambahan.py. Sebelum perbaikan test ini gagal karena `pesanan` bernilai `U`, dan sesudah perbaikan lulus. Test bawaan `test_matrix_laporan_penjualan` yang sebelumnya gagal juga ikut lulus. 

**Peran AI.**
AI menunjukkan lokasi kode yang perlu diperiksa dan mengusulkan perubahan `"U"` menjadi `"R"` serta contoh isi test. Saya menulis test, menjalankannya sampai terlihat gagal, mengubah dua baris di `analyzer.py`, lalu memverifikasi bahwa test tersebut lulus dan seluruh suite tidak memiliki test baru yang rusak.


## BUG 6: ALIAS DELETE BOCOR KE STATEMENT BERIKUTNYA
**Ditemukan oleh:** SHAHNAZ SASKIA PUTRI dan ALIA ARDANI ·

**Diperbaiki oleh:** SHAHNAZ SASKIA PUTRI

**Gejala.**
Berdasarkan aturan scope pada SPESIFIKASI.md bagian 4, setiap statement DELETE memiliki scope sendiri. Alias yang dideklarasikan pada DELETE hanya berlaku dalam lingkup statement tersebut dan tidak boleh digunakan oleh statement berikutnya yang berdiri sendiri.

Pada kode lama, alias s yang dideklarasikan melalui DELETE FROM sesi s masih dapat ditemukan ketika resolver memproses SELECT setelahnya. Akibatnya, penggunaan s.id pada SELECT tidak menghasilkan diagnostic alias tidak terdefinisi, meskipun SELECT tersebut hanya mendeklarasikan sumber pengguna dengan alias u.

Perilaku ini menyebabkan referensi kolom pada statement berikutnya dapat diarahkan ke tabel dari statement sebelumnya. Bug tetap perlu diperbaiki walaupun CRUD matrix tidak berubah, karena hasil resolusi nama dan diagnostic tidak sesuai dengan aturan scope.

**Reproduksi minimal.** SQL
```
DELETE FROM sesi s;
SELECT s.id FROM pengguna u;
```
Pada kode lama, scope DELETE masih tersimpan ketika SELECT diproses. Resolver kemudian menemukan alias s dari DELETE dan mengarahkan s.id pada SELECT ke tabel sesi.

Hasil yang diharapkan adalah diagnostic berlevel error pada baris 2 dengan pesan:
'alias 's' tidak terdefinisi'
Diagnostic tersebut diperlukan karena alias s hanya dideklarasikan dalam DELETE. Pada SELECT berikutnya, alias yang tersedia adalah u.

**Akar masalah.**
Masalah terdapat pada fungsi _delete() dalam crud/resolver.py. Kode lama membuka scope baru melalui _push(), mendaftarkan tabel dan alias DELETE melalui _declare_source(), kemudian memproses kondisi WHERE melalui _expr(). Namun, setelah pemrosesan selesai, fungsi tidak memanggil _pop() untuk keluar dari scope DELETE.

Akibatnya, self.scope masih menunjuk pada scope DELETE. Ketika SELECT berikutnya memanggil _push(), scope baru SELECT dibuat dengan scope DELETE yang tertinggal sebagai parent. Hubungan tersebut membuat dua statement yang sebenarnya terpisah diperlakukan seolah-olah memiliki hubungan scope bertingkat.

Saat resolver mencari alias s melalui _lookup(), pencarian dapat mencapai scope DELETE yang masih berada dalam rantai scope. Alias tersebut kemudian dianggap tersedia, padahal masa berlakunya seharusnya sudah berakhir.

Masalah ini berkaitan dengan konsep pengelolaan scope pada Crafting Interpreters Bab 11. Resolver perlu membuka scope saat memasuki suatu lingkup dan menutupnya setelah pemrosesan lingkup selesai. Ketidakseimbangan antara pembukaan dan penutupan scope menyebabkan deklarasi dari lingkup sebelumnya memengaruhi resolusi nama pada lingkup berikutnya.

**Perbaikan.**
Perubahan dilakukan pada fungsi _delete() dalam crud/resolver.py dengan menambahkan self._pop() setelah pemanggilan self._expr(dele.where). Fungsi setelah perbaikan menjadi:
```
def _delete(self, dele: ast.Delete) -> None:
    self._push()
    self._declare_source(dele.table)
    self._expr(dele.where)
    self._pop()
```
Pemanggilan _pop() ditempatkan setelah pemrosesan WHERE agar tabel dan alias DELETE tetap tersedia ketika kondisi DELETE diperiksa. Setelah pemeriksaan selesai, _pop() mengembalikan scope aktif ke parent-nya sehingga scope DELETE tidak menjadi lingkungan bagi statement berikutnya.

Perbaikan menggunakan fungsi pengelolaan scope yang sudah tersedia dan mengikuti pola yang telah digunakan oleh _select() serta _update(). Perubahan tidak memerlukan penambahan struktur AST maupun perubahan API publik.

Alternatif perbaikan adalah mengatur self.scope langsung menjadi None setelah DELETE selesai. Cara tersebut tidak digunakan karena _pop() lebih tepat dalam mengembalikan keadaan scope sebelumnya. Mengatur scope menjadi None secara langsung mengabaikan hubungan parent yang sudah dikelola oleh struktur Scope.

**Test regresi.**
Test test_alias_delete_tidak_bocor_ke_statement_berikutnya ditambahkan dalam tests/test_tambahan.py dengan input:
```
DELETE FROM sesi s WHERE s.id = 1;
SELECT s.id FROM pengguna u;
```
Test test_alias_delete_tidak_bocor_ke_statement_berikutnya memeriksa bahwa input tidak menghasilkan kesalahan lexer maupun parser, tetapi menghasilkan tepat satu diagnostic berlevel error dengan pesan alias 's' tidak terdefinisi pada baris 2. Dalam pemeriksaan ulang berbantuan AI, test terbaru dijalankan pada salinan kode sebelum perbaikan Bug 6 dan gagal karena daftar diagnostic masih kosong. Pada kode setelah perbaikan, test tersebut lulus. Hasil ini menunjukkan bahwa penambahan _pop() mencegah alias DELETE terbawa ke statement berikutnya.

Pengujian dilakukan menggunakan perintah:
```
python -m pytest tests/test_tambahan.py::test_alias_delete_tidak_bocor_ke_statement_berikutnya -v
```

Hasil pengujian setelah perbaikan adalah: 1 passed in 0.20s
Hasil tersebut menunjukkan bahwa test regresi Bug 6 lulus pada kode yang sudah memiliki _pop()

**Peran AI.**
AI turut membantu menjelaskan kesalahan lokasi folder ketika pytest belum menemukan file test, menyarankan penguatan pemeriksaan diagnostic, serta menyusun draf laporan berdasarkan kode dan hasil pengujian yang tersedia.


## BUG 7: ALIAS SCOPE LUAR MENGALAHKAN ALIAS SCOPE DALAM
**Ditemukan oleh:** ALIA ARDANI dan SHAHNAZ SASKIA PUTRI ·

**Diperbaiki oleh:** ALIA ARDANI

**Gejala.**
Berdasarkan aturan scope pada SPESIFIKASI.md bagian 4, pencarian alias harus dimulai dari scope terdalam menuju scope terluar. Jika alias yang sama digunakan pada query luar dan subquery, alias dalam harus menutupi alias luar. Aturan ini disebut shadowing.

Pada kode lama, resolver justru memilih alias dari query luar terlebih dahulu. Ketika query luar menggunakan alias x untuk tabel pelanggan dan subquery menggunakan alias x untuk tabel pesanan, kolom x.id pada subquery salah diarahkan ke pelanggan. Seharusnya, kolom tersebut diarahkan ke pesanan.

**Reproduksi minimal.** SQL
```
SELECT x.id FROM pelanggan x
WHERE EXISTS (SELECT x.id FROM pesanan x);
```
Pada kode lama, x.id pada query luar maupun subquery sama-sama teresolusi ke pelanggan. Hasil yang diharapkan adalah x.id pada query luar teresolusi ke pelanggan, sedangkan x.id pada subquery teresolusi ke pesanan.

Query ini valid dan tidak seharusnya menghasilkan diagnostic. Penggunaan alias yang sama diperbolehkan karena kedua alias dideklarasikan dalam scope yang berbeda.

**Akar masalah.**
Masalah terdapat pada fungsi _lookup() dalam crud/resolver.py. Fungsi tersebut membangun daftar chain mulai dari scope yang sedang aktif, kemudian mengikuti parent hingga scope terluar. Dengan demikian, urutan chain sebenarnya sudah sesuai untuk pencarian alias, yaitu dari dalam ke luar.

Namun, kode lama menelusuri daftar tersebut menggunakan:
```
for scope in reversed(chain):
```
Penggunaan reversed() membalik urutan pencarian menjadi dari luar ke dalam. Karena fungsi langsung mengembalikan entry pertama yang cocok, alias x dari tabel pelanggan ditemukan dan dikembalikan sebelum alias x dari tabel pesanan diperiksa.

Masalah ini berkaitan dengan konsep resolusi nama dan shadowing dalam Crafting Interpreters Bab 11. Nama harus dihubungkan dengan deklarasi yang paling dekat dengan tempat penggunaannya. Pencarian dari scope terluar melanggar aturan tersebut karena deklarasi luar mengalahkan deklarasi dalam.

**Perbaikan.**
Perubahan dilakukan pada fungsi _lookup() dalam crud/resolver.py dengan mengganti menjadi:
```
for scope in chain:
```
Perubahan ini membuat resolver mengikuti urutan chain yang sudah dimulai dari scope terdalam. Jika alias ditemukan pada scope tersebut, resolver langsung mengembalikan entry-nya. Jika tidak ditemukan, pencarian dilanjutkan ke scope luar.

Pencarian ke scope luar tetap dipertahankan karena subquery dapat menggunakan alias dari query luar apabila alias tersebut tidak dideklarasikan di dalam subquery. Oleh karena itu, alternatif membatasi pencarian hanya pada scope terdalam tidak dipilih karena akan menghalangi resolusi referensi berkorelasi.

Perbaikan hanya mengubah urutan pencarian alias tanpa mengubah struktur AST maupun API publik.

**Test regresi.**
Test test_alias_dalam_menutupi_alias_luar ditambahkan dalam tests/test_tambahan.py. Test menggunakan query luar dan subquery yang sama-sama memakai alias x, tetapi merujuk pada tabel berbeda.

Test memeriksa bahwa parsing selesai tanpa kesalahan dan resolver tidak menghasilkan diagnostic. Selanjutnya, test memeriksa atribut resolved pada kedua kolom untuk memastikan kolom luar diarahkan ke pelanggan dan kolom dalam diarahkan ke pesanan. Pemeriksaan dilakukan pada AST karena CRUD matrix saja belum dapat membuktikan ketepatan resolusi alias.

Sebelum perbaikan, test dijalankan menggunakan:
```
python -m pytest tests/test_tambahan.py::test_alias_dalam_menutupi_alias_luar -v
```
Test menghasilkan FAILED pada pemeriksaan kolom dalam dengan pesan: AssertionError: assert 'pelanggan' == 'pesanan'

Setelah perbaikan, test yang sama dijalankan bersama seluruh test resolver bawaan:
```
python -m pytest tests/test_resolver.py tests/test_tambahan.py::test_alias_dalam_menutupi_alias_luar -v
```
Hasil pengujian adalah: 5 passed in 0.18s
Hasil tersebut menunjukkan bahwa test regresi yang sebelumnya gagal sudah lulus tanpa mengubah hasil yang diharapkan. Empat test resolver bawaan juga tetap lulus setelah urutan pencarian diperbaiki.

**Peran AI.**
AI membantu memvlidasi kesalahan penggunaan reversed(chain) pada fungsi _lookup(), menjelaskan pengaruhnya terhadap shadowing, serta memberikan gambaran dan membantu perbaikan kode pada test_alias_dalam_menutupi_alias_luar . 


## BUG 8: PARSER MENYAMAKAN PRESEDENSI AND DAN OR
**Ditemukan oleh:** ALIA ARDANI dan SHAHNAZ SASKIA PUTRI ·

**Diperbaiki oleh:** ALIA ARDANI

**Gejala.**
Menurut SPESIFIKASI.md bagian 3.1, operator AND memiliki presedensi lebih tinggi daripada OR. Namun, parser lama memproses keduanya pada tingkat yang sama. Query berhasil diparsing tanpa error, tetapi pengelompokan kondisi pada AST salah.

**Reproduksi minimal.** 
```
SELECT id FROM t WHERE a = 1 OR b = 2 AND c = 3;
```
AST kode lama menggambarkan (a = 1 OR b = 2) AND c = 3. Hasil yang diharapkan adalah a = 1 OR (b = 2 AND c = 3), sehingga akar ekspresinya berupa OR dan cabang kanannya berupa AND.

**Akar masalah.**
Fungsi _logical() dalam crud/parser.py memproses AND dan OR dalam satu perulangan:
```
while self._check_kw("AND", "OR"):
    op = self._advance().value
    left = ast.BinaryOp(left, op, self._not())
```
Setiap operasi baru menggunakan hasil sebelumnya sebagai operand kiri. Akibatnya, ekspresi dikelompokkan dari kiri ke kanan tanpa membedakan prioritas kedua operator.

Masalah ini berkaitan dengan Crafting Interpreters Bab 6 bagian 6.1, yang menjelaskan pemisahan aturan grammar untuk setiap tingkat presedensi. Bagian 6.2 menjelaskan bahwa setiap aturan tersebut diterjemahkan menjadi fungsi dalam parser recursive descent. Konsep ini digunakan untuk menerapkan urutan presedensi yang ditetapkan spesifikasi proyek.

**Perbaikan.**
Perubahan dilakukan dalam crud/parser.py. Fungsi _logical() diubah agar hanya menangani OR, dan fungsi _and() ditambahkan untuk menangani AND.
```
def _logical(self):
    # OR memiliki presedensi lebih rendah daripada AND.
    left = self._and()
    while self._check_kw("OR"):
        op = self._advance().value
        left = ast.BinaryOp(left, op, self._and())
    return left

def _and(self):
    # AND memiliki presedensi lebih rendah daripada NOT.
    left = self._not()
    while self._check_kw("AND"):
        op = self._advance().value
        left = ast.BinaryOp(left, op, self._not())
    return left
```
Fungsi _expr() tetap memanggil _logical(). Pemisahan ini membuat operasi AND terbentuk sebagai operand OR, sehingga pengelompokan AST sesuai dengan spesifikasi.

Alternatifnya adalah menggunakan satu fungsi dengan tabel prioritas operator. Cara tersebut tidak dipilih karena pemisahan fungsi cukup untuk memperbaiki masalah dan sesuai dengan pola recursive descent pada Bab 6.

**Test regresi.**
Test test_and_lebih_kuat_daripada_or ditambahkan dalam tests/test_tambahan.py. Test memeriksa parsing tanpa error, akar ekspresi berupa OR, cabang kiri berupa perbandingan kolom a, dan cabang kanan berupa AND yang menghubungkan perbandingan kolom b dan c.

Perintah pengujian:
```
python -m pytest tests/test_tambahan.py::test_and_lebih_kuat_daripada_or -v
```
Sebelum perbaikan, test menghasilkan 1 failed in 0.62s karena akar ekspresi berupa AND, bukan OR. Setelah perbaikan, test yang sama menghasilkan 1 passed in 0.13s tanpa mengubah isi test.

**Peran AI.**
AI membantu dalam menemukan penyebab keselahan logika pada fungsi sebelumnya, membantu dalam memperbaiki test pemeriksaan AST, dan menyarankan pemisahan fungsi _logical() dan _and(). AI juga membantu saya dalam keslahan logical ini pada konsep teori.


## BUG 9: PARSER MENOLAK LEFT OUTER JOIN
**Ditemukan oleh:** ALIA ARDANI dan SHAHNAZ SASKIA PUTRI ·

**Diperbaiki oleh:** ALIA ARDANI

**Gejala.**
Menurut grammar pada SPESIFIKASI.md bagian 3, kata OUTER bersifat opsional setelah LEFT. Artinya, bentuk LEFT JOIN maupun LEFT OUTER JOIN seharusnya diterima oleh parser.

Namun, parser lama menolak query yang menggunakan LEFT OUTER JOIN. Program menghasilkan parse error ketika menemukan keyword OUTER, sehingga statement SELECT tersebut tidak berhasil diparsing. Hasil yang diharapkan adalah tidak ada parse error dan terbentuk satu statement SELECT dengan jenis join "LEFT".

**Reproduksi minimal.** 
```
SELECT p.id FROM pelanggan p LEFT OUTER JOIN pesanan s ON p.id = s.id;
```
Pada kode lama, query tersebut menghasilkan pesan: Baris 1, kolom 35: diharapkan JOIN, ditemukan 'OUTER'
Kesalahan muncul karena parser langsung mengharapkan JOIN setelah membaca LEFT, padahal terdapat keyword opsional OUTER di antaranya.

**Akar masalah.**
Masalah terdapat pada fungsi _join() dalam crud/parser.py. Kode lama mengenali LEFT dan menetapkan jenis join, tetapi belum memeriksa kemungkinan adanya OUTER:
```
elif self._match_kw("LEFT"):
    kind = "LEFT"
self._expect_kw("JOIN")
```
Setelah LEFT dikonsumsi, token aktif masih berupa OUTER. Pemanggilan _expect_kw("JOIN") kemudian gagal karena token tersebut tidak sesuai dengan keyword yang diharapkan. Dengan demikian, fungsi parser belum menerapkan seluruh bentuk yang diperbolehkan oleh grammar.

Masalah ini berkaitan dengan Crafting Interpreters Bab 6 bagian 6.2, yang menjelaskan penerjemahan aturan grammar menjadi fungsi parser recursive descent. Unsur opsional dalam grammar diterjemahkan menjadi pemeriksaan bersyarat. Dalam proyek ini, parser perlu memeriksa dan mengonsumsi OUTER jika ada, kemudian tetap mewajibkan JOIN.

**Perbaikan.**
Perubahan dilakukan pada fungsi _join() dalam crud/parser.py dengan menambahkan self._match_kw("OUTER") setelah penetapan kind = "LEFT":
```
def _join(self) -> ast.Join:
    tok = self._peek()
    kind = "INNER"

    if self._match_kw("INNER"):
        kind = "INNER"
    elif self._match_kw("LEFT"):
        kind = "LEFT"
        # OUTER boleh ada atau tidak setelah LEFT.
        self._match_kw("OUTER")

    self._expect_kw("JOIN")
    source = self._table_ref()
    self._expect_kw("ON")
    condition = self._expr()
    return ast.Join(kind, source, condition, line=tok.line)
```
Fungsi _match_kw("OUTER") mengonsumsi keyword tersebut jika tersedia. Jika tidak tersedia, parser melanjutkan pemeriksaan JOIN tanpa menghasilkan error. Dengan demikian, kedua bentuk dapat diterima dan tetap direpresentasikan sebagai jenis join "LEFT" pada AST.

Pemeriksaan ditempatkan di dalam cabang LEFT agar penerimaan OUTER mengikuti posisi yang ditetapkan grammar. Perubahan ini tidak memerlukan perubahan struktur AST maupun API publik.

Alternatif menggunakan _expect_kw("OUTER") tidak dipilih karena akan menjadikan OUTER wajib. Akibatnya, bentuk LEFT JOIN yang juga valid justru akan ditolak.

**Test regresi.**
Test test_left_outer_join_diterima ditambahkan dalam tests/test_tambahan.py. Test menggunakan query pada reproduksi minimal dan memeriksa bahwa script.errors kosong serta jumlah statement yang terbentuk adalah satu.

Pada percobaan awal, penulisan input test kekurangan spasi sehingga alias p tergabung dengan keyword LEFT menjadi pLEFT. Input test diperbaiki terlebih dahulu dengan menuliskan SQL dalam satu baris. Kegagalan dari input yang salah tersebut tidak digunakan sebagai bukti Bug 9.

Setelah input benar, test dijalankan sebelum perubahan parser menggunakan:
```
python -m pytest tests/test_tambahan.py::test_left_outer_join_diterima -v
```
Hasilnya 1 failed in 0.55s, dengan pesan bahwa parser mengharapkan JOIN tetapi menemukan OUTER. Setelah fungsi _join() diperbaiki, test yang sama menghasilkan 1 passed in 0.11s tanpa mengubah lagi input maupun pemeriksaan test.

**Peran AI.**
AAI membantu saya dalam menemukan bug ini, membantu memperbaiki kode program untuk perbaikan fungsi dan kede program untuk test, AI juga menunjukkan bagian fungsi _join() yang menyebabkan OUTER ditolak dan menyarankan penggunaan _match_kw("OUTER")


## BUG 10: LEXER MENOLAK PARAMETER BERAWALAN ANGKA
**Ditemukan oleh:** ALIA ARDANI dan SHAHNAZ SASKIA PUTRI ·

**Diperbaiki oleh:** ALIA ARDANI

**Gejala.**
SPESIFIKASI.md bagian 2.6 menyebutkan bahwa parameter berbentuk ? atau :nama, dengan nama berisi huruf, angka, dan garis bawah. Pada pengerjaan ini, aturan tersebut ditafsirkan memperbolehkan angka sebagai karakter pertama karena tidak ada pembatasan khusus yang disebutkan.

Namun, lexer lama menolak input :1 dan menghasilkan LexError. Berdasarkan interpretasi tersebut, hasil yang diharapkan adalah satu token PARAM bernilai :1, diikuti token EOF.

**Reproduksi minimal.** 
```
SELECT :1 FROM t;
```
Bagian yang memicu masalah adalah parameter :1. Pengujian langsung menggunakan tokenize(":1") pada kode lama menghasilkan: Baris 1, kolom 1: parameter ':' harus diikuti nama
Posisi tersebut berasal dari pengujian parameter secara terpisah, bukan dari SQL lengkap di atas.

**Akar masalah.**
Masalah terdapat pada fungsi _scan_token() dalam crud/lexer.py. Setelah membaca tanda :, kode lama memeriksa karakter berikutnya menggunakan:
```
if self._peek().isalpha() or self._peek() == "_":
```
Pemanggilan isalpha() hanya menerima huruf, sehingga angka 1 langsung ditolak. Sementara itu, perulangan pembacaan karakter berikutnya sudah menggunakan isalnum(), yang menerima huruf maupun angka. Akibatnya, angka diperbolehkan di tengah nama parameter, tetapi tidak pada awalnya.

Hal ini berkaitan dengan konsep pengenalan token dalam Crafting Interpreters Bab 4. Pemeriksaan karakter pada lexer harus mengikuti aturan leksikal bahasa yang digunakan. 

**Perbaikan.**
Perubahan dilakukan pada cabang if ch == ":" dalam fungsi _scan_token() di crud/lexer.py, dengan mengganti isalpha() menjadi isalnum():
```
if ch == ":":
    # Nama parameter berisi huruf, angka, atau garis bawah.
    if self._peek().isalnum() or self._peek() == "_":
        start = self.pos
        while self._peek().isalnum() or self._peek() == "_":
            self._advance()
        self._add(
            TokenType.PARAM,
            ":" + self.src[start:self.pos],
            line,
            col,
        )
        return
    raise LexError("parameter ':' harus diikuti nama", line, col)
```
Perubahan ini memungkinkan angka diterima pada awal nama parameter. Pemeriksaan tetap memastikan ada karakter nama setelah :, sehingga tanda : tanpa nama masih ditolak. Aturan identifier biasa dan API publik tidak diubah.

Alternatif yang dipertimbangkan adalah menghapus pemeriksaan karakter pertama. Cara tersebut tidak dipilih karena dapat membuat : tanpa nama diterima sebagai token parameter. Penggunaan isalnum() mempertahankan validasi sekaligus menerima angka.

**Test regresi.**
Test test_parameter_berawalan_angka ditambahkan dalam tests/test_tambahan.py. Test menggunakan tokenize(":1") dan memeriksa jenis token PARAM, nilai :1, posisi baris 1 kolom 1, serta keberadaan token EOF setelahnya.

Perintah pengujian:
```
python -m pytest tests/test_tambahan.py::test_parameter_berawalan_angka -v
```
Sebelum perbaikan, test menghasilkan 1 failed in 0.66s karena lexer mengeluarkan LexError. Setelah perbaikan, test yang sama menghasilkan 1 passed in 0.09s tanpa mengubah isi test.

**Peran AI.**
AI membantu menemukan pembatasan karakter pertama parameter, memberikan gambaran dalam menyusun test regresi, dan menyarankan penggantian isalpha() menjadi isalnum(). AI juga menjelaskan bahwa spesifikasi belum menetapkan aturan karakter pertama secara tegas.


## BUG 11: DIAGNOSTIK RESOLVER TERBAWA KE SCRIPT BERIKUTNYA
**Ditemukan oleh:** ALIA ARDANI dan SHAHNAZ SASKIA PUTRI ·

**Diperbaiki oleh:** ALIA ARDANI dan SHAHNAZ SASKIA PUTRI

**Gejala.**
Ketika satu objek Resolver digunakan untuk memproses dua script secara berurutan, diagnostik dari script pertama ikut muncul pada hasil script kedua. Akibatnya, script kedua yang valid tetap dilaporkan memiliki error.

SPESIFIKASI.md bagian 7 menetapkan API resolve_script(script) yang mengembalikan diagnostik. Dalam perbaikan ini, hasil tersebut ditafsirkan hanya memuat diagnostik script yang sedang diproses. Penggunaan ulang instance belum diatur secara eksplisit, sehingga temuan ini dicatat sebagai perbaikan untuk skenario tersebut.

**Reproduksi minimal.** 
Jalankan kedua SQL berikut sebagai dua script terpisah menggunakan objek resolver yang sama:
```
SELECT q.id FROM pelanggan p;
SELECT p.id FROM pelanggan p;
```

Cara reproduksi:
```
resolver = Resolver()
resolver.resolve_script(parse_sql("SELECT q.id FROM pelanggan p;"))
hasil = resolver.resolve_script(parse_sql("SELECT p.id FROM pelanggan p;"))
```
Hasil kedua masih memuat error alias 'q' tidak terdefinisi, padahal hasil yang diharapkan adalah list kosong.

**Akar masalah.**
Masalah terdapat pada fungsi resolve_script() dalam crud/resolver.py. List self.diagnostics hanya dibuat saat objek diinisialisasi dan tidak direset sebelum memproses script berikutnya.

Hal ini berkaitan dengan pengelolaan state pada pass resolusi dalam Crafting Interpreters Bab 11. Pada kasus ini, hasil diagnostik pemrosesan sebelumnya masih tersimpan dalam objek. Scope sudah kembali None, sehingga penyebabnya bukan kebocoran scope.

**Perbaikan.**
Tambahkan pembuatan list diagnostik baru pada awal fungsi resolve_script():
```
def resolve_script(self, script: ast.Script) -> list[Diagnostic]:
    # Diagnostik hanya untuk script yang sedang diproses.
    self.diagnostics = []

    for stmt in script.statements:
        self.resolve_statement(stmt)

    return self.diagnostics
```
Alternatif self.diagnostics.clear() tidak dipilih karena mengosongkan list yang sama, sehingga hasil pemanggilan sebelumnya yang masih disimpan oleh pemanggil ikut berubah. Penggunaan list baru mempertahankan hasil sebelumnya.

**Test regresi.**
Test test_resolver_diagnostik_tidak_terbawa_ke_script_berikutnya ditambahkan dalam tests/test_tambahan.py. Test memeriksa bahwa script pertama menghasilkan error alias, sedangkan script kedua menghasilkan diagnostik kosong ketika menggunakan resolver yang sama.

Perintah pengujian:
```
python -m pytest tests/test_tambahan.py::test_resolver_diagnostik_tidak_terbawa_ke_script_berikutnya -v
```
Sebelum perbaikan, hasilnya 1 failed in 0.54s. Setelah perbaikan, test yang sama menghasilkan 1 passed in 0.10s. Pengujian seluruh suite menghasilkan 52 passed in 0.27s.

**Peran AI.**
AI membantu dalam menemukan dan mengidentifikasi penyebab diagnostik lama terbawa melalui pemeriksaan fungsi resolve_script(), AI juga memberikan gamabran terkait penyusunan test regrasi dan menyarankan pembuatan list diagnostik baru.
