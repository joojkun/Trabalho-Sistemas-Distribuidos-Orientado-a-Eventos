# Trabalho de microsservicos de e-commerce

O projeto usa dois exchanges:

- `eCommerce`, do tipo `direct`, para pedidos, estoque, pagamento e entrega.
- `Promoções`, do tipo `topic`, para as promoções.

Cada processo tem sua própria fila. A comunicação dos processos acontece
somente por eventos do RabbitMQ.

## Instalacao

```powershell
py -m pip install -r requirements.txt
docker compose up -d
py gerar_chaves.py
```

As chaves ficam em `chaves/<microsservico>/`. A chave privada e usada apenas
pelo produtor. A chave publica fica no mesmo diretorio para ser lida pelos
consumidores.

## Execucao

Em terminais separados, execute:

```powershell
py estoque.py
py pagamento.py
py entrega.py
py principal.py
py promocoes.py
py consumidor_c1.py
py consumidor_c2.py
```

No pagamento, e possivel forcar um caso para a apresentacao:

```powershell
$env:PAGAMENTO_RESULTADO = "recusado"
py pagamento.py
```

Para testar o fluxo sem iniciar o RabbitMQ, use a simulacao local:

```powershell
py simulacao.py --cenario todos
```

Ela deve mostrar `sucesso -> enviado`, `estoque -> cancelado_estoque` e
`pagamento -> cancelado_pagamento`. A simulacao tambem usa os mesmos envelopes
assinados para conferir a verificacao de autenticidade.
