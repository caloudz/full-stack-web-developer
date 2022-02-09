import os
from flask import Flask, request, jsonify, abort
from sqlalchemy import exc
import json
from flask_cors import CORS

from .database.models import db_drop_and_create_all, setup_db, Drink
from .auth.auth import AuthError, requires_auth

app = Flask(__name__)
setup_db(app)
CORS(app)

db_drop_and_create_all()

# --------------------------------------------------------------
# ROUTES
# --------------------------------------------------------------

@app.route('/')
def index():
    return jsonify({
        'success': True,
        'message': 'Welcome to Coffee Shop, what can I get you?'
        })

# --------------------------------------------------------------
# GET /drinks
#   it should be a public endpoint
#   it should contain only the drink.short() data representation
# returns status code 200 and json {"success": True, "drinks": drinks} where drinks is the list of drinks
#   or appropriate status code indicating reason for failure
# --------------------------------------------------------------

@app.route('/drinks', methods=['GET'])
def get_drinks():
    results = Drink.query.order_by(Drink.title).all()
    drinks = [d.short() for d in results]
    return jsonify({
        'success': True,
        'drinks': drinks
    }), 200

# --------------------------------------------------------------
# GET /drinks-detail
#   it should require the 'get:drinks-detail' permission
#   it should contain the drink.long() data representation
# returns status code 200 and json {"success": True, "drinks": drinks} where drinks is the list of drinks
#   or appropriate status code indicating reason for failure
# --------------------------------------------------------------

@app.route('/drinks-detail', methods=['GET'])
@requires_auth('get:drinks-detail')
def get_drinks_detail(payload):
    results = Drink.query.all()
    drinks = [d.long() for d in results]
    return jsonify({
        'success': True,
        'drinks': drinks
    }), 200

# --------------------------------------------------------------
# POST /drinks
#   it should create a new row in the drinks table
#   it should require the 'post:drinks' permission
#   it should contain the drink.long() data representation
# returns status code 200 and json {"success": True, "drinks": drink} where drink an array containing only the newly created drink
#   or appropriate status code indicating reason for failure
# --------------------------------------------------------------

@app.route('/drinks', methods=['POST'])
@requires_auth('post:drinks')
def post_drinks(payload):
    body = request.get_json()
    if not body:
        abort(404)
    title = body['title']
    recipe = json.dumps(body['recipe'])
    drink = Drink(
        title = title,
        recipe = recipe
    )
    try:
        drink.insert() 
        return jsonify({
            'success': True,
            'drinks': drink.long()
        }), 200
    except Exception:
        abort(422)

# --------------------------------------------------------------
# PATCH /drinks/<id>
#   where <id> is the existing model id
#   it should respond with a 404 error if <id> is not found
#   it should update the corresponding row for <id>
#   it should require the 'patch:drinks' permission
#   it should contain the drink.long() data representation
# returns status code 200 and json {"success": True, "drinks": drink} where drink an array containing only the updated drink
#   or appropriate status code indicating reason for failure
# --------------------------------------------------------------

@app.route('/drinks/<id>', methods=['PATCH'])
@requires_auth('patch:drinks')
def patch_drinks(payload, id):
    try:
        drink = Drink.query.get(id)
        if not drink:
            abort(404)
        body = request.get_json()
        for k in body.keys():
            if k == 'title':
                drink.title = body['title']
            elif k == 'recipe':
                drink.recipe = json.dumps(body['recipe'])
        drink.update()
        return jsonify({
            'success': True,
            'drinks': [drink.long()]
        }), 200
    except Exception:
        abort(422)

# --------------------------------------------------------------
# DELETE /drinks/<id>
#   where <id> is the existing model id
#   it should respond with a 404 error if <id> is not found
#   it should delete the corresponding row for <id>
#   it should require the 'delete:drinks' permission
# returns status code 200 and json {"success": True, "delete": id} where id is the id of the deleted record
#   or appropriate status code indicating reason for failure
# --------------------------------------------------------------

@app.route('/drinks/<id>', methods=['DELETE'])
@requires_auth('delete:drinks')
def delete_drinks(payload, id):
    drink = Drink.query.get(id)
    if not drink:
        abort(404)
    try:
        drink.delete()
        return jsonify({
            'success': True,
            'delete': id
        }), 200
    except Exception:
        abort(422)

# --------------------------------------------------------------
# Error Handling
# --------------------------------------------------------------

@app.errorhandler(400)
def bad_request(error):
    return jsonify({
      'success': False,
      'error': 400,
      'message': 'Bad Request'
    }), 400

@app.errorhandler(404)
def not_found(error):
    return jsonify({
        'success': False,
        'error': 404,
        'message': 'Resource Not Found'
    }), 404

@app.errorhandler(422)
def unprocessable(error):
    return jsonify({
        "success": False,
        "error": 422,
        "message": "Unprocessable"
    }), 422

@app.errorhandler(500)
def internal_server_error(error):
    return jsonify({
        'success': False,
        'error': 500,
        'message': 'Internal Server Error'
    }), 500

@app.errorhandler(AuthError)
def auth_error(error):
    return jsonify({
        "success": False,
        "error": error.status_code,
        "message": error.error
    }), error.status_code

if __name__ == "__main__":
    app.debug = True
    app.run()
