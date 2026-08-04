"""
Script para migrar o banco existente:
  1. Adiciona coluna 'username' em users
  2. Preenche username dos usuários existentes baseado no email
  3. Torna email opcional (nullable=True)
  4. Adiciona unique constraint em username

Rode UMA VEZ após substituir os arquivos:
  python scripts/migrate_username.py
"""
import os, sys
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from run import app
from app import db
from sqlalchemy import text


def migrate():
    with app.app_context():
        with db.engine.connect() as conn:

            # 1. Verifica se a coluna já existe
            result = conn.execute(text("""
                SELECT column_name FROM information_schema.columns
                WHERE table_name='users' AND column_name='username'
            """))
            if result.fetchone():
                print("✅ Coluna 'username' já existe — nada a fazer.")
                return

            print("🔧 Adicionando coluna 'username'...")

            # 2. Adiciona coluna username (nullable temporariamente)
            conn.execute(text(
                "ALTER TABLE users ADD COLUMN username VARCHAR(60)"
            ))
            conn.commit()

            # 3. Preenche username a partir do email (parte antes do @)
            #    Para usuários sem email, usa 'user_<id>'
            conn.execute(text("""
                UPDATE users
                SET username = CASE
                    WHEN email IS NOT NULL AND email LIKE '%@%'
                        THEN LOWER(SPLIT_PART(email, '@', 1))
                    ELSE LOWER(CONCAT('user_', id))
                END
            """))
            conn.commit()

            # 4. Torna username NOT NULL e adiciona unique constraint
            conn.execute(text(
                "ALTER TABLE users ALTER COLUMN username SET NOT NULL"
            ))
            conn.execute(text(
                "CREATE UNIQUE INDEX IF NOT EXISTS ix_users_username ON users (username)"
            ))

            # 5. Torna email nullable (já era nullable no Postgres, mas garante)
            conn.execute(text(
                "ALTER TABLE users ALTER COLUMN email DROP NOT NULL"
            ))
            conn.commit()

            print("✅ Migração concluída!")
            print("   Usernames gerados a partir dos emails existentes.")
            print("   Confira em: Supervisor → Usuários")


if __name__ == "__main__":
    migrate()
