import os
from app import create_app
from app.utils.placeholder import generate_default_placeholders

app = create_app()

with app.app_context():
    generate_default_placeholders(app.static_folder)
    print("Placeholder images regenerated successfully.") 