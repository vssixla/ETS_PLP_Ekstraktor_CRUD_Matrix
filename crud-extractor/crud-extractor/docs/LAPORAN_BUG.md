# Laporan Bug

Salin blok di bawah untuk setiap bug. Bagian **Akar masalah** wajib ditulis dengan kata-kata
sendiri dan memakai konsep dari *Crafting Interpreters* (sebutkan bab). Bagian ini diuji lisan.

---
## Bug 1: Parser Membuang Statement Valid setelah Kesalahan Sintaks

**Ditemukan oleh:** ALIA ARDANI · **Diperbaiki oleh:** ALIA ARDANI

**Gejala.** 
Pada file campuran_error.sql, statement SELECT di baris 4 mengandung kesalahan sintaks. Program melaporkan kesalahan tersebut, tetapi hanya memproses SELECT pertama di baris 2. Statement UPDATE di baris 6 dan DELETE di baris 8 yang valid ikut terlewat.

Pada SPESIFIKASI.md bagian 6, parser seharusnya membuang token sampai dan termasuk tanda ";" berikutnya, kemudian melanjutkan pemrosesan statement setelahnya. Statement rusak menghasilkan tepat satu parse error dan tidak dihitung dalam CRUD matrix.


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
