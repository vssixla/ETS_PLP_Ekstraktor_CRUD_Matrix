# ETS PLP 2026 — Kelompok 7
**SQL CRUD Matrix Extractor**

**Informasi Tugas:**  
ETS Semester 3 Tahun 2026  
Mata Kuliah: Programming Language Pragmatics  
Kelas: 2B — D4 Teknik Informatika  
Dosen: Joe Lian Min, M.Eng.

## DESKRIPSI
SQL CRUD Matrix Extractor merupakan proyek ETS yang dikembangkan untuk membaca file SQL dan menganalisis operasi CRUD (*Create, Read, Update,* dan *Delete*) pada setiap tabel. Hasil analisis disajikan dalam bentuk CRUD Matrix yang menunjukkan operasi yang dilakukan terhadap masing-masing tabel.

## ANGGOTA KELOMPOK
| NIM | Nama | GitHub |
|---|---|---|
| 251524035 | Alia Ardani | @vssixla |
| 251524062 | Shahnaz Saskia Putri | @nanaszs |

## TEKNOLOGI
- Python 3.10 atau lebih baru
- Pytest
- Git dan GitHub

## ALUR KERJA
Proses analisis SQL dilakukan melalui beberapa tahap:

1. **Lexer** — Membaca kode SQL dan mengubahnya menjadi kumpulan token.
2. **Parser** — Memeriksa susunan token berdasarkan grammar dan membentuk AST.
3. **Resolver** — Menentukan hubungan tabel, alias, dan scope.
4. **Analyzer** — Menganalisis operasi CRUD pada setiap tabel.
5. **Output** — Menghasilkan CRUD Matrix serta detail penggunaan tabel dan kolom.

          +-------------+
          |   File SQL  |
          +-------------+
                 |
                 v
          +-------------+
          |    Lexer    |
          +-------------+
                 |
                 v
          +-------------+
          |   Parser    |
          +-------------+
                 |
                 v
          +-------------+
          |  Resolver   |
          +-------------+
                 |
                 v
          +-------------+
          |  Analyzer  |
          +-------------+
                 |
                 v
          +-------------+
          | CRUD Matrix |
          +-------------+
                 |
                 v
          +-------------+
          |  File CSV   |
          +-------------+

## CARA MENJALANKAN

1. Clone repositori:
   ```bash
   git clone https://github.com/vssixla/ETS_PLP_Ekstraktor_CRUD_Matrix_035_062.git
   ```

2. Masuk ke direktori proyek:
   ```bash
   cd ETS_PLP_Ekstraktor_CRUD_Matrix_035_062
   ```

3. Instal pytest:
   ```bash
   python -m pip install pytest
   ```

4. Jalankan seluruh test:
   ```bash
   python -m pytest
   ```

5. Jalankan ekstraktor CRUD Matrix:
   ```bash
   python -m crud.cli data/sample/*.sql --detail detail.csv --kolom kolom.csv
   ```

6. Lihat AST hasil parsing dan resolusi:
   ```bash
   python -m crud.cli data/sample/audit.sql --ast
   ```

7. Jalankan evaluasi:
   ```bash
   python evaluate.py
   ```

---

```text
 /\_/\
( o.o )
 > ^ <
```

