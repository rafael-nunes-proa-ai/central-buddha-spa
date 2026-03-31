# import json
# import re
# from pydantic_ai.tools import Tool
# from pydantic_ai import RunContext
# import requests
# import os
# from dotenv import load_dotenv
# from datetime import datetime, timedelta
# from typing import List, Dict, Optional
# import json
# from collections import Counter

# from store.database import delete_session, get_messages, update_context, update_current_agent, get_session, update_current_agent
# from utils import validar_dados
# from utils import resolver_data
# from agents.deps import MyDeps

# load_dotenv()

# #
# # HELPER FUNCTIONS
# #

# def remover_cod_bloq(dados):
#     print("DEBUG remover_cod_bloq - entrada bruta:", json.dumps(dados, ensure_ascii=False))

#     for dia in dados:
#         print(f"DEBUG remover_cod_bloq - dia {dia.get('data')} disp={dia.get('disp')}")

#         for profissional in dia.get('horarios', []):
#             horarios = profissional.get('horarios', [])
#             print(
#                 f"DEBUG remover_cod_bloq - profissional={profissional.get('nome')} "
#                 f"intervalo={profissional.get('tempo_intervalo')} "
#                 f"horarios_originais={[h.get('horario') for h in horarios]}"
#             )

#             for horario in horarios:
#                 horario.pop('cod', None)
#                 horario.pop('bloq', None)

#             total_horarios = int(dia.get('disp', '0').split()[0])
#             intervalo = int(profissional.get('tempo_intervalo', '30'))

#             if horarios:
#                 ultimo_horario_str = horarios[-1]['horario']
#                 ultimo_horario = datetime.strptime(ultimo_horario_str, '%H:%M')

#                 while len(horarios) < total_horarios:
#                     ultimo_horario += timedelta(minutes=intervalo)
#                     novo = {'horario': ultimo_horario.strftime('%H:%M')}
#                     print(
#                         f"DEBUG remover_cod_bloq - ADICIONANDO HORARIO ARTIFICIAL "
#                         f"{novo['horario']} para {profissional.get('nome')}"
#                     )
#                     horarios.append(novo)

#             print(
#                 f"DEBUG remover_cod_bloq - horarios_finais={ [h.get('horario') for h in horarios] }"
#             )

#     return dados

# def encontrar_horarios_validos(horarios: List[Dict[str, str]], intervalo_min: int, duracao_min: int) -> List[str]:
#     try:
#         horarios_dt = sorted([
#             datetime.strptime(h['horario'], '%H:%M') for h in horarios if 'horario' in h
#         ])
#     except Exception as e:
#         print(f"DEBUG encontrar_horarios_validos - erro parsing: {e}")
#         return []

#     print(
#         "DEBUG encontrar_horarios_validos - horarios_recebidos=",
#         [h.strftime('%H:%M') for h in horarios_dt],
#         "intervalo_min=", intervalo_min,
#         "duracao_min=", duracao_min
#     )

#     blocos_validos = []
#     intervalo = timedelta(minutes=intervalo_min)
#     blocos_necessarios = (duracao_min + intervalo_min - 1) // intervalo_min

#     print("DEBUG encontrar_horarios_validos - blocos_necessarios=", blocos_necessarios)

#     for i in range(len(horarios_dt)):
#         bloco = [horarios_dt[i]]
#         for j in range(i + 1, len(horarios_dt)):
#             if horarios_dt[j] == bloco[-1] + intervalo:
#                 bloco.append(horarios_dt[j])
#             else:
#                 break

#         print(
#             "DEBUG encontrar_horarios_validos - bloco_tentado=",
#             [h.strftime('%H:%M') for h in bloco]
#         )

#         if len(bloco) >= blocos_necessarios:
#             blocos_validos.append(bloco[0].strftime('%H:%M'))

#     print("DEBUG encontrar_horarios_validos - blocos_validos=", blocos_validos)
#     return blocos_validos

# def encontrar_horarios_validos_otimizado(horarios: List[Dict[str, str]], intervalo_min: int, duracao_min: int) -> List[str]:
#     """
#     Retorna até os 3 primeiros horários que iniciam blocos contínuos suficientes para a duração desejada,
#     garantindo ao menos 1h de intervalo entre os blocos retornados.

#     Args:
#         horarios (List): Lista de horários retornados pelo Belle Software
#         intervalo_min (int): intervado da agenda em minutos
#         duracao_min (int): tempo da terapia em minutos
#     """
#     try:
#         horarios_dt = sorted([
#             datetime.strptime(h['horario'], '%H:%M') for h in horarios if 'horario' in h
#         ])
#     except Exception:
#         return []  

#     blocos_validos = []
#     intervalo = timedelta(minutes=intervalo_min)
#     blocos_necessarios = (duracao_min + intervalo_min - 1) // intervalo_min
#     ultima_adicao = None

#     for i in range(len(horarios_dt)):
#         bloco = [horarios_dt[i]]
#         for j in range(i + 1, len(horarios_dt)):
#             if horarios_dt[j] == bloco[-1] + intervalo:
#                 bloco.append(horarios_dt[j])
#             else:
#                 break

#         if len(bloco) >= blocos_necessarios:
#             inicio = bloco[0]
#             if ultima_adicao is None or (inicio - ultima_adicao) >= timedelta(hours=1):
#                 blocos_validos.append(inicio.strftime('%H:%M'))
#                 ultima_adicao = inicio

#         if len(blocos_validos) == 3:
#             break

#     return blocos_validos

# def otimizar_horarios(
#     agenda, 
#     duracao_procedimento,
#     duracao_procedimento_min=70
# ):
#     intervalo_min = int(agenda['horarios'][0]['tempo_intervalo'])
    
#     passos_validar = duracao_procedimento // intervalo_min

#     def horarios_otimizados(horarios):
#         horarios = [h for h in horarios if h and isinstance(h, str)]

#         if not horarios:
#             return []

#         horarios_dt = [datetime.strptime(h, "%H:%M") for h in horarios]
#         otimizados = []

#         # 1) Valida sequência de horários que suportam a duração real
#         for i in range(len(horarios_dt)):
#             if i + passos_validar - 1 < len(horarios_dt):
#                 sequencia = horarios_dt[i:i + passos_validar]
#                 is_consecutivos = all(
#                     (sequencia[j + 1] - sequencia[j]) == timedelta(minutes=intervalo_min)
#                     for j in range(len(sequencia) - 1)
#                 )
#                 if is_consecutivos:
#                     otimizados.append(horarios[i])

#         # se não houver nenhum horário realmente válido, retorna vazio
#         if not otimizados:
#             return []

#         # 2) Exibe horários espaçados, mas sempre sobre a lista já validada
#         horarios_finais = []
#         idx = 0
#         count = 0

#         while idx < len(otimizados):
#             count += 1
#             horarios_finais.append(otimizados[idx])

#             current_time = datetime.strptime(otimizados[idx], "%H:%M")
#             next_time = current_time + timedelta(minutes=duracao_procedimento_min)

#             prox_idx = next(
#                 (i for i, h in enumerate(otimizados) if datetime.strptime(h, "%H:%M") >= next_time),
#                 len(otimizados)
#             )

#             if prox_idx < len(otimizados) and prox_idx > 0:
#                 prev_time = datetime.strptime(otimizados[prox_idx - 1], "%H:%M")
#                 next_valid_time = datetime.strptime(otimizados[prox_idx], "%H:%M")

#                 if (next_valid_time - prev_time) > timedelta(minutes=intervalo_min):
#                     ultimo_inicio = prev_time - timedelta(minutes=(duracao_procedimento - 10))

#                     if count >= 4:
#                         penultimo_inicio = prev_time - timedelta(minutes=(70 + duracao_procedimento - 10))

#                         if duracao_procedimento >= 70:
#                             if duracao_procedimento < 130:
#                                 horarios_finais = horarios_finais[:-2]
#                             elif duracao_procedimento < 190:
#                                 horarios_finais = horarios_finais[:-3]
#                             elif duracao_procedimento < 310:
#                                 horarios_finais = horarios_finais[:-4]
#                             else:
#                                 horarios_finais = horarios_finais[:-6]
#                         else:
#                             horarios_finais = horarios_finais[:-1]

#                         if horarios_finais:
#                             horarios_finais.append(penultimo_inicio.strftime("%H:%M"))
#                             horarios_finais.append(ultimo_inicio.strftime("%H:%M"))
#                     else:
#                         if duracao_procedimento >= 70:
#                             horarios_finais = horarios_finais[:-2]
#                             horarios_finais.append(ultimo_inicio.strftime("%H:%M"))
#                         else:
#                             horarios_finais[-1] = ultimo_inicio.strftime("%H:%M")

#                     count = 0

#             idx = prox_idx

#         # 3) Ajuste final do último horário possível, ainda sobre a lista validada
#         if horarios_finais and len(horarios_finais) == 1:
#             return horarios_finais

#         if horarios_finais and len(horarios_finais) > 1:
#             ultimo_disponivel = datetime.strptime(otimizados[-1], "%H:%M")
#             fim_bloco = ultimo_disponivel + timedelta(minutes=intervalo_min)
#             limite_final = (fim_bloco - timedelta(minutes=duracao_procedimento)) + timedelta(minutes=10)

#             if duracao_procedimento >= 70:
#                 if duracao_procedimento < 130:
#                     horarios_finais = horarios_finais[:-1]
#                 elif duracao_procedimento < 190:
#                     horarios_finais = horarios_finais[:-2]
#                 elif duracao_procedimento < 250:
#                     horarios_finais = horarios_finais[:-3]

#             horarios_finais[-1] = limite_final.strftime("%H:%M")

#         return horarios_finais
        
#         if horarios_finais and len(horarios_finais) > 1:
#             ultimo_disponivel = datetime.strptime(horarios[-1], "%H:%M")
#             fim_bloco = ultimo_disponivel + timedelta(minutes=intervalo_min)
#             limite_final = (fim_bloco - timedelta(minutes=duracao_procedimento)) + timedelta(minutes=10)

#             # Último horário gerado
#             dt_ultimo = datetime.strptime(horarios_finais[-1], "%H:%M")
#             diferenca = (limite_final - dt_ultimo).total_seconds() / 60.0
            
#             if duracao_procedimento >= 70:
#                 if duracao_procedimento >= 70 and duracao_procedimento < 130:
#                     horarios_finais = horarios_finais[:-1]
#                 elif duracao_procedimento >= 130 and duracao_procedimento < 190:
#                     horarios_finais = horarios_finais[:-2]
#                 elif duracao_procedimento >= 190 and duracao_procedimento < 250:
#                     horarios_finais = horarios_finais[:-3]
#                 horarios_finais[-1] = limite_final.strftime("%H:%M")
#             else:
#                 horarios_finais[-1] = limite_final.strftime("%H:%M")
                
#             horarios_finais[-1] = limite_final.strftime("%H:%M")
#         # ---------------------------------------------------

#         return horarios_finais

#     nova_agenda = agenda.copy()
#     nova_agenda['horarios'] = []

#     for prof in agenda['horarios']:
#         prof_otimizado = prof.copy()
#         prof_otimizado['horarios'] = horarios_otimizados(prof['horarios'])
#         nova_agenda['horarios'].append(prof_otimizado)

#     return nova_agenda


# def otimizar_horarios_completos(
#     agenda, 
#     duracao_procedimento  # tempo real do procedimento para validar sequência livre
# ):
#     intervalo_min = int(agenda['horarios'][0]['tempo_intervalo'])
#     passos_validar = duracao_procedimento // intervalo_min
    
#     def horarios_otimizados(horarios):
#         # Filtra apenas horários realmente disponíveis (descarta None, '', '-', etc.)
#         horarios = [h for h in horarios if h and isinstance(h, str)]
        
#         horarios_dt = [datetime.strptime(h, "%H:%M") for h in horarios]
#         otimizados = []
        
#         for i in range(len(horarios_dt)):
#             # Pega a sequência que deveria cobrir a duração do procedimento
#             if i + passos_validar - 1 < len(horarios_dt):
#                 sequencia = horarios_dt[i:i+passos_validar]
                
#                 # Verifica se todos são consecutivos e não têm buracos
#                 is_consecutivos = all(
#                     (sequencia[j+1] - sequencia[j]) == timedelta(minutes=intervalo_min)
#                     for j in range(len(sequencia) - 1)
#                 )
                
#                 if is_consecutivos:
#                     otimizados.append(horarios[i])
        
#         return otimizados
    
#     nova_agenda = agenda.copy()
#     nova_agenda['horarios'] = []
    
#     for prof in agenda['horarios']:
#         prof_otimizado = prof.copy()
#         prof_otimizado['horarios'] = horarios_otimizados(prof['horarios'])
#         nova_agenda['horarios'].append(prof_otimizado)
    
#     return nova_agenda

# def filtrar_por_data(dados, data):
#     """
#     Retorna uma lista contendo os objetos de 'dados' que possuem a data informada.

#     Args:
#         dados (list): Lista de dicionários (cada um representando um dia).
#         data (str): Data no formato 'dd/mm/yyyy'.

#     Returns:
#         list: Lista com os objetos cuja data corresponde à informada.
#     """
#     agenda_filtrada = [dia for dia in dados if dia.get('data') == data]
#     return agenda_filtrada

# def simplificar_horarios(dados_do_dia):
#     """
#     Simplifica a estrutura dos horários para conter apenas strings de horários por profissional,
#     mantendo a estrutura original do dia.

#     Args:
#         dados_do_dia (list): Lista contendo um único dicionário representando um dia.

#     Returns:
#         dict: Estrutura do dia com os horários simplificados por profissional.
#     """
#     if not dados_do_dia:
#         return {}

#     dia = dados_do_dia[0]
#     novos_profissionais = []

#     for profissional in dia.get('horarios', []):
#         horarios_strings = [h.get('horario') for h in profissional.get('horarios', [])]
        
#         novos_profissionais.append({
#             'codProf': profissional.get('codProf'),
#             'tempo_intervalo': profissional.get('tempo_intervalo'),
#             'nome': profissional.get('nome'),
#             'horarios': horarios_strings
#         })
#     agenda = {
#         'nome': dia.get('nome'),
#         'data': dia.get('data'),
#         'disp': dia.get('disp'),
#         'horarios': novos_profissionais
#     }
#     return agenda


# #
# # TOOLS
# #

# @Tool
# def consult_categorias() -> str:
#     """Retorna uma lista contendo todas as categorias de terapia disponíveis no Buddha Spa.

#     Returns:
#         str: JSON string com as categorias disponíveis
#     """
#     url = "https://app.bellesoftware.com.br/api/release/controller/IntegracaoExterna/v1.0/servicos/categorias_servico?codigoCategoria=&nomeCategoria="
#     payload = {}
#     headers = {
#         'Authorization': os.getenv("LABELLE_TOKEN")
#     }

#     try:
#         response = requests.get(url, headers=headers, data=payload)
#         response.raise_for_status()

#         # Parse o JSON para validar se está correto
#         data = response.json()
#         #print(f"Categorias retornadas: {data}")

#         return json.dumps(data, ensure_ascii=False)
#     except Exception as e:
#         print(f"Erro ao consultar categorias: {e}")
#         return json.dumps({"erro": "Não foi possível consultar as categorias no momento"})

# @Tool
# def consult_terapias(codCategoria: int ) -> list:
#     """Retorna uma lista de terapias disponíveis para uma categoria específica no Buddha Spa.
#        Só usar quando o usuário escolher uma categoria de terapia.
        
#     Args:
#         codCategoria (int): The category code for which to retrieve therapies.

#     Returns:
#         list: list of available therapies.
#     """

#     url = f'https://app.bellesoftware.com.br/api/release/controller/IntegracaoExterna/v1.0/servico/listar?codPlano=&codProf=&codSala=&filtro=&codCategoria={codCategoria}&codTipo='

#     payload = {}
#     headers = {
#     'Authorization': os.getenv("LABELLE_TOKEN")
#     }

#     response = requests.request("GET", url, headers=headers, data=payload)

#     if response.status_code != 200:
#         raise Exception(f"Erro na requisição: {response.status_code} - {response.text}")

#     dados = response.json()    

#     # Função para limpar o nome
#     def limpar_nome(nome):
#         nome = re.sub(r'\d+', '', nome)  
#         nome = nome.replace(' Dom', '')  
#         nome = nome.replace(' DOM', '')  
#         return nome.strip()              

#     for item in dados:
#         item['nome_terapia'] = limpar_nome(item.get('nome', ''))

#     #print(f"Terapias retornadas: {dados}")

#     return json.dumps(dados, ensure_ascii=False)

# @Tool
# def consult_terapeutas() ->  list:
#     """Retorna uma lista de terapeutas disponíveis no Buddha Spa.
#     Esta ferramenta só deve ser chamada de o usuário precisar escolher um terapeuta específico.
    
#     Returns:
#         list: Lista de terapeutas disponíveis
#     """
#     url = "https://app.bellesoftware.com.br/api/release/controller/IntegracaoExterna/v1.0/usuario/listar?codEstab=1&usuario&possuiAgenda=1"
#     payload = {}
#     headers = {
#         'Authorization': os.getenv("LABELLE_TOKEN")
#     }

#     try:
#         response = requests.get(url, headers=headers, data=payload)
#         response.raise_for_status()
        
#         # Parse o JSON para validar se está correto
#         data = response.json()
#         #print(f"Terapeutas retornados: {data}")
        
#         return json.dumps(data, ensure_ascii=False)
#     except Exception as e:
#         print(f"Erro ao consultar terapeutas: {e}")
#         return json.dumps({"erro": "Não foi possível consultar os terapeutas no momento"})

# @Tool
# def consulta_terapeutas_por_terapia(
#     codigo_servico: str,
#     dtAgenda: str,
#     periodo: str
#     ) -> list:
#     """Retorna uma lista de terapeutas disponíveis para uma terapia especifica.
#     Só utilizar depois de perguntar se o usuário tem terapeuta preferêncial e responder que sim.

#     Args:
#         codigo_servico (str): código do serviço da terapia
#         dtAgenda (str): data preferência para agendamento no formato 'DD/MM/AAAA'
#         periodo (str): periodo do dia 'manha', 'tarde' ou 'noite', caso o usuario não escolher deve o valor padrão é 'todos'

#     Returns:
#         list: Lista de terapeutas disponíveis
#     """

#     tpAgd = "p"
#     periodo = periodo
#     dtAgenda = dtAgenda

#     url = f'https://app.bellesoftware.com.br/api/release/controller/IntegracaoExterna/v1.0/agenda/disponibilidade?codEstab=1&dtAgenda={dtAgenda}&periodo={periodo}&tpAgd={tpAgd}&servicos={codigo_servico}'
#     payload = {}
#     headers = {
#         'Authorization': os.getenv("LABELLE_TOKEN")
#     }

#     try:
#         print(
#             f"DEBUG TERAPEUTAS POR TERAPIA - codigo_servico={codigo_servico} "
#             f"dtAgenda={dtAgenda} periodo={periodo}"
#         )

#         response = requests.get(url, headers=headers, data=payload)
#         response.raise_for_status()

#         agendas = response.json()
#         print("DEBUG TERAPEUTAS POR TERAPIA - agendas_brutas:", json.dumps(agendas, ensure_ascii=False))

#         for agenda in agendas:
#             if agenda.get("data") == dtAgenda:
#                 terapeutas = []
#                 for terapeuta in agenda.get("horarios", []):
#                     terapeutas.append({
#                         "nome": terapeuta.get("nome"),
#                         "codProf": terapeuta.get("codProf")
#                     })

#                 print("DEBUG TERAPEUTAS POR TERAPIA - terapeutas_filtrados:", json.dumps(terapeutas, ensure_ascii=False))
#                 return json.dumps(terapeutas, ensure_ascii=False)

#         print("DEBUG TERAPEUTAS POR TERAPIA - data nao encontrada na agenda")
#         return []

#     except Exception as e:
#         print(f"Erro ao consultar terapeutas: {e}")
#         return json.dumps({"erro": "Não foi possível consultar os terapeutas no momento"})

# @Tool
# def consult_agenda(dtAgenda: str, periodo: str, duracao: str) -> list:
#     """Retorna uma lista de horários disponíveis para agendamento no Buddha Spa para cada terapeuta.

#     Args:
#         dtAgenda (str): data preferência para agendamento no formato 'DD/MM/AAAA'
#         periodo (str): período do dia para o agendamento (manhã, tarde, noite ou todos)
#         duracao (str): tempo da terapia em minutos
#     Returns:
#         list: Lista de horários disponíveis para agendamento
#     """
    
#     url = f'https://app.bellesoftware.com.br/api/release/controller/IntegracaoExterna/v1.0/agenda/disponibilidade?codEstab=1&dtAgenda={dtAgenda}&periodo={periodo}&tpAgd=p'
#     payload = {}
#     headers = {
#         'Authorization': os.getenv("LABELLE_TOKEN")
#     }
#     def fetch_and_process():
#         resp = requests.get(url, headers=headers, data=payload)
#         resp.raise_for_status()
#         return remover_cod_bloq(resp.json())

#     try:
#         terapeutas = fetch_and_process()
#         #print(f"Horários disponíveis: {terapeutas}")

#         if not terapeutas:
#             hoje = datetime.today()
#             dias_ate_domingo = (6 - hoje.weekday()) % 7 or 7
#             print(f"Sem terapeutas disponíveis. Reconsultando (dias até domingo: {dias_ate_domingo})")

#             terapeutas = fetch_and_process()
#             print(f"Terapeutas retornados na segunda tentativa: {terapeutas}")
            
#         resultado = []

#         for dia in terapeutas:
#             for profissional in dia.get("horarios", []):
#                 intervalo = int(profissional.get("tempo_intervalo", "30"))
#                 horarios = profissional.get("horarios", [])
                
#                 horarios_validos = encontrar_horarios_validos(
#                     horarios,
#                     intervalo_min=intervalo,
#                     duracao_min=int(duracao)
#                 )

#                 resultado.append({
#                     "data": dia["data"],
#                     "dia_semana": dia["nome"],
#                     "profissional": profissional["nome"],
#                     "horarios_validos": horarios_validos
#                 })
                
#         print(f"Horários válidos encontrados: {resultado}")

#         return json.dumps(resultado, ensure_ascii=False)
#     except Exception as e:
#         print(f"Erro ao consultar terapeutas: {e}")
#         return json.dumps({"erro": "Não foi possível consultar agendas disponíveis no momento"})

# @Tool
# def consultar_agenda_otimizada(codServico: int, dtAgenda: str, terapeuta: str, duracao: str) -> str:
#     """Retorna uma lista otimizada de horários disponíveis para agendamento no Buddha Spa.
#        Não retorna agenda para terapias específicas.
#        NUNCA utilizar antes de perguntar se o usuário tem terapeuta preferêncial.

#     Args:
#         codServico (int): Código da terapia selecionada
#         dtAgenda (str): data preferência para agendamento no formato 'DD/MM/AAAA'
#         terapeuta (str): nome do terapeuta, caso não tenha, deve ser 'null'
#         duracao (str): tempo da terapia em minutos

#     Returns:
#         str: JSON string com horários disponíveis para agendamento
#     """

#     url = (
#         "https://app.bellesoftware.com.br/api/release/controller/"
#         f"IntegracaoExterna/v1.0/agenda/disponibilidade?codEstab=1&dtAgenda={dtAgenda}"
#         f"&periodo=todos&tpAgd=p&servicos={codServico}"
#     )

#     headers = {
#         "Authorization": os.getenv("LABELLE_TOKEN")
#     }

#     try:
#         resp = requests.get(url, headers=headers)
#         resp.raise_for_status()
#         agendas = resp.json()

#         print("DEBUG consultar_agenda_otimizada - agendas_brutas:", json.dumps(agendas, ensure_ascii=False))

#         agenda_filtrada = filtrar_por_data(agendas, dtAgenda)
#         print("DEBUG consultar_agenda_otimizada - agenda_filtrada:", json.dumps(agenda_filtrada, ensure_ascii=False))

#         if not agenda_filtrada:
#             return json.dumps({"erro": "Não encontramos agenda para a data informada."}, ensure_ascii=False)

#         dia = agenda_filtrada[0]

#         resultado = {
#             "dia_semana": dia.get("nome"),
#             "data": dia.get("data"),
#             "disp": dia.get("disp"),
#             "horarios": []
#         }

#         for profissional in dia.get("horarios", []):
#             intervalo = int(profissional.get("tempo_intervalo", "10"))
#             horarios_api = profissional.get("horarios", [])

#             horarios_validos = encontrar_horarios_validos_otimizado(
#                 horarios=horarios_api,
#                 intervalo_min=intervalo,
#                 duracao_min=int(duracao) + 10
#             )

#             resultado["horarios"].append({
#                 "codProf": profissional.get("codProf"),
#                 "tempo_intervalo": profissional.get("tempo_intervalo"),
#                 "nome": profissional.get("nome"),
#                 "horarios": horarios_validos
#             })

#         print("DEBUG consultar_agenda_otimizada - resultado_final:", json.dumps(resultado, ensure_ascii=False))
#         return json.dumps(resultado, ensure_ascii=False)

#     except Exception as e:
#         print(f"Erro ao consultar terapeutas: {e}")
#         return json.dumps({"erro": "Não foi possível consultar agendas disponíveis no momento"}, ensure_ascii=False)

# @Tool
# def consultar_agenda_completa(codServico: int, dtAgenda: str, terapeuta: str, codProf: str, duracao: str):
#     """Retorna uma lista com todos os horários disponíveis para agendamento.
#        Utilizar quando o usuário solicitar um horário diferente do apresentado pela Tool consultar_agenda_otimizada.

#     Args:
#         codServico (int): Código da terapia selecionada
#         dtAgenda (str): data preferência para agendamento no formato 'DD/MM/AAAA'
#         terapeuta (str): nome do terapeuta, campo obrigatório
#         codProf (str) : código do terapeuta escolhido, campo obrigatório
#         duracao (str): tempo daterapia em minutos

#     Returns:
#         object: Lista de horários disponíveis para agendamento
#     """
#     codServico = codServico
#     tpAgd = "p"  # if terapeuta == "null" else "p"
#     periodo = 'todos'
#     dtAgenda = dtAgenda
#     nome_terapeuta = terapeuta
    
#     url = f'https://app.bellesoftware.com.br/api/release/controller/IntegracaoExterna/v1.0/agenda/disponibilidade?codEstab=1&dtAgenda={dtAgenda}&periodo={periodo}&tpAgd={tpAgd}&servicos={codServico}'
#     payload = {}
#     headers = {
#         'Authorization': os.getenv("LABELLE_TOKEN")
#     }
#     try:
#         resp = requests.get(url, headers=headers, data=payload)
#         resp.raise_for_status()
#         agendas = resp.json()
#         agenda_completa_simplificada = simplificar_horarios(filtrar_por_data(agendas, dtAgenda))        
#         agenda_otimizada = otimizar_horarios_completos(agenda_completa_simplificada, int(duracao)+10)
#         filtrados = [
#             prof for prof in agenda_otimizada['horarios']
#             if str(prof.get('codProf')) == str(codProf)
#         ]
#         print(
#             f"DEBUG consultar_agenda_completa - codServico={codServico} dtAgenda={dtAgenda} "
#             f"terapeuta={terapeuta} codProf={codProf} duracao={duracao}"
#         )

#         print("DEBUG consultar_agenda_completa - agendas_brutas:", json.dumps(agendas, ensure_ascii=False))
#         print("DEBUG consultar_agenda_completa - agenda_simplificada:", json.dumps(agenda_completa_simplificada, ensure_ascii=False))
#         print("DEBUG consultar_agenda_completa - agenda_otimizada:", json.dumps(agenda_otimizada, ensure_ascii=False))
#         print("DEBUG consultar_agenda_completa - filtrados:", json.dumps(filtrados, ensure_ascii=False))
#         if filtrados:
#             return filtrados[0]
#         else:
#             return "Não encontramos nenhuma agenda para esta data e terapeuta específicos"
        
#     except Exception as e:
#         print(f"Erro ao consultar terapeutas: {e}")
#         return json.dumps({"erro": "Não foi possível consultar agendas disponíveis no momento"})

# def _valor_util_transferencia(valor: str | None) -> bool:
#     if valor is None:
#         return False

#     valor_limpo = str(valor).strip().lower()

#     placeholders = {
#         "",
#         "none",
#         "null",
#         "não informado",
#         "nao informado",
#         "000.000.000-00",
#         "(00) 00000-0000",
#         "naoinformado@buddha.com",
#     }

#     return valor_limpo not in placeholders

# @Tool
# def agente_cadastro(
#     conversation_id: str, 
#     codigo_categoria: str, 
#     terapia: str, 
#     duracao: int, 
#     terapeuta: str, 
#     codigo_terapeuta: int, 
#     data: str, 
#     dia_semana: str, 
#     horario: str,
#     codigo_servico: str,
#     nome_servico: str,
#     label_servico: str,
#     valor_servico: str,
#     nome: str | None = None,
#     cpf: str | None = None,
#     celular: str | None = None,
#     email: str | None = None,
#     data_nascimento: str | None = None,
#     genero: str | None = None
# ) -> str:
#     """Transfere para o agente de cadastro de usuário."""

#     session = get_session(conversation_id)
#     context_atual = session[2] or {}

#     if isinstance(context_atual, str):
#         context_atual = context_atual.strip()
#         if context_atual == "" or context_atual.lower() == "none":
#             context_atual = {}
#         else:
#             try:
#                 context_atual = json.loads(context_atual)
#             except Exception:
#                 context_atual = {}

#     def priorizar_contexto(chave: str, valor_novo):
#         valor_contexto = context_atual.get(chave)

#         if _valor_util_transferencia(valor_contexto):
#             return valor_contexto

#         if _valor_util_transferencia(valor_novo):
#             return valor_novo

#         return valor_contexto or valor_novo

#     data_dict = {
#         "codigo_categoria": codigo_categoria,
#         "terapia": terapia,
#         "duracao": duracao,
#         "terapeuta": terapeuta,
#         "codigo_terapeuta": codigo_terapeuta,
#         "data": data,
#         "dia_semana": dia_semana,
#         "horario": horario,
#         "codigo_servico": codigo_servico,
#         "nome_servico": nome_servico,
#         "label_servico": label_servico,
#         "valor_servico": valor_servico,

#         # prioridade total para o que já veio do get_user / contexto
#         "nome": priorizar_contexto("nome", nome),
#         "cpf": priorizar_contexto("cpf", cpf),
#         "celular": priorizar_contexto("celular", celular),
#         "email": priorizar_contexto("email", email),

#         # para estes dois, mantém o que já existe se vier vazio
#         "data_nascimento": context_atual.get("data_nascimento") if not data_nascimento else data_nascimento,
#         "genero": context_atual.get("genero") if not genero else genero,
#     }

#     print("DEBUG agente_cadastro - contexto_atual:", context_atual)
#     print("DEBUG agente_cadastro - entrada_tool:", {
#         "nome": nome,
#         "cpf": cpf,
#         "celular": celular,
#         "email": email,
#         "data_nascimento": data_nascimento,
#         "genero": genero,
#     })
#     print("DEBUG agente_cadastro - data_final:", data_dict)

#     update_context(conversation_id, data_dict)
#     update_current_agent(conversation_id, "cadastro_agent")

#     return (
#         "Para prosseguir com o agendamento, primeiro confirme se o atendimento será para o próprio usuário "
#         "ou para outra pessoa. "
#         "Se for para outra pessoa, solicite o número de celular dessa pessoa e siga com a identificação dela. "
#         "Se o usuário confirmar que o atendimento é para ele mesmo, consulte o cadastro pelo celular informado "
#         "e verifique quais campos estão faltando entre nome, CPF, celular, email, data de nascimento e gênero. "
#         "Se faltar algum campo, peça educadamente apenas os campos faltantes, um por vez, atualize o cadastro "
#         "e o contexto, e só depois continue o fluxo. "
#         "Se não faltar nada, mostre os dados principais já cadastrados e pergunte se o usuário deseja alterar algo. "
#         "Quando o cadastro estiver confirmado, siga para o voucher."
#     )

# @Tool
# def agente_voucher(
#     conversation_id: str,
#     codigo_usuario: str,
#     nome: str,
#     cpf: str,
#     celular: str,
#     email: str,
#     data_nascimento: str | None = None,
#     genero: str | None = None
# ) -> str:
#     """Transfere para o agente de validação de voucher."""

#     # Recupera contexto atual para não sobrescrever valores válidos com None
#     session = get_session(conversation_id)
#     context_atual = session[2] or {}

#     if isinstance(context_atual, str):
#         context_atual = context_atual.strip()
#         if context_atual == "" or context_atual.lower() == "none":
#             context_atual = {}
#         else:
#             try:
#                 context_atual = json.loads(context_atual)
#             except Exception:
#                 context_atual = {}

#     # fallback para os valores já existentes no contexto
#     if not data_nascimento:
#         data_nascimento = context_atual.get("data_nascimento")

#     if not genero:
#         genero = context_atual.get("genero")

#     print("DEBUG agente_voucher - data_nascimento:", data_nascimento)
#     print("DEBUG agente_voucher - genero:", genero)

#     if not codigo_usuario or str(codigo_usuario).strip().lower() in ("null", "none", ""):
#         print("Cadastrando usuário novo...")
#         url = 'https://app.bellesoftware.com.br/api/release/controller/IntegracaoExterna/v1.0/cliente/gravar'
#         headers = {
#             'Authorization': os.getenv("LABELLE_TOKEN"),
#             'Content-Type': 'application/json'
#         }
#         payload = {
#             "nome": nome,
#             "ddiCelular": "+55",
#             "celular": celular,
#             "email": email,
#             "cpf": cpf,
#             "observacao": "Cadastro realizado via WhatsApp",
#             "tpOrigem": "WhatsApp",
#             "codOrigem": "99",
#             "codEstab": 1
#         }
#         try:
#             response = requests.post(url, headers=headers, json=payload)
#             response.raise_for_status()
#             codigo_usuario = response.json().get("codigo")

#             if codigo_usuario and (data_nascimento or genero):
#                 resultado_complemento = complementar_cadastro_cliente(
#                     conversation_id=conversation_id,
#                     codigo_usuario=int(codigo_usuario),
#                     data_nascimento=data_nascimento,
#                     genero=genero
#                 )
#                 print(f"Resultado complemento cadastro: {resultado_complemento}")

#         except Exception as e:
#             print(f"Erro ao realizar o cadastro: {e}")
#             return "Pergunte se o usuário possui algum voucher, plano (pacote) ou vale bem-estar antes de concluir o agendamento" 
#     # Só atualiza o que realmente tem valor
#     data = {
#         "codigo_usuario": codigo_usuario,
#         "nome": nome,
#         "cpf": cpf,
#         "celular": celular,
#         "email": email,
#     }

#     if data_nascimento:
#         data["data_nascimento"] = data_nascimento

#     if genero:
#         data["genero"] = genero

#     update_context(conversation_id, data)
#     update_current_agent(conversation_id, "voucher_agent")

#     print("Cadastro do usuário concluído, pergunte se o usuário possui algum voucher.")
#     return "Pergunte se o usuário possui algum voucher antes de concluir o agendamento"

# CAMPOS_CADASTRO_OBRIGATORIOS = [
#     "nome",
#     "cpf",
#     "celular",
#     "email",
#     "data_nascimento",
#     "genero",
# ]

# def _valor_preenchido(valor) -> bool:
#     if valor is None:
#         return False

#     if isinstance(valor, str):
#         valor_limpo = valor.strip().lower()

#         if valor_limpo in ("", "null", "none"):
#             return False

#         # placeholders comuns da Belle para data vazia
#         if valor_limpo in ("0000-00-00", "00/00/0000"):
#             return False

#     return True

# def _somente_numeros(valor: str | None) -> str | None:
#     if valor is None:
#         return None

#     numeros = re.sub(r"\D", "", str(valor))
#     return numeros or None

# def _normalizar_cliente_belle(data, celular_consultado: str | None = None) -> dict:
#     """
#     Normaliza o retorno da Belle para o formato do contexto/MyDeps.
#     Aceita retorno em dict ou list.
#     """
#     registro = None

#     if isinstance(data, list):
#         if data:
#             registro = data[0]

#     elif isinstance(data, dict):
#         if isinstance(data.get("data"), list) and data["data"]:
#             registro = data["data"][0]
#         elif isinstance(data.get("cliente"), dict):
#             registro = data["cliente"]
#         elif any(
#             chave in data
#             for chave in [
#                 "codigo",
#                 "codCliente",
#                 "codCli",
#                 "cod",
#                 "nome",
#                 "cpf",
#                 "celular",
#                 "email",
#                 "dataNascimento",
#                 "data_nascimento",
#                 "dtNascimento",
#                 "genero",
#                 "sexo",
#             ]
#         ):
#             registro = data

#     if not isinstance(registro, dict):
#         return {}

#     return {
#         "codigo_usuario": registro.get("codigo")
#             or registro.get("codCliente")
#             or registro.get("codCli")
#             or registro.get("cod")
#             or registro.get("codigo_usuario"),
#         "nome": registro.get("nome"),
#         "cpf": _somente_numeros(registro.get("cpf")),
#         "celular": _somente_numeros(
#             registro.get("celular")
#             or registro.get("telefoneCelular")
#             or celular_consultado
#         ),
#         "email": registro.get("email"),
#         "data_nascimento": (
#             registro.get("dataNascimento")
#             or registro.get("data_nascimento")
#             or registro.get("dtNascimento")
#         ),
#         "genero": registro.get("genero") or registro.get("sexo"),
#     }

# def verificar_campos_faltantes_cadastro(dados_cliente: dict) -> dict:
#     """
#     Recebe os dados normalizados do cliente e devolve quais campos
#     obrigatórios estão faltando no cadastro.
#     """
#     dados_normalizados = {
#         "codigo_usuario": dados_cliente.get("codigo_usuario"),
#         "nome": dados_cliente.get("nome"),
#         "cpf": _somente_numeros(dados_cliente.get("cpf")),
#         "celular": _somente_numeros(dados_cliente.get("celular")),
#         "email": dados_cliente.get("email"),
#         "data_nascimento": (
#             None
#             if (dados_cliente.get("data_nascimento") or dados_cliente.get("dataNascimento") or dados_cliente.get("dtNascimento")) in ["0000-00-00", "00/00/0000", "", None]
#             else (
#                 dados_cliente.get("data_nascimento")
#                 or dados_cliente.get("dataNascimento")
#                 or dados_cliente.get("dtNascimento")
#             )
#         ),
#         "genero": (
#             None
#             if (dados_cliente.get("genero") or dados_cliente.get("sexo")) in ["", None]
#             else (dados_cliente.get("genero") or dados_cliente.get("sexo"))
#         ),
#     }

#     campos_faltantes = [
#         campo
#         for campo in CAMPOS_CADASTRO_OBRIGATORIOS
#         if not _valor_preenchido(dados_normalizados.get(campo))
#     ]

#     campos_preenchidos = [
#         campo
#         for campo in CAMPOS_CADASTRO_OBRIGATORIOS
#         if campo not in campos_faltantes
#     ]

#     return {
#         "dados_cliente": dados_normalizados,
#         "campos_faltantes": campos_faltantes,
#         "campos_preenchidos": campos_preenchidos,
#         "cadastro_completo": len(campos_faltantes) == 0,
#     }

# @Tool
# def consult_cadastro(celular: str, conversation_id: str | None = None) -> dict:
#     """Verifica se o número de celular já está cadastrado no sistema.

#     Além de consultar a Belle, esta função normaliza os dados do cliente e
#     já informa claramente quais campos obrigatórios do cadastro estão faltando.

#     Args:
#         celular (str): Número de celular a ser verificado.
#         conversation_id (str | None): ID da conversa atual, para sincronizar o contexto.

#     Returns:
#         dict: Resultado padronizado da consulta.
#     """
#     url = f'https://app.bellesoftware.com.br/api/release/controller/IntegracaoExterna/v1.0/cliente/listar?codEstab=1&celular={celular}'
#     headers = {
#         'Authorization': os.getenv("LABELLE_TOKEN")
#     }

#     resultado_vazio = {
#         "encontrado": False,
#         "dados_cliente": {},
#         "campos_faltantes": CAMPOS_CADASTRO_OBRIGATORIOS.copy(),
#         "campos_preenchidos": [],
#         "cadastro_completo": False
#     }

#     try:
#         response = requests.get(url, headers=headers)
#         response.raise_for_status()

#         data = response.json()
#         print(f"Resultado bruto da consulta de cadastro: {data}")

#         dados_cliente = _normalizar_cliente_belle(data, celular_consultado=celular)

#         if not dados_cliente:
#             print("Cadastro não encontrado na Belle.")
#             return resultado_vazio

#         analise = verificar_campos_faltantes_cadastro(dados_cliente)

#         resultado = {
#             "encontrado": True,
#             **analise
#         }

#         # Atualiza o contexto somente com os valores realmente preenchidos
#         # para não sobrescrever contexto válido com None
#         if conversation_id:
#             context_update = {
#                 chave: valor
#                 for chave, valor in analise["dados_cliente"].items()
#                 if _valor_preenchido(valor)
#             }
#             context_update["campos_faltantes"] = analise["campos_faltantes"]
#             context_update["cadastro_completo"] = analise["cadastro_completo"]

#             update_context(conversation_id, context_update)

#         print(f"Resultado padronizado da consulta de cadastro: {resultado}")
#         return resultado

#     except Exception as e:
#         print(f"Erro ao consultar cadastro: {e}")
#         return {
#             "erro": "Não foi possível consultar o cadastro no momento",
#             **resultado_vazio
#         }
    
# @Tool
# def delete_conversation(conversation_id: str) -> str:
#     """Deleta uma sessão de conversa e encerra a conversa.

#     Args:
#         conversation_id (str): ID da conversa a ser deletada.

#     Returns:
#         str: Mensagem de confirmação ou erro.
#     """
#     try:
#         delete_session(conversation_id)
#         print(f"Sessão {conversation_id} deletada com sucesso.")
#         return "Sessão deletada com sucesso."
#     except Exception as e:
#         print(f"Erro ao deletar sessão: {e}")
#         return f"Erro ao deletar sessão: {e}"
    
# @Tool
# def validar_voucher_ou_vale(ctx: RunContext[MyDeps], codigo_voucher: str, data_agendamento: str) -> str:
#     """
#     Valida um voucher ou vale bem-estar.

#     Nova regra:
#     - item preenchido -> voucher
#     - item vazio -> vale bem-estar
#     """
#     conversation_id = ctx.deps.session_id
#     print("=" * 80)
#     print("DEBUG VALIDAR_VOUCHER_OU_VALE - INÍCIO")
#     print(f"Conversation ID: {conversation_id}")
#     print(f"Código voucher: {codigo_voucher}")
#     print(f"Data agendamento recebida: {data_agendamento}")
#     print(f"Tipo da data: {type(data_agendamento)}")
#     print("=" * 80)

#     url = f'https://app.bellesoftware.com.br/api/release/controller/IntegracaoExterna/v1.0/voucher/unico?codVoucher={codigo_voucher}'
#     headers = {
#         'Authorization': os.getenv("LABELLE_TOKEN")
#     }

#     try:
#         response = requests.get(url, headers=headers)
#         response.raise_for_status()
#         data = response.json()

#         print(f"Resultado da validação API: {data}")

#         if not isinstance(data, dict):
#             return "❌ Erro ao validar código."

#         status = data.get("status", "").lower()

#         # Puxa o tipo e item
#         tipo_api = data.get("tipo", "")
#         item = data.get("item")

#         # REGRA: tipo="Serviços" ou "Servicos" → voucher (terapia predefinida)
#         #        tipo="Geral" → vale bem-estar (valor para gastar)
#         # Normaliza removendo acentos para comparação
#         import unicodedata
#         tipo_normalizado = unicodedata.normalize('NFD', tipo_api).encode('ascii', 'ignore').decode('utf-8').lower()
#         is_voucher = tipo_normalizado == "servicos"
#         tipo_label = "voucher" if is_voucher else "vale bem-estar"
        
#         print(f"DEBUG - Tipo API: {tipo_api}")
#         print(f"DEBUG - Tipo normalizado: {tipo_normalizado}")
#         print(f"DEBUG - Is voucher: {is_voucher}")
#         print(f"DEBUG - Tipo label: {tipo_label}")

#         # Validação de status
#         if status not in ["em aberto", "válido", "validado"]:
#             return f"❌ {tipo_label.title()} inválido ou expirado. Status: {data.get('status')}"

#         # Validação de data
#         vencimento_fim = data.get("vencimentoFim")
#         if not vencimento_fim:
#             return f"⚠️ {tipo_label.title()} sem data de vencimento."

#         print(f"DEBUG - Vencimento fim (API): {vencimento_fim}")
#         print(f"DEBUG - Data agendamento (param): {data_agendamento}")
        
#         try:
#             dt_vencimento_fim = datetime.strptime(vencimento_fim, "%d/%m/%Y").date()
#             print(f"DEBUG - dt_vencimento_fim parseado: {dt_vencimento_fim}")
#         except Exception as e:
#             print(f"ERRO ao parsear vencimento_fim: {e}")
#             return f"❌ Erro ao processar data de vencimento: {vencimento_fim}"
        
#         try:
#             dt_agendamento = datetime.strptime(data_agendamento, "%d/%m/%Y").date()
#             print(f"DEBUG - dt_agendamento parseado: {dt_agendamento}")
#         except Exception as e:
#             print(f"ERRO ao parsear data_agendamento: {e}")
#             return f"❌ Erro ao processar data de agendamento: {data_agendamento}"

#         # Dados comuns
#         valor = data.get("valor", "0,00")
#         tipo_valor = data.get("tipoValor", "")
#         validade = f"{data.get('vencimentoIni')} até {vencimento_fim}"
#         msg = data.get("msg", "")

#         # Verifica se está vencido
#         voucher_vencido = dt_agendamento > dt_vencimento_fim
#         print(f"DEBUG - Voucher vencido? {voucher_vencido} (agendamento: {dt_agendamento} > vencimento: {dt_vencimento_fim})")
#         print("=" * 80)

#         # 🔥 Diferença principal (baseada no item)
#         if is_voucher:
#             terapia = item.get("nome", "Desconhecido")

#             # VOUCHER VENCIDO - Mensagem especial
#             if voucher_vencido:
#                 return (
#                     f"⚠️ <strong>Este voucher está fora do prazo de validade.</strong> 🤔\n\n"
#                     f"<strong>Terapia do voucher:</strong> {terapia}\n"
#                     f"<strong>Validade:</strong> {validade}\n\n"
#                     f"Se você o adquiriu pelo site, será necessário revalidá-lo no site para utilizá-lo.\n"
#                     f"Se você o adquiriu na unidade, será necessário realizar o pagamento da diferença diretamente na unidade no dia do atendimento.\n\n"
#                     f"Você pode continuar com o agendamento, mas a utilização do voucher ficará condicionada a essa regularização.\n\n"
#                     f"<strong>Deseja continuar com o agendamento mesmo assim?</strong>"
#                 )

#             # VOUCHER VÁLIDO - Armazena tipo_beneficio e terapia
#             update_context(conversation_id, {
#                 "tipo_beneficio": "voucher",
#                 "terapia": terapia
#             })
#             print(f"DEBUG - Contexto atualizado: tipo_beneficio=voucher, terapia={terapia}")
            
#             # Atualiza ctx.deps para refletir as mudanças
#             ctx.deps.tipo_beneficio = "voucher"
#             ctx.deps.terapia = terapia
#             print(f"DEBUG - ctx.deps atualizado: tipo_beneficio={ctx.deps.tipo_beneficio}, terapia={ctx.deps.terapia}")
            
#             return (
#                 f"✅ <strong>Voucher válido!</strong>\n"
#                 f"<strong>Terapia:</strong> {terapia}\n"
#                 f"<strong>Valor:</strong> {valor} {tipo_valor}\n"
#                 f"<strong>Validade:</strong> {validade}\n"
#                 f"Mensagem: {msg}"
#             )

#         else:
#             # VALE BEM-ESTAR VENCIDO
#             if voucher_vencido:
#                 return (
#                     f"⚠️ <strong>Este vale está fora do prazo de validade.</strong> 🤔\n\n"
#                     f"<strong>Valor disponível:</strong> {valor} {tipo_valor}\n"
#                     f"<strong>Validade:</strong> {validade}\n\n"
#                     f"Para utilizá-lo, será necessário o pagamento de uma diferença diretamente na unidade no dia do atendimento.\n\n"
#                     f"<strong>Deseja continuar com o agendamento mesmo assim?</strong>"
#                 )

#             # VALE BEM-ESTAR VÁLIDO - Armazena tipo_beneficio (sem terapia, será escolhida depois)
#             update_context(conversation_id, {
#                 "tipo_beneficio": "vale"
#             })
#             print(f"DEBUG - Contexto atualizado: tipo_beneficio=vale")
            
#             # Atualiza ctx.deps para refletir as mudanças
#             ctx.deps.tipo_beneficio = "vale"
#             print(f"DEBUG - ctx.deps atualizado: tipo_beneficio={ctx.deps.tipo_beneficio}")
            
#             return (
#                 f"✅ <strong>Vale bem-estar válido!</strong>\n"
#                 f"<strong>Valor disponível:</strong> {valor} {tipo_valor}\n"
#                 f"<strong>Validade:</strong> {validade}\n"
#                 f"Mensagem: {msg}"
#             )

#     except Exception as e:
#         print(f"Erro ao validar: {e}")
#         return f"Erro ao validar código: {str(e)}"
     
# @Tool
# def valida_cpf_email_telefone(cpf: str, email: str, telefone: str) -> object:
#     """Valida CPF, email e telefone do usuário.
#     Usar somente quando o usuário informar/confirmar os seguintes dados: CPF, telefone e e-mail.
#     Nunca invente esses dados, usar somente quando o usuário informar.

#     Args:
#         cpf (str): CPF do usuário.
#         email (str): Email do usuário.
#         telefone (str): número do telefone ou celular do usuário 

#     Returns:
#         obj: Objeto com análise se os dados são válidos ou não.
#     """
#     return validar_dados(cpf, email, telefone)

# def resolver_data_tool(texto: str) -> dict:
#     """
#     Resolve datas/dias em pt-BR (America/Sao_Paulo) de forma determinística.
#     Use sempre que usuário mencionar data/dia (DD/MM, DD/MM, amanhã, próxima quarta, etc).
#     """
#     return resolver_data(texto)

# @Tool
# def atualizar_cadastro_cliente(
#     conversation_id: str,
#     codigo_usuario: int,
#     nome: str | None = None,
#     cpf: str | None = None,
#     celular: str | None = None,
#     email: str | None = None,
#     data_nascimento: str | None = None,
#     genero: str | None = None
# ) -> str:
#     """
#     Atualiza os dados de cadastro de um cliente existente no sistema Buddha Spa.

#     Apenas os campos informados serão atualizados.
#     Também sincroniza o contexto local com os nomes corretos das chaves do MyDeps
#     e recalcula os campos faltantes após cada atualização.
#     """

#     url = f"https://app.bellesoftware.com.br/api/release/controller/IntegracaoExterna/v1.0/cliente?codCliente={codigo_usuario}"

#     headers = {
#         "Authorization": os.getenv("LABELLE_TOKEN"),
#         "Content-Type": "application/json"
#     }

#     payload = {}
#     context_update = {}

#     if nome:
#         payload["nome"] = nome
#         context_update["nome"] = nome

#     if cpf:
#         payload["cpf"] = cpf
#         context_update["cpf"] = _somente_numeros(cpf)

#     if celular:
#         payload["celular"] = celular
#         context_update["celular"] = _somente_numeros(celular)

#     if email:
#         payload["email"] = email
#         context_update["email"] = email

#     if data_nascimento:
#         payload["dataNascimento"] = data_nascimento
#         context_update["data_nascimento"] = data_nascimento

#     if genero:
#         payload["genero"] = genero
#         context_update["genero"] = genero

#     payload["observacao"] = "Atualização de cadastro via WhatsApp"

#     if not context_update:
#         return "Nenhum dado foi informado para atualização."

#     try:
#         print("Atualizando cliente:", codigo_usuario)
#         print("Payload:", payload)

#         response = requests.put(url, json=payload, headers=headers)

#         if response.status_code not in [200, 204]:
#             print("Erro API:", response.text)
#             return "Não foi possível atualizar o cadastro no momento."

#         # Recupera o contexto atual para recalcular faltantes
#         session = get_session(conversation_id)
#         context_atual = session[2] or {}

#         if isinstance(context_atual, str):
#             context_atual = context_atual.strip()
#             if context_atual == "" or context_atual.lower() == "none":
#                 context_atual = {}
#             else:
#                 try:
#                     context_atual = json.loads(context_atual)
#                 except Exception:
#                     context_atual = {}

#         contexto_mesclado = {
#             **context_atual,
#             **context_update,
#             "codigo_usuario": codigo_usuario,
#         }

#         analise = verificar_campos_faltantes_cadastro(contexto_mesclado)

#         context_update["codigo_usuario"] = codigo_usuario
#         context_update["campos_faltantes"] = analise["campos_faltantes"]
#         context_update["cadastro_completo"] = analise["cadastro_completo"]

#         update_context(conversation_id, context_update)

#         if analise["campos_faltantes"]:
#             faltantes_texto = ", ".join(analise["campos_faltantes"])
#             return (
#                 f"✅ Seus dados foram atualizados com sucesso! "
#                 f"Ainda faltam os seguintes campos no cadastro: {faltantes_texto}."
#             )

#         return "✅ Seus dados foram atualizados com sucesso! Seu cadastro está completo."

#     except Exception as e:
#         return f"Erro ao atualizar cadastro: {str(e)}"
    

# def complementar_cadastro_cliente(
#     conversation_id: str,
#     codigo_usuario: int,
#     data_nascimento: str | None = None,
#     genero: str | None = None
# ) -> str:
#     """
#     Complementa o cadastro do cliente com campos que não podem ser enviados
#     no endpoint de criação (/cliente/gravar), como data de nascimento e gênero.
#     """

#     url = f"https://app.bellesoftware.com.br/api/release/controller/IntegracaoExterna/v1.0/cliente?codCliente={codigo_usuario}"

#     headers = {
#         "Authorization": os.getenv("LABELLE_TOKEN"),
#         "Content-Type": "application/json"
#     }

#     payload = {}
#     context_update = {}

#     if data_nascimento:
#         payload["dataNascimento"] = data_nascimento
#         context_update["data_nascimento"] = data_nascimento

#     if genero:
#         payload["genero"] = genero
#         context_update["genero"] = genero

#     if not payload:
#         return "Nenhum dado complementar foi informado para atualização."

#     payload["observacao"] = "Complemento de cadastro via WhatsApp"

#     try:
#         print("Complementando cadastro do cliente:", codigo_usuario)
#         print("Payload complemento:", payload)

#         response = requests.put(url, json=payload, headers=headers)

#         if response.status_code not in [200, 204]:
#             print("Erro API complemento:", response.text)
#             return "Não foi possível complementar o cadastro no momento."

#         update_context(conversation_id, context_update)

#         return "✅ Dados complementares atualizados com sucesso!"

#     except Exception as e:
#         print(f"Erro ao complementar cadastro: {e}")
#         return f"Erro ao complementar cadastro: {str(e)}"

# @Tool
# def identificar_terapeuta_recorrente(
#     codigo_usuario: str,
#     dtInicio: str,
#     dtFim: str
# ) -> str:
#     """Retorna o terapeuta mais recorrente no histórico do cliente.

#     Só utilizar após o cliente escolher a terapia e informar a data desejada.

#     Args:
#         codigo_usuario (str): código do cliente no sistema
#         dtInicio (str): data inicial para busca no formato 'DD/MM/AAAA'
#         dtFim (str): data final para busca no formato 'DD/MM/AAAA'

#     Returns:
#         str: JSON string com o terapeuta recorrente ou lista vazia
#     """

#     url = (
#         "https://app.bellesoftware.com.br/api/release/controller/"
#         f"IntegracaoExterna/v1.0/cliente/agenda?codCliente={codigo_usuario}&codEstab=1&dtInicio={dtInicio}&dtFim={dtFim}"
#     )

#     headers = {
#         "Authorization": os.getenv("LABELLE_TOKEN")
#     }

#     try:
#         response = requests.get(url, headers=headers)
#         response.raise_for_status()

#         agendas = response.json()
#         print(f"Histórico bruto de agendas do cliente {codigo_usuario}: {agendas}")

#         contagem_terapeutas = {}
#         nomes_terapeutas = {}

#         for agenda in agendas:
#             prof = agenda.get("prof") or {}

#             # tenta várias chaves possíveis
#             cod = (
#                 prof.get("cod")
#                 or prof.get("codProf")
#                 or prof.get("cod_usuario")
#                 or prof.get("codigo")
#             )

#             nome = (
#                 prof.get("nome")
#                 or prof.get("nom_usuario")
#                 or prof.get("nomeProf")
#                 or prof.get("usuario")
#             )

#             if not cod:
#                 continue

#             cod = str(cod).strip()
#             if not cod:
#                 continue

#             contagem_terapeutas[cod] = contagem_terapeutas.get(cod, 0) + 1

#             # só salva/atualiza nome se vier algo válido
#             if nome and str(nome).strip():
#                 nomes_terapeutas[cod] = str(nome).strip()
#                 print(
#                         f"DEBUG HISTORICO - cod={cod} "
#                         f"nome={nomes_terapeutas.get(cod, nome)} "
#                         f"quantidade_atual={contagem_terapeutas[cod]}"
#                     )

#         if not contagem_terapeutas:
#             return json.dumps([], ensure_ascii=False)
#         print(f"DEBUG HISTORICO - contagem_final={contagem_terapeutas}")
#         print(f"DEBUG HISTORICO - nomes_finais={nomes_terapeutas}")
#         cod_mais_frequente = max(contagem_terapeutas, key=contagem_terapeutas.get)
#         quantidade = contagem_terapeutas[cod_mais_frequente]

#         # regra mínima para considerar recorrente
#         if quantidade < 3:
#             return json.dumps([], ensure_ascii=False)

#         resultado = [{
#             "nome": nomes_terapeutas.get(cod_mais_frequente, "Não identificado"),
#             "codProf": cod_mais_frequente,
#             "quantidade_atendimentos": quantidade
#         }]

#         print(
#                 f"DEBUG HISTORICO - terapeuta_mais_frequente={cod_mais_frequente} "
#                 f"nome={nomes_terapeutas.get(cod_mais_frequente, 'Não identificado')} "
#                 f"quantidade={quantidade}"
#             )

#         print(f"Terapeuta recorrente identificado: {resultado}")
#         return json.dumps(resultado, ensure_ascii=False)

#     except Exception as e:
#         print(f"Erro ao consultar histórico de terapeutas: {e}")
#         return json.dumps(
#             {"erro": "Não foi possível consultar o histórico de terapeutas no momento"},
#             ensure_ascii=False
#         )
    
# @Tool
# def consult_cadastro_cpf(cpf: str) -> str:
#     """Verifica se o cpf já está cadastrado no sistema
    

#     Args:
#         cpf (str): CPF do usuário.

#     Returns:
#         dic: dicionário com os dados do cadastro do usuário.
#     """
#     url = f'https://app.bellesoftware.com.br/api/release/controller/IntegracaoExterna/v1.0/cliente/listar?codEstab=1&celular={cpf}'
#     headers = {
#         'Authorization': os.getenv("LABELLE_TOKEN")
#     }

#     try:
#         response = requests.get(url, headers=headers)
#         response.raise_for_status()
        
#         data = response.json()
#         print(f"Resultado da consulta de cadastro: {data}")
        
#         return data
#     except Exception as e:
#         print(f"Erro ao consultar cadastro: {e}")
#         return {"erro": "Não foi possível consultar o cadastro no momento"}

# @Tool
# def finalizar_agendamento(
#     conversation_id: str,
#     voucher: Optional[str] = None
# ) -> str:
#     """
#     Finaliza um agendamento considerando:
#     - plano
#     - voucher / vale bem-estar
#     """

#     session = get_session(conversation_id)
#     context = session[2] or {}

#     # 🔥 tratamento do context
#     if isinstance(context, str):
#         context = context.strip()
#         if not context or context.lower() in ("none", "null"):
#             context = {}
#         else:
#             try:
#                 context = json.loads(context)
#             except Exception:
#                 context = {}

#     codigo_usuario = context.get("codigo_usuario")

#     if not codigo_usuario or str(codigo_usuario).strip().lower() in ("none", "null", ""):
#         return "❌ Não foi possível finalizar: código do cliente inválido."

#     # 🔥 identifica plano
#     cod_plano = context.get("cod_plano")
#     nome_plano = context.get("nome_plano")

#     # 🔥 monta observação dinâmica
#     observacao_partes = []

#     if cod_plano:
#         observacao_partes.append(f"Cliente possui o plano {nome_plano}")

#     if voucher:
#         observacao_partes.append(f"Voucher: {voucher}")

#     observacao = " | ".join(observacao_partes)

#     # 🔥 payload único
#     payload = {
#         "codCli": codigo_usuario,
#         "codEstab": 1,
#         "prof": {
#             "cod_usuario": context.get("codigo_terapeuta"),
#             "nom_usuario": context.get("terapeuta")
#         },
#         "dtAgd": context.get("data"),
#         "hri": context.get("horario"),
#         "serv": [
#             {
#                 "codServico": context.get("codigo_servico"),
#                 "nome": context.get("nome_servico"),
#                 "label": context.get("label_servico"),
#                 "valor": context.get("valor_servico"),
#                 "tempo": context.get("duracao")
#             }
#         ],
#         "codPlano": cod_plano if cod_plano else "",
#         "agSala": True,
#         "codSala": 1,
#         "codVendedor": "",
#         "codEquipamento": 1,
#         "observacao": observacao
#     }

#     print(f"Payload final do agendamento: {payload}")

#     url = 'https://app.bellesoftware.com.br/api/release/controller/IntegracaoExterna/v1.0/agenda/gravar'

#     headers = {
#         'Authorization': os.getenv("LABELLE_TOKEN"),
#         'Content-Type': 'application/json'
#     }

#     try:
#         response = requests.post(url, headers=headers, json=payload)
#         response.raise_for_status()

#         data = response.json()
#         print(f"Resposta da Belle: {data}")

#         if not data.get("dis", False):
#             update_current_agent(conversation_id, "agendamento_agent")
#             return (
#                 f"❌ HORÁRIO INDISPONÍVEL: {data.get('msg', 'erro desconhecido')}. "
#                 "Escolha outro horário."
#             )

#         update_current_agent(conversation_id, "agendamento_agent")

#         # 🔥 resposta inteligente
#         if cod_plano:
#             return "✅ Agendamento realizado com plano!"
#         elif voucher:
#             return " Agendamento realizado com voucher!"
#         else:
#             return " Agendamento realizado com sucesso!"

#     except Exception as e:
#         print(f"Erro ao finalizar agendamento: {e}")
#         try:
#             print(f"Response text: {response.text}")
#         except Exception:
#             pass
#         return f"Erro ao finalizar agendamento: {str(e)}"

# @Tool
# def consultar_pacotes(ctx: RunContext[MyDeps], cpf: str = None) -> str:
#     """Consulta pacotes do cliente pelo CPF"""
#     try:
#         conversation_id = ctx.deps.session_id
#         print("=" * 80)
#         print("CONSULTAR_PACOTES CHAMADA")
#         print(f"conversation_id (do ctx.deps): {conversation_id}, cpf: {cpf}")
#         print("=" * 80)
        
#         # Pede CPF se não foi passado
#         if not cpf:
#             return "Para consultar seus pacotes, preciso do seu CPF."
        
#         # Limpa CPF
#         cpf_limpo = cpf.replace(".", "").replace("-", "").replace("/", "").strip()
#         print(f"CPF limpo: {cpf_limpo}")
        
#         # Busca cliente por CPF
#         url = f'https://app.bellesoftware.com.br/api/release/controller/IntegracaoExterna/v1.0/cliente/listar?cpf={cpf_limpo}&id=&codEstab=1&email=&celular='
#         headers = {'Authorization': os.getenv("LABELLE_TOKEN")}
        
#         print(f"URL: {url}")
#         response = requests.get(url, headers=headers)
#         print(f"Status: {response.status_code}")
#         print(f"Response: {response.text[:200]}")
        
#         response.raise_for_status()
#         data = response.json()
#         print(f"Data completa: {data}")
        
#         # Recupera tentativas do contexto
#         print(f"DEBUG - Tentando buscar sessão: {conversation_id}")
#         session = get_session(conversation_id)
        
#         if session is None:
#             print(f"ERRO - Sessão não encontrada para conversation_id: {conversation_id}")
#             return "❌ CPF não encontrado. Deseja tentar novamente?"
        
#         context_atual = session[2] or {}
        
#         if isinstance(context_atual, str):
#             context_atual = context_atual.strip()
#             if context_atual == "" or context_atual.lower() == "none":
#                 context_atual = {}
#             else:
#                 try:
#                     context_atual = json.loads(context_atual)
#                 except Exception:
#                     context_atual = {}
        
#         tentativas_atuais = context_atual.get("tentativas_cpf_pacote", 0)
        
#         # API pode retornar lista ou objeto
#         if not data:
#             tentativas_atuais += 1
#             update_context(conversation_id, {"tentativas_cpf_pacote": tentativas_atuais})
            
#             if tentativas_atuais >= 2:
#                 return (
#                     "❌ CPF não encontrado novamente.\n\n"
#                     "Por favor, entre em contato com a nossa unidade para verificar seu cadastro:\n"
#                     "📞 <strong>11 99999-9999</strong>\n\n"
#                     "Ou acesse nosso site:\n"
#                     "🌐 https://buddhaspa.com.br/\n\n"
#                     "Até mais! 👋"
#                 )
            
#             return "❌ CPF não encontrado. Deseja tentar novamente?"
        
#         # Se for lista, pega primeiro item
#         if isinstance(data, list):
#             if len(data) == 0:
#                 tentativas_atuais += 1
#                 update_context(conversation_id, {"tentativas_cpf_pacote": tentativas_atuais})
                
#                 if tentativas_atuais >= 2:
#                     return (
#                         "❌ CPF não encontrado novamente.\n\n"
#                         "Por favor, entre em contato com a nossa unidade para verificar seu cadastro:\n"
#                         "📞 <strong>11 99999-9999</strong>\n\n"
#                         "Ou acesse nosso site:\n"
#                         "🌐 https://buddhaspa.com.br/\n\n"
#                         "Até mais! 👋"
#                     )
                
#                 return "❌ CPF não encontrado. Deseja tentar novamente?"
#             cliente = data[0]
#         else:
#             # Se for objeto direto
#             cliente = data
        
#         print(f"Cliente: {cliente}")
        
#         codigo = cliente.get("codigo")
#         print(f"Codigo: {codigo}")
        
#         if not codigo:
#             tentativas_atuais += 1
#             update_context(conversation_id, {"tentativas_cpf_pacote": tentativas_atuais})
            
#             if tentativas_atuais >= 2:
#                 return (
#                     "❌ Não foi possível identificar seu cadastro novamente.\n\n"
#                     "Por favor, entre em contato com a nossa unidade:\n"
#                     "📞 <strong>11 99999-9999</strong>\n\n"
#                     "Ou acesse nosso site:\n"
#                     "🌐 https://buddhaspa.com.br/\n\n"
#                     "Até mais! 👋"
#                 )
            
#             return "❌ Não foi possível identificar seu cadastro. Deseja tentar novamente?"
        
#         # Busca planos
#         url_planos = f"https://app.bellesoftware.com.br/api/release/controller/IntegracaoExterna/v1.0/cliente/planos?codCliente={codigo}&codEstab=1"
#         print(f"URL planos: {url_planos}")
        
#         response = requests.get(url_planos, headers=headers)
#         print(f"Status planos: {response.status_code}")
#         planos = response.json()
#         print(f"Planos: {planos}")
        
#         if not planos or len(planos) == 0:
#             tentativas_atuais += 1
#             update_context(conversation_id, {"tentativas_cpf_pacote": tentativas_atuais})
            
#             if tentativas_atuais >= 2:
#                 return (
#                     "❌ Você não possui pacotes cadastrados.\n\n"
#                     "Por favor, entre em contato com a nossa unidade para mais informações:\n"
#                     "📞 <strong>11 99999-9999</strong>\n\n"
#                     "Ou acesse nosso site:\n"
#                     "🌐 https://buddhaspa.com.br/\n\n"
#                     "Até mais! 👋"
#                 )
            
#             return "❌ Você não possui pacotes cadastrados. Deseja tentar com outro CPF?"
        
#         # SUCESSO - Reseta contador de tentativas
#         print("DEBUG - Tentativas de CPF resetadas para 0 (pacotes encontrados)")
#         update_context(conversation_id, {
#             "tentativas_cpf_pacote": 0,
#             "tipo_beneficio": "pacote"
#         })
        
#         # Formata resultado
#         resultado = "✅ <strong>Pacotes encontrados:</strong>\n"
#         for idx, plano in enumerate(planos, 1):
#             cod_plano = plano.get('codPlano')
#             nome_plano = plano.get('nome', 'Pacote sem nome')
#             servicos = plano.get('servicos', [])
            
#             resultado += f"\n<strong>📦 Pacote {idx}:</strong> {nome_plano}"
            
#             if servicos:
#                 resultado += "\n   <strong>Terapias disponíveis:</strong>"
#                 terapias_lista = []
#                 for idx_servico, servico in enumerate(servicos, 1):
#                     nome_servico = servico.get('nome')
#                     saldo = servico.get('saldoRestante', '0')
#                     resultado += f"\n   {idx_servico}. {nome_servico} - Saldo: {saldo}"
#                     terapias_lista.append(nome_servico)
                
#                 # Armazena lista de terapias no contexto para facilitar seleção
#                 update_context(conversation_id, {
#                     "terapias_disponiveis": terapias_lista
#                 })
#                 print(f"DEBUG - Terapias armazenadas no contexto: {terapias_lista}")
            
#             resultado += "\n"
        
#         resultado += "\n<strong>O que deseja utilizar?</strong>"
#         print(f"Resultado formatado: {resultado}")
#         return resultado
        
#     except Exception as e:
#         print(f"ERRO: {e}")
#         import traceback
#         traceback.print_exc()
#         return f"Erro: {str(e)}"
# @Tool
# def ir_para_cadastro(ctx: RunContext[MyDeps]) -> str:
#     """
#     Transição do voucher_agent para cadastro_agent.
#     Só deve ser chamada após validar benefício com sucesso.
    
#     VERIFICAÇÃO CRÍTICA:
#     - Se benefício = voucher/pacote → DEVE ter terapia escolhida
#     - Se benefício = vale bem-estar → pode prosseguir sem terapia (será escolhida depois)
#     """
#     conversation_id = ctx.deps.session_id
#     tipo_beneficio = ctx.deps.tipo_beneficio if hasattr(ctx.deps, 'tipo_beneficio') else None
#     terapia = ctx.deps.terapia if hasattr(ctx.deps, 'terapia') else None
    
#     print("=" * 80)
#     print("DEBUG IR_PARA_CADASTRO - VERIFICAÇÃO")
#     print(f"Conversation ID: {conversation_id}")
#     print(f"Tipo benefício: {tipo_beneficio}")
#     print(f"Terapia escolhida: {terapia}")
#     print("=" * 80)
    
#     # VERIFICAÇÃO CRÍTICA: Voucher/Pacote DEVE ter terapia escolhida
#     if tipo_beneficio in ['voucher', 'pacote']:
#         if not terapia:
#             print("❌ ERRO: Tentativa de transição sem terapia escolhida!")
#             return (
#                 "❌ ERRO INTERNO: Não é possível prosseguir sem terapia escolhida.\n\n"
#                 f"Por favor, entre em contato com a nossa unidade:\n"
#                 f"📞 11 99999-9999"
#             )
    
#     # Atualiza o agente atual para cadastro_agent
#     update_current_agent(conversation_id, "cadastro_agent")
    
#     print("✅ Transição para cadastro_agent realizada com sucesso!")
    
#     # Retorna string vazia para não gerar mensagem intermediária
#     # A próxima mensagem do usuário será processada pelo cadastro_agent
#     return ""

# @Tool
# def armazenar_terapia(ctx: RunContext[MyDeps], terapia: str) -> str:
#     """
#     Armazena a terapia escolhida pelo usuário no contexto.
#     Use esta tool quando o usuário escolher uma terapia do pacote.
    
#     Args:
#         terapia: Nome da terapia escolhida
#     """
#     conversation_id = ctx.deps.session_id
    
#     print("=" * 80)
#     print("DEBUG ARMAZENAR_TERAPIA")
#     print(f"Conversation ID: {conversation_id}")
#     print(f"Terapia: {terapia}")
#     print("=" * 80)
    
#     # Armazena a terapia no contexto
#     update_context(conversation_id, {
#         "terapia": terapia
#     })
    
#     # Atualiza ctx.deps para refletir as mudanças
#     ctx.deps.terapia = terapia
    
#     print(f"DEBUG - Terapia armazenada: {terapia}")
#     print(f"DEBUG - ctx.deps.terapia: {ctx.deps.terapia}")
#     print("=" * 80)
    
#     return f"✅ Terapia '{terapia}' armazenada com sucesso."
