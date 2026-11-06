"""Test tambahan buatan kelompok.

Isi dengan:
1. Satu test regresi untuk setiap bug yang kalian perbaiki (gagal sebelum perbaikan,
   lulus sesudahnya). Beri nama yang menjelaskan bug-nya.
2. Lima test kasus tepi, masing-masing dengan komentar singkat mengapa kasus itu berisiko.
"""

import pytest
from crud.pipeline import analyze_source
from crud.lexer import tokenize, LexError

#test untuk Bug 1
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

#Bug 2
def test_keyword_huruf_campuran():
    toks = tokenize("Select x FrOm t")
    assert toks[0].value == "SELECT"
    assert toks[2].value == "FROM"

#Bug 3
def test_operator_tidak_sama_dipindai_sebagai_satu_token():
    from crud.lexer import TokenType, tokenize

    tokens = tokenize("a <> 10")

    assert [
        (token.type, token.value)
        for token in tokens
    ] == [
        (TokenType.IDENT, "a"),
        (TokenType.OP, "<>"),
        (TokenType.NUMBER, "10"),
        (TokenType.EOF, ""),
    ]

#tes_TODO (T1)
def test_insert_select_membentuk_ast_dan_crud():
    from crud import ast_nodes as ast
    from crud.parser import parse_sql
    from crud.pipeline import analyze_source

    sql = "INSERT INTO arsip (id) SELECT id FROM pesanan;"

    # Parser menerima INSERT ... SELECT tanpa kesalahan.
    script = parse_sql(sql)

    assert script.errors == []
    assert len(script.statements) == 1

    # AST menyimpan tabel tujuan dan query sumber.
    statement = script.statements[0]

    assert isinstance(statement, ast.Insert)
    assert statement.table.name == "arsip"
    assert statement.columns == ["id"]
    assert statement.values == []
    assert isinstance(statement.query, ast.Select)
    assert statement.query.sources[0].name == "pesanan"

    # INSERT membuat data pada tujuan dan membaca tabel sumber.
    hasil = analyze_source(sql)

    assert hasil.lex_error is None
    assert hasil.parse_errors == []
    assert hasil.matrix() == {
        "arsip": "C",
        "pesanan": "R",
    }

#tes_TODO (T3)
def test_komentar_blok_berisi_bintang():
    toks = tokenize("a /* x ** y */ b")
    assert toks[0].value == "a"
    assert toks[1].value == "b"


def test_komentar_blok_tidak_ditutup():
    with pytest.raises(LexError):
        tokenize("SELECT 1 /* belum ditutup")

#Bug 4
def test_string_kutip_ganda_menjadi_satu_token():
    toks = tokenize("'O''Brien'")
    assert len(toks) == 2          # satu STRING + EOF
    assert toks[0].value == "O'Brien"
