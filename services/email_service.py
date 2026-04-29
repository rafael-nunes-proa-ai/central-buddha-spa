"""
Serviço de Envio de E-mails usando AWS SES via SMTP
Usado para alertas de monitoramento do Google Maps API
"""

import os
import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from datetime import datetime, timezone, timedelta
from dotenv import load_dotenv

load_dotenv()

# Fuso horário de São Paulo (UTC-3)
TZ_SAO_PAULO = timezone(timedelta(hours=-3))


def _agora_br() -> str:
    """Retorna data/hora atual no fuso de São Paulo formatada"""
    return datetime.now(TZ_SAO_PAULO).strftime('%d/%m/%Y %H:%M:%S')

# Configurações AWS SES via SMTP
SMTP_HOST = os.getenv('SMTP_HOST', 'email-smtp.us-east-1.amazonaws.com')
SMTP_PORT = int(os.getenv('SMTP_PORT', 587))
SMTP_USER = os.getenv('AWS_SES_ACCESS_KEY')  # SMTP username
SMTP_PASS = os.getenv('AWS_SES_SECRET_KEY')  # SMTP password
EMAIL_FROM = os.getenv('EMAIL_FROM', 'naoresponda@proatecnologia.com.br')

# E-mails dos responsáveis
ALERT_EMAILS = [
    os.getenv('ALERT_EMAIL_1')
]

# Verifica se SMTP está configurado
SMTP_CONFIGURED = bool(SMTP_USER and SMTP_PASS)


def enviar_alerta_50_porcento(requisicoes_mes: int, total: int):
    """
    Envia alerta quando atingir 50% da cota gratuita (5.000 requisições)
    
    Args:
        requisicoes_mes: Requisições do mês atual
        total: Total histórico de requisições
    """
    if not SMTP_CONFIGURED:
        print("⚠️ AWS SES SMTP não configurado. E-mail não enviado.")
        return
    
    # Filtra emails válidos
    destinatarios = [email for email in ALERT_EMAILS if email]
    
    if not destinatarios:
        print("⚠️ Nenhum e-mail de alerta configurado.")
        return
    
    assunto = "🚨 ALERTA: Google Maps API - 50% da Cota Gratuita Atingida"
    
    corpo_html = f"""
    <html>
    <head>
        <style>
            body {{ font-family: Arial, sans-serif; line-height: 1.6; color: #333; }}
            .container {{ max-width: 600px; margin: 0 auto; padding: 20px; }}
            .header {{ background-color: #ff9800; color: white; padding: 20px; text-align: center; border-radius: 5px; }}
            .content {{ background-color: #f9f9f9; padding: 20px; margin-top: 20px; border-radius: 5px; }}
            .alert {{ background-color: #fff3cd; border-left: 4px solid #ff9800; padding: 15px; margin: 20px 0; }}
            .stats {{ background-color: white; padding: 15px; margin: 15px 0; border-radius: 5px; }}
            .footer {{ margin-top: 30px; padding-top: 20px; border-top: 1px solid #ddd; font-size: 12px; color: #666; }}
            .button {{ display: inline-block; padding: 10px 20px; background-color: #4285f4; color: white; text-decoration: none; border-radius: 5px; margin-top: 10px; }}
            ul {{ margin: 10px 0; padding-left: 20px; }}
        </style>
    </head>
    <body>
        <div class="container">
            <div class="header">
                <h1>⚠️ ALERTA AUTOMÁTICO</h1>
                <p>Buddha Spa - Bot Central</p>
            </div>
            
            <div class="content">
                <div class="alert">
                    <h2>🚨 50% da Cota Gratuita Atingida!</h2>
                    <p><strong>Você atingiu metade do limite gratuito mensal do Google Maps Geocoding API.</strong></p>
                </div>
                
                <div class="stats">
                    <h3>📊 Estatísticas de Uso</h3>
                    <ul>
                        <li><strong>Requisições este mês:</strong> {requisicoes_mes:,}</li>
                        <li><strong>Total histórico:</strong> {total:,}</li>
                        <li><strong>Cota gratuita mensal:</strong> 10.000 requisições</li>
                        <li><strong>Percentual usado:</strong> {(requisicoes_mes/10000)*100:.1f}%</li>
                        <li><strong>Data/Hora:</strong> {_agora_br()}</li>
                    </ul>
                </div>
                
                <div class="stats">
                    <h3>💰 Informações de Custo</h3>
                    <ul>
                        <li><strong>Cota gratuita:</strong> 10.000 requisições/mês</li>
                        <li><strong>Após 10.000:</strong> $5 por 1.000 requisições (até 100k)</li>
                        <li><strong>Após 100.000:</strong> $4 por 1.000 requisições (até 500k)</li>
                    </ul>
                </div>
                
                <div class="stats">
                    <h3>✅ Ações Recomendadas</h3>
                    <ul>
                        <li>Revisar uso no dashboard do Google Cloud</li>
                        <li>Verificar logs do bot para identificar picos de uso</li>
                        <li>Considerar otimizações se necessário (cache, redução de chamadas)</li>
                        <li>Monitorar próximos dias para evitar exceder a cota</li>
                    </ul>
                </div>
                
                <a href="https://console.cloud.google.com/apis/dashboard" class="button">
                    📊 Acessar Dashboard Google Cloud
                </a>
            </div>
            
            <div class="footer">
                <p>Este é um alerta automático do sistema de monitoramento do Buddha Spa Bot Central.</p>
                <p>Para dúvidas, entre em contato com a equipe de TI.</p>
            </div>
        </div>
    </body>
    </html>
    """
    
    corpo_texto = f"""
⚠️ ALERTA AUTOMÁTICO - Buddha Spa Bot Central

🚨 50% DA COTA GRATUITA ATINGIDA!

Você atingiu metade do limite gratuito mensal do Google Maps Geocoding API.

📊 ESTATÍSTICAS DE USO
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
Requisições este mês: {requisicoes_mes:,}
Total histórico: {total:,}
Cota gratuita mensal: 10.000 requisições
Percentual usado: {(requisicoes_mes/10000)*100:.1f}%
Data/Hora: {_agora_br()}

💰 INFORMAÇÕES DE CUSTO
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
Cota gratuita: 10.000 requisições/mês
Após 10.000: $5 por 1.000 requisições (até 100k)
Após 100.000: $4 por 1.000 requisições (até 500k)

✅ AÇÕES RECOMENDADAS
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
- Revisar uso no dashboard do Google Cloud
- Verificar logs do bot para identificar picos de uso
- Considerar otimizações se necessário (cache, redução de chamadas)
- Monitorar próximos dias para evitar exceder a cota

Dashboard: https://console.cloud.google.com/apis/dashboard

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
Este é um alerta automático do sistema de monitoramento.
    """
    
    _enviar_email(destinatarios, assunto, corpo_html, corpo_texto)


def enviar_alerta_100_porcento(requisicoes_mes: int, total: int):
    """
    Envia alerta quando exceder a cota gratuita (10.000 requisições)
    
    Args:
        requisicoes_mes: Requisições do mês atual
        total: Total histórico de requisições
    """
    if not SMTP_CONFIGURED:
        print("⚠️ AWS SES SMTP não configurado. E-mail não enviado.")
        return
    
    # Filtra emails válidos
    destinatarios = [email for email in ALERT_EMAILS if email]
    
    if not destinatarios:
        print("⚠️ Nenhum e-mail de alerta configurado.")
        return
    
    assunto = "🚨🚨 URGENTE: Google Maps API - Cota Gratuita EXCEDIDA!"
    
    corpo_html = f"""
    <html>
    <head>
        <style>
            body {{ font-family: Arial, sans-serif; line-height: 1.6; color: #333; }}
            .container {{ max-width: 600px; margin: 0 auto; padding: 20px; }}
            .header {{ background-color: #d32f2f; color: white; padding: 20px; text-align: center; border-radius: 5px; }}
            .content {{ background-color: #f9f9f9; padding: 20px; margin-top: 20px; border-radius: 5px; }}
            .alert {{ background-color: #ffebee; border-left: 4px solid #d32f2f; padding: 15px; margin: 20px 0; }}
            .stats {{ background-color: white; padding: 15px; margin: 15px 0; border-radius: 5px; }}
            .footer {{ margin-top: 30px; padding-top: 20px; border-top: 1px solid #ddd; font-size: 12px; color: #666; }}
            .button {{ display: inline-block; padding: 10px 20px; background-color: #d32f2f; color: white; text-decoration: none; border-radius: 5px; margin-top: 10px; }}
            ul {{ margin: 10px 0; padding-left: 20px; }}
            .warning {{ color: #d32f2f; font-weight: bold; }}
        </style>
    </head>
    <body>
        <div class="container">
            <div class="header">
                <h1>🚨 ALERTA CRÍTICO 🚨</h1>
                <p>Buddha Spa - Bot Central</p>
            </div>
            
            <div class="content">
                <div class="alert">
                    <h2>⚠️ COTA GRATUITA EXCEDIDA!</h2>
                    <p class="warning">Você ultrapassou o limite de 10.000 requisições gratuitas!</p>
                    <p><strong>A partir de agora, você está sendo cobrado por cada requisição adicional.</strong></p>
                </div>
                
                <div class="stats">
                    <h3>📊 Estatísticas de Uso</h3>
                    <ul>
                        <li><strong>Requisições este mês:</strong> {requisicoes_mes:,}</li>
                        <li><strong>Total histórico:</strong> {total:,}</li>
                        <li><strong>Requisições excedentes:</strong> {requisicoes_mes - 10000:,}</li>
                        <li><strong>Data/Hora:</strong> {_agora_br()}</li>
                    </ul>
                </div>
                
                <div class="stats">
                    <h3>💰 Custo Estimado</h3>
                    <ul>
                        <li><strong>Requisições pagas:</strong> {requisicoes_mes - 10000:,}</li>
                        <li><strong>Custo por 1.000 req:</strong> $5.00</li>
                        <li><strong>Custo estimado:</strong> ${((requisicoes_mes - 10000) / 1000) * 5:.2f}</li>
                    </ul>
                    <p style="color: #d32f2f; font-weight: bold;">⚠️ Este valor será cobrado na sua fatura do Google Cloud!</p>
                </div>
                
                <div class="stats">
                    <h3>🚨 Ações URGENTES</h3>
                    <ul>
                        <li><strong>Revisar IMEDIATAMENTE</strong> o dashboard do Google Cloud</li>
                        <li><strong>Identificar</strong> causa do alto volume de requisições</li>
                        <li><strong>Considerar</strong> pausar o bot temporariamente se necessário</li>
                        <li><strong>Implementar</strong> cache para reduzir chamadas à API</li>
                        <li><strong>Verificar</strong> se há loop ou bug causando requisições excessivas</li>
                    </ul>
                </div>
                
                <a href="https://console.cloud.google.com/apis/dashboard" class="button">
                    📊 Acessar Dashboard AGORA
                </a>
            </div>
            
            <div class="footer">
                <p>Este é um alerta CRÍTICO do sistema de monitoramento do Buddha Spa Bot Central.</p>
                <p><strong>Ação imediata necessária!</strong> Entre em contato com a equipe de TI urgentemente.</p>
            </div>
        </div>
    </body>
    </html>
    """
    
    corpo_texto = f"""
🚨🚨 ALERTA CRÍTICO - Buddha Spa Bot Central 🚨🚨

⚠️ COTA GRATUITA EXCEDIDA!

Você ultrapassou o limite de 10.000 requisições gratuitas!
A partir de agora, você está sendo cobrado por cada requisição adicional.

📊 ESTATÍSTICAS DE USO
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
Requisições este mês: {requisicoes_mes:,}
Total histórico: {total:,}
Requisições excedentes: {requisicoes_mes - 10000:,}
Data/Hora: {_agora_br()}

💰 CUSTO ESTIMADO
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
Requisições pagas: {requisicoes_mes - 10000:,}
Custo por 1.000 req: $5.00
Custo estimado: ${((requisicoes_mes - 10000) / 1000) * 5:.2f}

⚠️ Este valor será cobrado na sua fatura do Google Cloud!

🚨 AÇÕES URGENTES
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
- Revisar IMEDIATAMENTE o dashboard do Google Cloud
- Identificar causa do alto volume de requisições
- Considerar pausar o bot temporariamente se necessário
- Implementar cache para reduzir chamadas à API
- Verificar se há loop ou bug causando requisições excessivas

Dashboard: https://console.cloud.google.com/apis/dashboard

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
Este é um alerta CRÍTICO do sistema de monitoramento.
AÇÃO IMEDIATA NECESSÁRIA!
    """
    
    _enviar_email(destinatarios, assunto, corpo_html, corpo_texto)


def _enviar_email(destinatarios: list, assunto: str, corpo_html: str, corpo_texto: str):
    """
    Envia e-mail usando AWS SES via SMTP
    
    Args:
        destinatarios: Lista de e-mails
        assunto: Assunto do e-mail
        corpo_html: Corpo em HTML
        corpo_texto: Corpo em texto puro
    """
    try:
        print("=" * 80)
        print("📧 ENVIANDO E-MAIL DE ALERTA")
        print(f"De: {EMAIL_FROM}")
        print(f"Para: {', '.join(destinatarios)}")
        print(f"Assunto: {assunto}")
        print(f"SMTP Host: {SMTP_HOST}:{SMTP_PORT}")
        print("=" * 80)
        
        # Cria mensagem multipart (HTML + texto)
        msg = MIMEMultipart('alternative')
        msg['Subject'] = assunto
        msg['From'] = EMAIL_FROM
        msg['To'] = ', '.join(destinatarios)
        
        # Anexa versão texto e HTML
        # IMPORTANTE: ordem importa - texto primeiro, HTML por último (preferido)
        parte_texto = MIMEText(corpo_texto, 'plain', 'utf-8')
        parte_html = MIMEText(corpo_html, 'html', 'utf-8')
        msg.attach(parte_texto)
        msg.attach(parte_html)
        
        # Conecta ao SMTP e envia
        with smtplib.SMTP(SMTP_HOST, SMTP_PORT) as server:
            server.ehlo()
            server.starttls()  # Habilita TLS
            server.ehlo()
            server.login(SMTP_USER, SMTP_PASS)
            server.send_message(msg, from_addr=EMAIL_FROM, to_addrs=destinatarios)
        
        print(f"✅ E-mail enviado com sucesso!")
        print(f"📬 Destinatários: {len(destinatarios)}")
        print("=" * 80)
        
    except smtplib.SMTPAuthenticationError as e:
        print("=" * 80)
        print(f"❌ ERRO de autenticação SMTP: {str(e)}")
        print("💡 Verifique AWS_SES_ACCESS_KEY e AWS_SES_SECRET_KEY no .env")
        print("� Lembre-se: deve ser SMTP credentials, não IAM credentials!")
        print("=" * 80)
    except smtplib.SMTPException as e:
        print("=" * 80)
        print(f"❌ ERRO SMTP: {str(e)}")
        print("=" * 80)
    except Exception as e:
        print("=" * 80)
        print(f"❌ ERRO inesperado ao enviar e-mail: {str(e)}")
        print("=" * 80)


def testar_envio_email():
    """
    Função de teste para verificar se o envio de e-mail está funcionando
    """
    print("🧪 TESTANDO ENVIO DE E-MAIL...")
    
    if not SMTP_CONFIGURED:
        print("❌ AWS SES SMTP não configurado!")
        print("Configure as variáveis de ambiente:")
        print("  - AWS_SES_ACCESS_KEY (SMTP username)")
        print("  - AWS_SES_SECRET_KEY (SMTP password)")
        print("  - EMAIL_FROM")
        print("  - ALERT_EMAIL_1")
        print("  - ALERT_EMAIL_2")
        print("  - ALERT_EMAIL_3 (opcional)")
        return False
    
    destinatarios = [email for email in ALERT_EMAILS if email]
    
    if not destinatarios:
        print("❌ Nenhum e-mail de alerta configurado!")
        return False
    
    assunto = "🧪 Teste - Sistema de Alertas Buddha Spa"
    corpo_html = """
    <html>
    <body>
        <h2>✅ Teste de E-mail</h2>
        <p>Este é um e-mail de teste do sistema de alertas do Buddha Spa Bot Central.</p>
        <p>Se você recebeu este e-mail, o sistema está funcionando corretamente!</p>
        <p><strong>Data/Hora:</strong> """ + _agora_br() + """</p>
    </body>
    </html>
    """
    corpo_texto = f"""
✅ Teste de E-mail

Este é um e-mail de teste do sistema de alertas do Buddha Spa Bot Central.
Se você recebeu este e-mail, o sistema está funcionando corretamente!

Data/Hora: {_agora_br()}
    """
    
    _enviar_email(destinatarios, assunto, corpo_html, corpo_texto)
    return True


if __name__ == "__main__":
    # Teste de envio
    testar_envio_email()
