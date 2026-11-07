"""Test tambahan buatan kelompok.

Isi dengan:
1. Satu test regresi untuk setiap bug yang kalian perbaiki (gagal sebelum perbaikan,
   lulus sesudahnya). Beri nama yang menjelaskan bug-nya.
2. Lima test kasus tepi, masing-masing dengan komentar singkat mengapa kasus itu berisiko.
"""

import pytest
from crud.pipeline import analyze_source
from crud.lexer import tokenize, LexError

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

#TES TODO(T2)
def test_t2_kolom_tanpa_qualifier():
    from crud.parser import parse_sql
    from crud.resolver import Resolver

    kasus = [
        # Satu sumber: kolom diarahkan ke pelanggan.
        (
            "SELECT nama FROM pelanggan;",
            "pelanggan",
            None,
        ),
        # Dua sumber: tidak boleh memilih salah satu.
        (
            "SELECT nama FROM pelanggan p, pesanan o;",
            None,
            "ambigu tanpa skema",
        ),
    ]

    for sql, expected_table, expected_warning in kasus:
        script = parse_sql(sql)
        assert script.errors == [], sql

        diagnostics = Resolver().resolve_script(script)
        column = script.statements[0].columns[0].expr

        assert column.resolved == expected_table, sql

        if expected_warning is None:
            assert diagnostics == [], sql
        else:
            assert len(diagnostics) == 1, sql
            assert diagnostics[0].level == "warning", sql
            assert expected_warning in diagnostics[0].message, sql
            assert diagnostics[0].line == 1, sql

#TES TODO(T2) 2
def test_t2_kolom_tanpa_qualifier_scope_kosong():
    from crud.parser import parse_sql
    from crud.resolver import Resolver, Scope, ScopeEntry

    # Ambil node kolom dari SQL yang diterima parser.
    script = parse_sql("SELECT nama FROM pelanggan;")
    assert script.errors == []

    column = script.statements[0].columns[0].expr

    # Scope luar memiliki tabel pelanggan.
    outer_scope = Scope()
    outer_scope.entries["pelanggan"] = ScopeEntry(
        name="pelanggan",
        table="pelanggan",
        line=1,
    )

    # Scope terdalam sengaja dibuat kosong untuk menguji aturan T2.
    resolver = Resolver()
    resolver.scope = Scope(parent=outer_scope)

    resolver._column(column)

    # Tidak boleh mengambil tabel dari scope luar.
    assert column.resolved is None
    assert len(resolver.diagnostics) == 1

    diagnostic = resolver.diagnostics[0]
    assert diagnostic.level == "warning"
    assert "tanpa tabel" in diagnostic.message
    assert diagnostic.line == 1

#tes_TODO (T3)
def test_komentar_blok_berisi_bintang():
    toks = tokenize("a /* x ** y */ b")
    assert toks[0].value == "a"
    assert toks[1].value == "b"


def test_komentar_blok_tidak_ditutup():
    with pytest.raises(LexError):
        tokenize("SELECT 1 /* belum ditutup")


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

#Bug 4
def test_string_kutip_ganda_menjadi_satu_token():
    toks = tokenize("'O''Brien'")
    assert len(toks) == 2          # satu STRING + EOF
    assert toks[0].value == "O'Brien"

#Bug 5
def test_subquery_di_update_hanya_dibaca():
    hasil = analyze_source(
        "UPDATE pelanggan SET aktif = 0 WHERE id IN (SELECT pelanggan_id FROM pesanan);"
    )
    assert hasil.matrix() == {"pelanggan": "U", "pesanan": "R"}

#Bug 6
def test_alias_delete_tidak_bocor_ke_statement_berikutnya():
    hasil = analyze_source(
        "DELETE FROM sesi s WHERE s.id = 1;\n"
        "SELECT s.id FROM pengguna u;"
    )
    pesan = [d.message for d in hasil.diagnostics]
    assert any("'s'" in m for m in pesan)

#Bug 7 
def test_alias_dalam_menutupi_alias_luar():
    from crud.parser import parse_sql
    from crud.resolver import Resolver

    sql = (
        "SELECT x.id FROM pelanggan x "
        "WHERE EXISTS (SELECT x.id FROM pesanan x);"
    )

    script = parse_sql(sql)
    assert script.errors == []

    diagnostics = Resolver().resolve_script(script)
    assert diagnostics == []

    select_luar = script.statements[0]
    select_dalam = select_luar.where.query

    kolom_luar = select_luar.columns[0].expr
    kolom_dalam = select_dalam.columns[0].expr

    assert kolom_luar.resolved == "pelanggan"
    assert kolom_dalam.resolved == "pesanan"

# Bug 8
def test_and_lebih_kuat_daripada_or():
    from crud import ast_nodes as ast
    from crud.parser import parse_sql

    script = parse_sql(
        "SELECT id FROM t WHERE a = 1 OR b = 2 AND c = 3;"
    )

    assert script.errors == []

    kondisi = script.statements[0].where

    # Pengelompokan yang benar: a = 1 OR (b = 2 AND c = 3).
    assert isinstance(kondisi, ast.BinaryOp)
    assert kondisi.op == "OR"

    assert isinstance(kondisi.left, ast.BinaryOp)
    assert kondisi.left.op == "="
    assert kondisi.left.left.name == "a"

    assert isinstance(kondisi.right, ast.BinaryOp)
    assert kondisi.right.op == "AND"
    assert kondisi.right.left.op == "="
    assert kondisi.right.left.left.name == "b"
    assert kondisi.right.right.op == "="
    assert kondisi.right.right.left.name == "c"

#Bug 9
def test_left_outer_join_diterima():
    from crud.parser import parse_sql

    sql = "SELECT p.id FROM pelanggan p LEFT OUTER JOIN pesanan s ON p.id = s.id;"
    script = parse_sql(sql)

    assert script.errors == []
    assert len(script.statements) == 1

#Bug 10
def test_parameter_berawalan_angka():
    from crud.lexer import tokenize, TokenType

    tokens = tokenize(":1")

    assert len(tokens) == 2
    assert tokens[0].type == TokenType.PARAM
    assert tokens[0].value == ":1"
    assert tokens[0].line == 1
    assert tokens[0].col == 1
    assert tokens[1].type == TokenType.EOF

#LIMA TEST KASUS TEPI
def test_tepi_input_kosong_menghasilkan_eof():
    from crud.lexer import TokenType

    # Risiko: lexer mengakses karakter di luar input saat sumber kosong.
    token = tokenize("")

    assert len(token) == 1
    assert tokens[0].type == TokenType.EOF

def test_tepi_input_hanya_whitespace():
    from crud.lexer import TokenType

    # Risiko: spasi, tab, dan baris baru menghasilkan token yang tidak diperlukan.
    tokens = tokenize(" \t\r\n ")

    assert len(tokens) == 1
    assert tokens[0].type == TokenType.EOF


def test_tepi_komentar_baris_di_akhir_file():
    from crud.lexer import TokenType

    # Risiko: pemindaian komentar menunggu newline meskipun input sudah habis.
    tokens = tokenize("-- komentar tanpa baris baru")

def test_tepi_komentar_tanpa_newline_di_akhir_input():
    from crud.lexer import TokenType

    # Risiko: pemindaian komentar menunggu newline meskipun input sudah habis.
    tokens = tokenize("-- komentar tanpa baris baru")

    assert len(tokens) == 1
    assert tokens[0].type == TokenType.EOF

def test_tepi_penanda_komentar_di_dalam_string():
    from crud.lexer import TokenType

    # Risiko: penanda komentar dalam string dianggap sebagai komentar SQL.
    tokens = tokenize("'-- bukan komentar /* tetap string */'")

    assert len(tokens) == 2
    assert tokens[0].type == TokenType.STRING
    assert tokens[0].value == "-- bukan komentar /* tetap string */"
    assert tokens[1].type == TokenType.EOF