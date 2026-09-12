from datetime import datetime

from comum.mensagens import consumir_eventos, publicar_evento


def preparar_envio(envelope):
    pedido = envelope["Data"]
    # A nota e criada apenas depois do pagamento aprovado.
    nota = "NF-" + pedido["pedido_id"].upper()
    dados = dict(pedido)
    dados["nota_fiscal"] = nota
    dados["data_envio"] = datetime.now().isoformat(timespec="seconds")
    publicar_evento("entrega", "pedido.enviado", dados)
    print("Nota emitida e pedido enviado:", pedido["pedido_id"])


def iniciar():
    consumir_eventos(
        "fila.entrega",
        ["pagamento.aprovado"],
        preparar_envio,
    )


if __name__ == "__main__":
    iniciar()
