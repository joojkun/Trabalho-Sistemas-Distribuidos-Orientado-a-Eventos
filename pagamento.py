import os
import random

from comum.mensagens import consumir_eventos, publicar_evento


def pagamento_aprovado():
    # A variavel de ambiente ajuda a repetir um cenario durante a apresentacao.
    resultado_forcado = os.getenv("PAGAMENTO_RESULTADO", "").lower()
    if resultado_forcado in ("aprovado", "recusado"):
        return resultado_forcado == "aprovado"
    return random.choice([True, False])


def processar_pagamento(envelope):
    pedido = envelope["Data"]
    # O pagamento so acontece depois da confirmacao do estoque.
    if pagamento_aprovado():
        publicar_evento("pagamento", "pagamento.aprovado", pedido)
        print("Pagamento aprovado:", pedido["pedido_id"])
    else:
        publicar_evento("pagamento", "pagamento.recusado", pedido)
        print("Pagamento recusado:", pedido["pedido_id"])


def iniciar():
    consumir_eventos(
        "fila.pagamento",
        ["pedido.estoque_ok"],
        processar_pagamento,
    )


if __name__ == "__main__":
    iniciar()
