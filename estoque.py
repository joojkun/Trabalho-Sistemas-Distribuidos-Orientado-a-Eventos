from catalogo import PRODUTOS
from comum.mensagens import consumir_eventos, publicar_evento


quantidades = {
    "1": 10,
    "2": 8,
    "3": 3,
    "4": 5,
}
reservas = {}


def tratar_evento(envelope):
    evento = envelope["Event"]
    pedido = envelope["Data"]
    pedido_id = pedido["pedido_id"]

    if evento == "pedido.criado":
        pode_atender = all(
            quantidades.get(item["produto_id"], 0) >= item["quantidade"]
            for item in pedido["produtos"]
        )

        if not pode_atender:
            publicar_evento("estoque", "estoque.indisponivel", pedido)
            print("Estoque insuficiente para", pedido_id)
            return

        for item in pedido["produtos"]:
            produto_id = item["produto_id"]
            quantidades[produto_id] -= item["quantidade"]
        reservas[pedido_id] = pedido["produtos"]
        publicar_evento("estoque", "pedido.estoque_ok", pedido)
        print("Estoque reservado para", pedido_id)

    elif evento == "pedido.excluido":
        itens = reservas.pop(pedido_id, [])
        for item in itens:
            quantidades[item["produto_id"]] += item["quantidade"]
        print("Estoque devolvido para", pedido_id)


def iniciar():
    for codigo, quantidade in quantidades.items():
        print("Estoque", codigo, PRODUTOS[codigo]["nome"], quantidade)
    consumir_eventos(
        "fila.estoque",
        ["pedido.criado", "pedido.excluido"],
        tratar_evento,
    )


if __name__ == "__main__":
    iniciar()
