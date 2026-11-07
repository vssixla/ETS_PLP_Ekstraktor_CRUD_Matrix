# Kartu Desain

Keputusan ini mengacu pada `SPESIFIKASI.md` dan perbaikan yang dilakukan dengan tetap mempertahankan API publik serta urutan pipeline lexer, parser, resolver, dan analyzer.

| No | Keputusan | Alternatif yang Ditolak | Alasan |
| :--- | :--- | :--- | :--- |

| 1 | **Memisahkan presedensi `AND` dan `OR` ke dua fungsi.** `_logical()` menangani `OR` dan memanggil `_and()`. `_and()` menangani `AND` dan memanggil `_not()`. Satu fungsi satu tingkat presedensi. | Menangani `AND` dan `OR` dalam satu perulangan pada tingkat yang sama (kode awal memakai `_check_kw("AND", "OR")`). | Spesifikasi bagian 3.1 menetapkan `AND` mengikat lebih kuat daripada `OR`. Pada satu perulangan, `a = 1 OR b = 2 AND c = 3` dikelompokkan dari kiri menjadi `(a = 1 OR b = 2) AND c = 3`, yang salah. Dengan dua fungsi, hasilnya `a = 1 OR (b = 2 AND c = 3)`. Ini sesuai pola recursive descent: tiap tingkat presedensi menjadi satu fungsi yang memanggil tingkat di bawahnya (Crafting Interpreters bab 6). |

| 2 | **Error recovery berhenti setelah mengonsumsi `;` berikutnya**, atau di akhir input. Setelah itu parser melanjutkan ke statement berikutnya. | Berhenti ketika menemukan keyword `SELECT` berikutnya. | Spesifikasi bagian 6 menetapkan `;` sebagai titik sinkronisasi. `SELECT` bisa muncul di tengah satu statement, misalnya pada subquery atau `INSERT ... SELECT`. Jika berhenti di sana, sisa statement rusak dibaca sebagai statement baru. Contoh: `INSERT INTO arsip (id SELECT id FROM pesanan;` akan menghasilkan statement `SELECT` palsu dan tabel `pesanan` ikut tercatat R. Dengan berhenti di `;`, statement rusak tidak dihitung dan setiap statement rusak menghasilkan tepat satu error. |
