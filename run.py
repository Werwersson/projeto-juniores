import os
from app import create_app

# Remova o os.environ.get daqui
app = create_app()

if __name__ == "__main__":
    app.run()
