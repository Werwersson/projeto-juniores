import os
from app import create_app

# Usa ProductionConfig por padrão — explicitamente use FLASK_ENV=development para dev local
app = create_app(os.environ.get("FLASK_ENV", "production"))

if __name__ == "__main__":
    app.run(debug=(os.environ.get("FLASK_ENV") == "development"))
