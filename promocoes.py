import random
import time

from catalogo import PRODUTOS
from comum.config import EXCHANGE_PROMOCOES
from comum.mensagens import publicar_evento


def gerar_promocao():
    codigo = random.choice(list(PRODUTOS))
    produto = PRODUTOS[codigo]
    desconto = random.choice([10, 15, 20, 30])
    dados = {
        "produto_id": codigo,
        "nome": produto["nome"],
        "desconto": desconto,
        "preco_original": produto["preco"],
    }
    evento = "promocao.categoria." + produto["categoria"]
    publicar_evento("promocoes", evento, dados, EXCHANGE_PROMOCOES)
    print("Promocao publicada:", evento, dados)


def iniciar():
    while True:
        gerar_promocao()
        time.sleep(10)


if __name__ == "__main__":
    iniciar()
