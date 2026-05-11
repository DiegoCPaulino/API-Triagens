import os
import oracledb


def _carregar_env():
    raiz = os.path.normpath(os.path.join(os.path.dirname(__file__), "..", ".."))
    caminho_env = os.path.join(raiz, ".env")
    if not os.path.isfile(caminho_env):
        return
    with open(caminho_env, encoding="utf-8") as f:
        for linha in f:
            linha = linha.strip()
            if not linha or linha.startswith("#") or "=" not in linha:
                continue
            chave, _, valor = linha.partition("=")
            chave = chave.strip()
            valor = valor.strip().strip('"').strip("'")
            if chave and chave not in os.environ:
                os.environ[chave] = valor


_carregar_env()

DB_USER = os.environ.get("DB_USER", "SEU_USUARIO_ORACLE")
DB_PASSWORD = os.environ.get("DB_PASSWORD", "SUA_SENHA_ORACLE")
DB_DSN = os.environ.get("DB_DSN", "oracle.fiap.com.br:1521/ORCL")

_PLACEHOLDERS = ("SEU_USUARIO_ORACLE", "SUA_SENHA_ORACLE")


def obter_conexao():
    if DB_USER in _PLACEHOLDERS or DB_PASSWORD in _PLACEHOLDERS:
        print("\n[AVISO] Credenciais Oracle nao configuradas.")
        print("Preencha DB_USER, DB_PASSWORD e DB_DSN no arquivo .env na raiz do projeto.")
        return None
    try:
        conexao = oracledb.connect(user=DB_USER, password=DB_PASSWORD, dsn=DB_DSN)
        return conexao
    except oracledb.DatabaseError as exc:
        print(f"\n[ERRO] Falha ao conectar ao banco Oracle: {exc}")
        print("Verifique as credenciais no arquivo .env.")
        return None


def testar_conexao():
    conexao = obter_conexao()
    if conexao is None:
        print("[AVISO] O sistema iniciou sem conexao com o banco. As operacoes de dados falharao.")
        return False
    try:
        conexao.close()
    except Exception:
        pass
    print("[OK] Conexao com o banco Oracle estabelecida com sucesso.")
    return True
