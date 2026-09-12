from comum.config import EXCHANGE_PROMOCOES
from comum.mensagens import consumir_eventos


def receber(envelope):
    print("C2 recebeu:", envelope["Event"], envelope["Data"])


if __name__ == "__main__":
    consumir_eventos(
        "fila.C2",
        ["promocao.categoria.*"],
        receber,
        EXCHANGE_PROMOCOES,
    )
