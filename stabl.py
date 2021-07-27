from app import create_app, db
from app.models import User, Customer, Admin, Package, PackageUse, Company, CompanyPackages

app = create_app()

@app.shell_context_processor
def make_shell_context():
    return {'db': db, 'User': User, 'Customer': Customer, 'Admin': Admin, 'Package': Package, 'PackageUse': PackageUse, 'Company': Company, 'CompanyPackages': CompanyPackages}


password = '123'

@app.cli.command('populate_data')
def populate_data():
    C1 = Company(name="Company 1")
    admin1 = Admin(company_id=1, name='Admin 1', email='admin@example.com')
    admin1.set_password(password)
    admin2 = Admin(company_id=1, name='Admin 2', email='admin2@example.com')
    admin2.set_password(password)

    db.session.add(C1)
    db.session.add(admin1)
    db.session.add(admin2)
    db.session.commit()

    C2 = Company(name="Company 2")
    admin3 = Admin(company_id=2, name='Admin 3', email='admin@example2.com')
    admin3.set_password(password)
    admin4 = Admin(company_id=2, name='Admin 4', email='admin2@example2.com')
    admin4.set_password(password)
    
    db.session.add(C2)
    db.session.add(admin3)
    db.session.add(admin4)
    db.session.commit()

    user1 = Customer(name="User 1", email="bladefire@gmail.com", phone="+6591511172")
    user1.set_password(password)
    user2 = Customer(name="User 2", email="jotham.goh@gmail.com", phone="+6594507510")
    user2.set_password(password)
    user3 = Customer(name="User 3", email="test@gmail.com", phone="+6594507511")
    user3.set_password(password)
    user4 = Customer(name="User 4", email="test2@gmail.com", phone="+6594507512")
    user4.set_password(password)

    db.session.add(user1)
    db.session.add(user2)
    db.session.add(user3)
    db.session.add(user4)
    db.session.commit()

    p1 = Package(
            admin_id=admin1.id, 
            cust_id=user1.id,
            company_id=C1.id,
            package_name="Haircut Men Company 1",
            package_num_total_uses_at_start=20,
            package_num_used_when_keyed=2,
            package_price_paid_in_cents=1323)
    p2 = Package(
            admin_id=admin3.id, 
            cust_id=user1.id,
            company_id=C2.id,
            package_name="Haircut Women Company 2",
            package_num_total_uses_at_start=10,
            package_num_used_when_keyed=0,
            package_price_paid_in_cents=999)
    p3 = Package(
            admin_id=admin2.id, 
            cust_id=user2.id,
            company_id=C1.id,
            package_name="Haircut Women Company 1",
            package_num_total_uses_at_start=13,
            package_num_used_when_keyed=0,
            package_price_paid_in_cents=4234)
    p4 = Package(
            admin_id=admin2.id, 
            cust_id=user3.id,
            company_id=C1.id,
            package_name="Haircut Women Company 1",
            package_num_total_uses_at_start=15,
            package_num_used_when_keyed=0,
            package_price_paid_in_cents=1423)

    db.session.add(p1)
    db.session.add(p2)
    db.session.add(p3)
    db.session.add(p4)
    db.session.commit()