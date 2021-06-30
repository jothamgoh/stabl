from app import create_app, db
from app.models import User, Customer, Admin, Package, PackageUse

app = create_app()

@app.shell_context_processor
def make_shell_context():
    return {'db': db, 'User': User, 'Customer': Customer, 'Admin': Admin, 'Package': Package, 'PackageUse': PackageUse}

