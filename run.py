from app import create_app

app = create_app()

# Добавляем CLI команду для генерации плейсхолдеров
@app.cli.command("generate-placeholders")
def generate_placeholders_command():
    """Создает плейсхолдеры для изображений."""
    from app.utils.placeholders import generate_default_placeholders
    print("Generating placeholder images...")
    placeholders = generate_default_placeholders()
    print(f"Generated {len(placeholders)} placeholder images:")
    for name, filename in placeholders.items():
        print(f"- {name}: {filename}")
    print("Done!")

if __name__ == '__main__':
    app.run(debug=True)
