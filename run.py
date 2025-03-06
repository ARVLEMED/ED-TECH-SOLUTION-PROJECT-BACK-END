from app import create_app
from seed_data import seed_data

app = create_app()  # Define `app` at the module level

if __name__ == '__main__':
    with app.app_context():
        seed_data()
        print("Mock data seeded!")
    app.run(debug=True)
