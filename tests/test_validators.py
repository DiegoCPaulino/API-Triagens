"""
Testes simples para src/apoio/validators.py
Execute a partir da raiz do projeto: python -m tests.test_validators
"""
from src.apoio.validators import (
    validar_nome,
    validar_cpf,
    validar_idade,
    validar_cep,
    validar_data_nascimento,
    validar_prioridade,
    validar_status,
    validar_id_numerico,
)


def test_validar_nome():
    assert validar_nome("Ana Souza")["status"] is True
    assert validar_nome("Maria")["status"] is False        # apenas um nome
    assert validar_nome(None)["status"] is False
    assert validar_nome("")["status"] is False
    assert validar_nome("José da Silva")["status"] is True
    print("  validar_nome: OK")


def test_validar_cpf():
    assert validar_cpf("12345678901")["status"] is True
    assert validar_cpf("123.456.789-01")["status"] is True   # com mascara
    assert validar_cpf("1234567890")["status"] is False      # 10 digitos
    assert validar_cpf(None)["status"] is False
    print("  validar_cpf: OK")


def test_validar_idade():
    assert validar_idade(11)["status"] is True
    assert validar_idade(17)["status"] is True
    assert validar_idade(14)["status"] is True
    assert validar_idade(10)["status"] is False   # abaixo do minimo
    assert validar_idade(18)["status"] is False   # acima do maximo
    assert validar_idade("15")["status"] is True  # string numerica aceita
    assert validar_idade(None)["status"] is False
    print("  validar_idade: OK")


def test_validar_cep():
    assert validar_cep("01310100")["status"] is True
    assert validar_cep("01310-100")["status"] is True   # com traco
    assert validar_cep("0131010")["status"] is False    # 7 digitos
    assert validar_cep(None)["status"] is False
    print("  validar_cep: OK")


def test_validar_data_nascimento():
    # Data que gera idade valida (adolescente em 2026)
    assert validar_data_nascimento("10/06/2012")["status"] is True   # 13 anos
    assert validar_data_nascimento("01/01/2000")["status"] is False  # adulto
    assert validar_data_nascimento("31/12/2999")["status"] is False  # futuro
    assert validar_data_nascimento("nao-e-data")["status"] is False
    assert validar_data_nascimento(None)["status"] is False
    print("  validar_data_nascimento: OK")


def test_validar_prioridade():
    assert validar_prioridade("baixa")["status"] is True
    assert validar_prioridade("média")["status"] is True
    assert validar_prioridade("alta")["status"] is True
    assert validar_prioridade("urgente")["status"] is False
    assert validar_prioridade(None)["status"] is False
    print("  validar_prioridade: OK")


def test_validar_status():
    assert validar_status("em análise")["status"] is True
    assert validar_status("aprovada")["status"] is True
    assert validar_status("reprovada")["status"] is True
    assert validar_status("aberta")["status"] is False      # status antigo Sprint 3
    assert validar_status("concluída")["status"] is False   # status antigo Sprint 3
    assert validar_status(None)["status"] is False
    print("  validar_status: OK")


def test_validar_id_numerico():
    assert validar_id_numerico(1)["status"] is True
    assert validar_id_numerico("42")["status"] is True
    assert validar_id_numerico(0)["status"] is False
    assert validar_id_numerico(-1)["status"] is False
    assert validar_id_numerico("abc")["status"] is False
    print("  validar_id_numerico: OK")


if __name__ == "__main__":
    print("=== Testes: validators ===")
    test_validar_nome()
    test_validar_cpf()
    test_validar_idade()
    test_validar_cep()
    test_validar_data_nascimento()
    test_validar_prioridade()
    test_validar_status()
    test_validar_id_numerico()
    print("\nTodos os testes passaram.")
