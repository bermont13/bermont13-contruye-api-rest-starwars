"""
This module takes care of starting the API Server, Loading the DB and Adding the endpoints
"""
import os
from flask import Flask, request, jsonify, url_for
from flask_migrate import Migrate
from flask_swagger import swagger
from flask_cors import CORS
from utils import APIException, generate_sitemap
from admin import setup_admin
from models import db, User, People, Planet, Favorites

app = Flask(__name__)
app.url_map.strict_slashes = False

# Configura la base de datos (Postgres si está en producción, SQLite si no)
db_url = os.getenv("DATABASE_URL")
if db_url is not None:
    app.config['SQLALCHEMY_DATABASE_URI'] = db_url.replace(
        "postgres://", "postgresql://")
else:
    app.config['SQLALCHEMY_DATABASE_URI'] = "sqlite:////tmp/test.db"

app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False

# Inicializa extensiones
MIGRATE = Migrate(app, db)
db.init_app(app)
CORS(app)
setup_admin(app)

# ----------------------------------------
# MANEJO DE ERRORES
# ----------------------------------------

@app.errorhandler(APIException)
def handle_invalid_usage(error):
    return jsonify(error.to_dict()), error.status_code

# Sitemap con todas las rutas
@app.route('/')
def sitemap():
    return generate_sitemap(app)

# Ruta de prueba
@app.route('/user', methods=['GET'])
def handle_hello():
    return jsonify({"msg": "Hello, this is your GET /user response"}), 200

# ----------------------------------------
# ENDPOINTS DE USUARIOS
# ----------------------------------------

@app.route('/users', methods=['GET'])
def get_users():
    try:
        users = User.query.all()
        users_list = [user.serialize() for user in users]
        return jsonify(users_list), 200
    except Exception as e:
        return jsonify({"error": str(e)}), 500

# ----------------------------------------
# ENDPOINTS DE PEOPLE
# ----------------------------------------

@app.route('/people', methods=['GET'])
def get_people():
    try:
        people = People.query.all()
        people_list = [p.serialize() for p in people]
        return jsonify(people_list), 200
    except Exception as e:
        return jsonify({"error": str(e)}), 500

@app.route('/people/<int:people_id>', methods=['GET'])
def get_person_by_id(people_id):
    try:
        person = People.query.get(people_id)
        if person is None:
            return jsonify({"error": "Personaje no encontrado"}), 404
        return jsonify(person.serialize()), 200
    except Exception as e:
        return jsonify({"error": str(e)}), 500

# ----------------------------------------
# ENDPOINTS DE PLANETS
# ----------------------------------------

@app.route('/planets', methods=['GET'])
def get_planets():
    try:
        planets = Planet.query.all()
        planets_list = [planet.serialize() for planet in planets]
        return jsonify(planets_list), 200
    except Exception as e:
        return jsonify({"error": str(e)}), 500

@app.route('/planets/<int:planet_id>', methods=['GET'])
def get_planet_by_id(planet_id):
    try:
        planet = Planet.query.get(planet_id)
        if planet is None:
            return jsonify({"msg": "Planeta no encontrado"}), 404
        return jsonify(planet.serialize()), 200
    except Exception as e:
        return jsonify({"error": str(e)}), 500

# ----------------------------------------
# FAVORITOS
# ----------------------------------------

@app.route('/users/favorites/<int:user_id>', methods=['GET'])
def get_user_favorites(user_id):
    try:
        favorites = Favorites.query.filter_by(user_id=user_id).all()
        favorites_list = []

        for fav in favorites:
            fav_data = {
                "id": fav.id,
                "user_id": fav.user_id,
                "planet_id": fav.planet_id,
                "people_id": fav.people_id
            }
            favorites_list.append(fav_data)

        return jsonify(favorites_list), 200
    except Exception as e:
        return jsonify({"error": str(e)}), 500

@app.route('/favorite/planet/<int:user_id>/<int:planet_id>', methods=['POST'])
def add_favorite_planet(user_id, planet_id):
    try:
        planet = Planet.query.get(planet_id)
        if planet is None:
            return jsonify({"error": "Planeta no encontrado"}), 404

        new_fav = Favorites(user_id=user_id, planet_id=planet_id)
        db.session.add(new_fav)
        db.session.commit()

        return jsonify({"msg": f"Planeta con id {planet_id} añadido a favoritos"}), 201
    except Exception as e:
        return jsonify({"error": str(e)}), 500

@app.route('/favorite/people/<int:people_id>', methods=['POST'])
def add_favorite_person(people_id):
    try:
        user_id = 1  # User fijo por ahora

        person = db.session.execute(
            db.select(People).filter_by(id=people_id)
        ).scalar_one_or_none()

        if person is None:
            return jsonify({"error": "Personaje no encontrado"}), 404

        new_fav = Favorites(user_id=user_id, people_id=people_id)
        db.session.add(new_fav)
        db.session.commit()

        return jsonify({"msg": f"Personaje con id {people_id} añadido a favoritos"}), 201
    except Exception as e:
        return jsonify({"error": str(e)}), 500
    
@app.route('/favorite/people/<int:user_id>/<int:people_id>', methods=['DELETE'])
def delete_favorite_person(user_id, people_id):
    try:
        favorite = Favorites.query.filter_by(user_id=user_id, people_id=people_id).first()
        if not favorite:
            return jsonify({"msg": "Favorito no encontrado"}), 404

        db.session.delete(favorite)
        db.session.commit()
        return jsonify({"msg": f"Personaje con id {people_id} eliminado de favoritos"}), 200

    except Exception as e:
        return jsonify({"error": str(e)}), 500
    
@app.route('/favorite/planet/<int:user_id>/<int:planet_id>', methods=['DELETE'])
def delete_favorite_planet(user_id, planet_id):
    try:
        favorite = Favorites.query.filter_by(user_id=user_id, planet_id=planet_id).first()
        if not favorite:
            return jsonify({"msg": "Favorito no encontrado"}), 404

        db.session.delete(favorite)
        db.session.commit()
        return jsonify({"msg": f"Planeta con id {planet_id} eliminado de favoritos"}), 200

    except Exception as e:
        return jsonify({"error": str(e)}), 500



# ----------------------------------------
# MAIN
# ----------------------------------------

if __name__ == '__main__':
    PORT = int(os.environ.get('PORT', 3000))
    app.run(host='0.0.0.0', port=PORT, debug=True)
