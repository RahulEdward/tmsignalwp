from app import app, socketio
from database.auth_db import init_db as ensure_auth_tables_exists
from database.master_contract_db import init_db as ensure_master_contract_tables_exists
from database.apilog_db import init_db as ensure_api_log_tables_exists

# Initialize database tables on startup
with app.app_context():
    ensure_auth_tables_exists()
    ensure_master_contract_tables_exists()
    ensure_api_log_tables_exists()

# For Railway/Gunicorn deployment
if __name__ == "__main__":
    socketio.run(app)
