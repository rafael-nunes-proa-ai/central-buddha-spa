"""
Script de Teste - Sistema de Alertas por E-mail
Testa o envio de e-mails de alerta do Google Maps API
"""

import sys
import os
from pathlib import Path

# Adiciona o diretório raiz ao path
root_dir = Path(__file__).parent
sys.path.insert(0, str(root_dir))

from services.email_service import testar_envio_email, enviar_alerta_50_porcento, enviar_alerta_100_porcento


def menu():
    """Menu interativo para testar envio de e-mails"""
    print("=" * 80)
    print("🧪 TESTE - SISTEMA DE ALERTAS POR E-MAIL")
    print("=" * 80)
    print()
    print("Escolha uma opção:")
    print()
    print("1. Enviar e-mail de teste simples")
    print("2. Enviar alerta de 50% da cota (5.000 requisições)")
    print("3. Enviar alerta de 100% da cota (10.000 requisições)")
    print("0. Sair")
    print()
    
    opcao = input("Digite a opção: ").strip()
    
    if opcao == "1":
        print("\n📧 Enviando e-mail de teste...\n")
        testar_envio_email()
    
    elif opcao == "2":
        print("\n📧 Enviando alerta de 50% da cota...\n")
        enviar_alerta_50_porcento(requisicoes_mes=5000, total=5000)
    
    elif opcao == "3":
        print("\n📧 Enviando alerta de 100% da cota...\n")
        enviar_alerta_100_porcento(requisicoes_mes=10000, total=10000)
    
    elif opcao == "0":
        print("\n👋 Saindo...\n")
        sys.exit(0)
    
    else:
        print("\n❌ Opção inválida!\n")
    
    print()
    input("Pressione ENTER para continuar...")
    print("\n" * 2)
    menu()


if __name__ == "__main__":
    try:
        menu()
    except KeyboardInterrupt:
        print("\n\n👋 Saindo...\n")
        sys.exit(0)
