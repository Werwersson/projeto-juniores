# Projeto Juniores — Estrutura de Pastas

```
projeto-juniores/
│
├── app/
│   ├── __init__.py               # Factory function, registra blueprints
│   │
│   ├── models/
│   │   ├── __init__.py
│   │   ├── user.py               # User, UserRole (enum)
│   │   ├── pgm.py                # PGM, PGMLeader
│   │   ├── activity.py           # ActivityType, ActivitySource (enum)
│   │   ├── log.py                # ChecklistLog, ManualLog
│   │   └── balance.py            # PremilesBalance
│   │
│   ├── blueprints/
│   │   ├── auth/
│   │   │   ├── __init__.py
│   │   │   ├── routes.py         # /login, /logout
│   │   │   └── forms.py
│   │   │
│   │   ├── supervisor/
│   │   │   ├── __init__.py
│   │   │   └── routes.py         # /supervisor/dashboard, /pgms, /usuarios
│   │   │
│   │   ├── lider/
│   │   │   ├── __init__.py
│   │   │   └── routes.py         # /lider/dashboard, /lider/pgm, /lider/lancamento
│   │   │
│   │   └── junior/
│   │       ├── __init__.py
│   │       └── routes.py         # /junior/dashboard, /junior/checklist, /junior/extrato
│   │
│   ├── services/
│   │   ├── auth_service.py       # login, logout, get_current_user
│   │   ├── premiles_service.py   # credit_premiles(), get_balance(), get_extrato()
│   │   ├── checklist_service.py  # can_check_today(), mark_activity()
│   │   └── pgm_service.py        # get_pgm_members(), rename_pgm()
│   │
│   ├── decorators.py             # @requires_role, @requires_pgm_access
│   │
│   ├── templates/
│   │   ├── base.html
│   │   ├── auth/
│   │   │   └── login.html
│   │   ├── supervisor/
│   │   │   ├── dashboard.html
│   │   │   ├── pgm_detail.html
│   │   │   └── usuario_detail.html
│   │   ├── lider/
│   │   │   ├── dashboard.html
│   │   │   ├── lancamento.html
│   │   │   └── junior_detail.html
│   │   └── junior/
│   │       ├── dashboard.html
│   │       ├── checklist.html
│   │       └── extrato.html
│   │
│   └── static/
│       ├── css/
│       │   └── custom.css
│       └── js/
│           └── checklist.js      # Lógica de bloqueio de datas no front
│
├── migrations/                   # Flask-Migrate (Alembic)
│
├── scripts/
│   └── seed.py                   # Popula usuários, PGMs e activities iniciais
│
├── tests/
│   ├── test_auth.py
│   ├── test_premiles.py
│   └── test_checklist.py
│
├── .env                          # DATABASE_URL, SECRET_KEY
├── .env.example
├── config.py                     # Config, DevelopmentConfig, ProductionConfig
├── requirements.txt
├── Procfile                      # web: gunicorn "app:create_app()"
└── run.py                        # Ponto de entrada local
```

## Stack completa

| Camada        | Tecnologia                        |
|---------------|-----------------------------------|
| Backend       | Flask 3.x                         |
| ORM           | SQLAlchemy 2.x + Flask-SQLAlchemy |
| Migrations    | Flask-Migrate (Alembic)           |
| Auth          | Flask-Login + bcrypt              |
| Forms         | Flask-WTF                         |
| Frontend      | Jinja2 + Bootstrap 5              |
| Banco         | PostgreSQL (Neon)                 |
| Deploy        | Railway                           |
| Process mgr   | Gunicorn                          |

## Regras de roteamento por role

| Role       | Prefixo    | Acesso                              |
|------------|------------|-------------------------------------|
| supervisor | /supervisor| Todos os PGMs, todos os usuários    |
| lider      | /lider     | Apenas o(s) PGM(s) que lidera      |
| junior     | /junior    | Apenas o próprio perfil e checklist |
