"""
app/services/period_service.py

Lógica de negócio para períodos de Premiles:
  - get_active_period()     → período ativo ou None
  - criar_periodo()         → cria e ativa um novo período
  - encerrar_periodo()      → tira snapshot, zera saldos, desativa
  - get_historico()         → todos os períodos encerrados
  - get_ranking_periodo()   → ranking de um período específico
"""
from datetime import date, datetime
from app import db
from app.models.period import Period, PeriodSnapshot
from app.models.activity import PremilesBalance
from app.models.user import User, UserRole


def get_active_period():
    """Retorna o período ativo, ou None se não houver nenhum."""
    return db.session.execute(
        db.select(Period).where(Period.is_active == True)  # noqa: E712
    ).scalar_one_or_none()


def criar_periodo(name: str, start_date: date, end_date, created_by_id: int) -> Period:
    """
    Cria um novo período e o define como ativo.
    Desativa qualquer período anterior que ainda esteja ativo.
    Não zera saldos ao criar — apenas ao encerrar.
    """
    # Desativa período ativo anterior (segurança)
    ativo = get_active_period()
    if ativo:
        raise ValueError(
            f"Já existe um período ativo: '{ativo.name}'. "
            "Encerre-o antes de criar um novo."
        )

    periodo = Period(
        name=name,
        start_date=start_date,
        end_date=end_date or None,
        is_active=True,
        created_by=created_by_id,
    )
    db.session.add(periodo)
    db.session.commit()
    return periodo


def encerrar_periodo(periodo_id: int) -> dict:
    """
    Encerra um período:
      1. Tira snapshot de cada junior (saldo + posição geral + posição por PGM)
      2. Zera o saldo de todos os juniores (premiles_balance)
      3. Marca o período como inativo e define closed_at
    Retorna um dict com estatísticas do encerramento.
    """
    periodo = db.session.get(Period, periodo_id)
    if not periodo:
        raise ValueError("Período não encontrado.")
    if not periodo.is_active:
        raise ValueError("Este período já foi encerrado.")

    # Busca todos os juniores com saldo, ordenados desc
    juniors = db.session.execute(
        db.select(User)
        .where(User.role == UserRole.JUNIOR)
        .join(PremilesBalance, PremilesBalance.junior_id == User.id, isouter=True)
        .order_by(db.desc(PremilesBalance.total_balance))
    ).scalars().all()

    # Monta ranking por PGM
    pgm_counters = {}

    snapshots_criados = 0
    for pos_geral, junior in enumerate(juniors, 1):
        saldo = junior.balance.total_balance if junior.balance else 0
        pgm_id = junior.pgm_id

        # Posição dentro do PGM
        pgm_counters[pgm_id] = pgm_counters.get(pgm_id, 0) + 1
        pos_pgm = pgm_counters[pgm_id]

        snap = PeriodSnapshot(
            period_id=periodo_id,
            junior_id=junior.id,
            pgm_id=pgm_id,
            total_premiles=saldo,
            position=pos_geral,
            pgm_position=pos_pgm,
        )
        db.session.add(snap)
        snapshots_criados += 1

    # Zera todos os saldos
    db.session.execute(
        db.update(PremilesBalance).values(total_balance=0)
    )

    # Fecha o período
    periodo.is_active = False
    periodo.closed_at = datetime.now()
    if not periodo.end_date:
        periodo.end_date = date.today()

    db.session.commit()

    return {
        "periodo": periodo.name,
        "snapshots": snapshots_criados,
        "encerrado_em": periodo.closed_at.strftime("%d/%m/%Y às %H:%M"),
    }


def get_historico():
    """Retorna todos os períodos, do mais recente ao mais antigo."""
    return db.session.execute(
        db.select(Period).order_by(Period.created_at.desc())
    ).scalars().all()


def get_ranking_periodo(periodo_id: int):
    """Retorna os snapshots de um período, ordenados por posição."""
    return db.session.execute(
        db.select(PeriodSnapshot)
        .where(PeriodSnapshot.period_id == periodo_id)
        .order_by(PeriodSnapshot.position)
    ).scalars().all()
