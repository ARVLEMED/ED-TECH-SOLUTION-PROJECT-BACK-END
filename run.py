from app import create_app
from seed_data import seed_data

app = create_app()

# Run the seed function inside the app context
if __name__ == '__main__':
    with app.app_context():
        # Seed the database (you can choose to remove this line if you want to seed manually)
        seed_data()
        print("Mock data seeded!")

    # Start the Flask application
    app.run(debug=True)
