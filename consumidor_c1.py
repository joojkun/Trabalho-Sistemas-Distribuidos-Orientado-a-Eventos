from comum.mensagens import consumir_eventos
from comum.config import EXCHANGE_PROMOCOES


def receber(envelope):
    print("C1 recebeu:", envelope["Event"], envelope["Data"])


if __name__ == "__main__":
    consumir_eventos(
        "fila.C1",
        ["promocao.categoria.A", "promocao.categoria.B"],
        receber,
        EXCHANGE_PROMOCOES,
    )
