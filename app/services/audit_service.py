import logging
from datetime import datetime

# Configuração básica para o Vercel capturar
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("TeoKids-Audit")

def audit_log(action, user_id, details=""):
    """
    Registra ações críticas no sistema.
    Estes logs poderão ser visualizados na aba "Logs" do painel do Vercel.
    """
    data_hora = datetime.now().strftime("%d/%m/%Y %H:%M:%S")
    mensagem = f"[{data_hora}] 🛡️ AUDITORIA | Ação: {action} | Resp. ID: {user_id} | Detalhes: {details}"
    
    # Imprime no log do servidor
    print(mensagem)
    logger.info(mensagem)