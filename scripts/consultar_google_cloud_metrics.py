"""
Script para consultar métricas REAIS do Google Cloud
Usa a Cloud Monitoring API para obter dados precisos
"""

from google.cloud import monitoring_v3
from datetime import datetime, timedelta
import os
from dotenv import load_dotenv

load_dotenv()

def consultar_metricas_geocoding():
    """
    Consulta métricas reais da Geocoding API no Google Cloud
    
    Requer:
    1. Instalar: pip install google-cloud-monitoring
    2. Configurar credenciais: GOOGLE_APPLICATION_CREDENTIALS no .env
    3. Habilitar Cloud Monitoring API no projeto
    """
    
    # ID do seu projeto Google Cloud
    project_id = os.getenv('GOOGLE_CLOUD_PROJECT_ID')
    
    if not project_id:
        print("❌ GOOGLE_CLOUD_PROJECT_ID não configurado no .env")
        print("   Adicione: GOOGLE_CLOUD_PROJECT_ID=seu-projeto-id")
        return
    
    try:
        # Cliente de monitoramento
        client = monitoring_v3.MetricServiceClient()
        project_name = f"projects/{project_id}"
        
        # Período: últimos 30 dias
        now = datetime.utcnow()
        thirty_days_ago = now - timedelta(days=30)
        
        interval = monitoring_v3.TimeInterval(
            {
                "end_time": {"seconds": int(now.timestamp())},
                "start_time": {"seconds": int(thirty_days_ago.timestamp())},
            }
        )
        
        # Métrica: Geocoding API requests
        # Documentação: https://cloud.google.com/monitoring/api/metrics_gcp
        metric_type = "serviceruntime.googleapis.com/api/request_count"
        
        # Filtro para Geocoding API
        filter_str = (
            f'metric.type="{metric_type}" '
            f'AND resource.type="consumed_api" '
            f'AND resource.labels.service="geocoding-backend.googleapis.com"'
        )
        
        # Agregação: soma de todas as requisições
        aggregation = monitoring_v3.Aggregation(
            {
                "alignment_period": {"seconds": 86400},  # 1 dia
                "per_series_aligner": monitoring_v3.Aggregation.Aligner.ALIGN_SUM,
                "cross_series_reducer": monitoring_v3.Aggregation.Reducer.REDUCE_SUM,
            }
        )
        
        # Consulta
        results = client.list_time_series(
            request={
                "name": project_name,
                "filter": filter_str,
                "interval": interval,
                "aggregation": aggregation,
            }
        )
        
        print("=" * 80)
        print("📊 MÉTRICAS REAIS DO GOOGLE CLOUD - GEOCODING API")
        print("=" * 80)
        print()
        
        total_requisicoes = 0
        
        for result in results:
            print(f"📅 Período: {thirty_days_ago.date()} até {now.date()}")
            print()
            print("📊 Requisições por dia:")
            print("-" * 80)
            
            for point in result.points:
                timestamp = point.interval.end_time
                value = point.value.int64_value
                total_requisicoes += value
                
                data = datetime.fromtimestamp(timestamp.seconds)
                print(f"   {data.date()}: {value:,} requisições")
            
            print()
            print("=" * 80)
            print(f"📈 TOTAL: {total_requisicoes:,} requisições nos últimos 30 dias")
            print("=" * 80)
        
        if total_requisicoes == 0:
            print("⚠️  Nenhuma requisição encontrada.")
            print("   Possíveis causas:")
            print("   - API ainda não foi usada")
            print("   - Filtro incorreto")
            print("   - Permissões insuficientes")
        
    except Exception as e:
        print(f"❌ Erro ao consultar métricas: {e}")
        print()
        print("📋 Checklist:")
        print("   1. Instalou? pip install google-cloud-monitoring")
        print("   2. Configurou GOOGLE_APPLICATION_CREDENTIALS no .env?")
        print("   3. Habilitou Cloud Monitoring API no projeto?")
        print("   4. Tem permissões de leitura no projeto?")
        print()
        print("🔗 Documentação:")
        print("   https://cloud.google.com/monitoring/docs/reference/libraries")


def consultar_via_billing_api():
    """
    Alternativa: Consultar via Cloud Billing API
    Retorna dados de faturamento (mais confiável para custos)
    """
    print("=" * 80)
    print("💰 ALTERNATIVA: CLOUD BILLING API")
    print("=" * 80)
    print()
    print("Para consultar custos e uso via API:")
    print()
    print("1. Habilite Cloud Billing API:")
    print("   https://console.cloud.google.com/apis/library/cloudbilling.googleapis.com")
    print()
    print("2. Instale o cliente:")
    print("   pip install google-cloud-billing")
    print()
    print("3. Use BigQuery Export (RECOMENDADO):")
    print("   - Billing → Billing export → BigQuery export")
    print("   - Configure exportação automática")
    print("   - Consulte com SQL:")
    print()
    print("   SELECT")
    print("     DATE(usage_start_time) as data,")
    print("     service.description as servico,")
    print("     sku.description as sku,")
    print("     SUM(usage.amount) as quantidade,")
    print("     SUM(cost) as custo")
    print("   FROM `projeto.dataset.gcp_billing_export_v1_XXXXX`")
    print("   WHERE service.description = 'Maps'")
    print("   GROUP BY data, servico, sku")
    print("   ORDER BY data DESC")
    print()


if __name__ == "__main__":
    print()
    print("🔍 Consultando métricas do Google Cloud...")
    print()
    
    # Tenta consultar métricas
    consultar_metricas_geocoding()
    
    print()
    print()
    
    # Mostra alternativa
    consultar_via_billing_api()
