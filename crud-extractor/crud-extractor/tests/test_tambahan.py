"""Test tambahan buatan kelompok.

Isi dengan:
1. Satu test regresi untuk setiap bug yang kalian perbaiki (gagal sebelum perbaikan,
   lulus sesudahnya). Beri nama yang menjelaskan bug-nya.
2. Lima test kasus tepi, masing-masing dengan komentar singkat mengapa kasus itu berisiko.
"""
from crud.pipeline import analyze_source

def test_recovery_memproses_statement_setelah_error():
    sql = (
        "SELECT id FROM pelanggan;\n"
        "SELECT id, FROM pesanan;\n"
        "UPDATE produk SET stok = 1;\n"
        "DELETE FROM keranjang WHERE id = 1;\n"
    )

    hasil = analyze_source(sql)

    # Kesalahan sintaks tidak boleh dianggap sebagai kesalahan lexer.
    assert hasil.lex_error is None

    # Statement rusak menghasilkan tepat satu parse error.
    assert len(hasil.parse_errors) == 1
    assert hasil.parse_errors[0].line == 2

    # Statement valid sebelum dan sesudah error tetap diproses.
    assert [
        (stmt.line, stmt.kind)
        for stmt in hasil.statements
    ] == [
        (1, "SELECT"),
        (3, "UPDATE"),
        (4, "DELETE"),
    ]

    # Tabel dari statement rusak tidak masuk hasil.
    assert hasil.matrix() == {
        "pelanggan": "R",
        "produk": "U",
        "keranjang": "D",
    }
