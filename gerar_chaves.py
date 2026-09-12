from comum.config import SERVICOS
from comum.seguranca import garantir_chaves


for nome in SERVICOS:
    garantir_chaves(nome)
    print("Chaves prontas:", nome)
