from app import create_app, db, bcrypt
from app.models.user import User, UserRole

def create_admin_user():
    app = create_app()
    
    admin_username = 'admin_user'
    admin_email = 'admin@example.ru'
    admin_password = 'admin123'
    
    with app.app_context():
        # Check if admin already exists by username or email
        existing_user = User.query.filter(
            (User.username == admin_username) | (User.email == admin_email)
        ).first()
        
        if existing_user:
            print(f'User with username "{admin_username}" or email "{admin_email}" already exists.')
            print(f'Please log in with these credentials or check the database.')
            return
        
        # Create admin user
        hashed_password = bcrypt.generate_password_hash(admin_password).decode('utf-8')
        admin = User(
            username=admin_username,
            email=admin_email,
            password=hashed_password,
            role=UserRole.ADMIN.value
        )
        
        db.session.add(admin)
        db.session.commit()
        print('Admin user created successfully!')
        print(f'Login: {admin_email}')
        print(f'Password: {admin_password}')

if __name__ == '__main__':
    create_admin_user() 