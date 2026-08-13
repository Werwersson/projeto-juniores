import logging
from datetime import datetime

# Configuração básica para o Vercel capturar
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("TeoKids-Audit")

def audit_log(action, details="", actor=None, target_user=None, **kwargs):
    """
    Registra ações críticas no sistema.
    O **kwargs garante que a função nunca quebre se receber argumentos extras.
    """
    data_hora = datetime.now().strftime("%d/%m/%Y %H:%M:%S")
    
    # Tenta descobrir o nome de quem fez a ação
    nome_ator = "Sistema"
    if actor:
        # Se for um objeto de usuário, tenta pegar o nome ou ID
        nome_ator = getattr(actor, 'name', getattr(actor, 'id', "Desconhecido"))
        
    mensagem = f"[{data_hora}] 🛡️ AUDITORIA | Ação: {action} | Resp: {nome_ator} | Detalhes: {details}"
    
    # Imprime no log do servidor
    print(mensagem)
    logger.info(mensagem)