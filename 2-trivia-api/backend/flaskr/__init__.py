import os
from flask import Flask, request, abort, jsonify
from flask_sqlalchemy import SQLAlchemy
from flask_cors import CORS
import random

from models import setup_db, Question, Category

QUESTIONS_PER_PAGE = 10

#----------------------------------------------------------------------------#
# Helper Functions
#----------------------------------------------------------------------------#

def get_pagination(request, results):
  '''
  Paginates and formats questions.
  '''
  page = request.args.get('page', 1, type=int)
  start = (page - 1) * QUESTIONS_PER_PAGE
  end = start + QUESTIONS_PER_PAGE

  questions = [q.format() for q in results]
  selection = questions[start:end]

  return selection

#----------------------------------------------------------------------------#
# App Setup
#----------------------------------------------------------------------------#

def create_app(test_config=None):
  # create and configure the app
  app = Flask(__name__)
  setup_db(app)
  
  # Set up CORS. Allow '*' for origins
  cors = CORS(app, resources={r"/*": {"origins": "*"}})
  #CORS(app)                                                                        # uncomment this later

  # Use the after_request decorator to set Access-Control-Allow
  @app.after_request
  def after_request(response):
    response.headers.add(
      'Access-Control-Allow-Headers',
      'Content-Type, Authorization, true'
      )
    response.headers.add(
      'Access-Control-Allow-Methods',
      'GET, POST, PUT, DELETE'
      )
    return response

  # API Endpoints
  #----------------------------------------------------------------------------#

  # Create an endpoint to handle GET requests for all available categories
  @app.route('/categories', methods=['GET'])
  def get_categories():
    categories = Category.query.order_by(Category.type).all()
    if len(categories) == 0:
      abort(404)
    return jsonify({
      'success': True,
      'categories': {
        category.id: category.type for category in categories
      }
    })
  
  # Create an endpoint to handle GET requests for questions,
  # including pagination (every 10 questions). 
  # This endpoint returns a list of questions, number of total questions,
  # current category, categories. 
  @app.route('/questions', methods=['GET'])
  def get_questions():
    results = Question.query.order_by(Question.id).all()
    selection = get_pagination(request, results)

    if (len(selection) == 0):
      abort(404)

    categories = Category.query.order_by(Category.type).all()

    return jsonify({
      'success': True,
      'questions': selection,
      'total_questions': len(results),
      'categories': {
        c.id: c.type for c in categories
      },
    })

  # Create an endpoint to DELETE question using a question ID. 
  @app.route('/questions/<int:question_id>', methods=['DELETE'])
  def delete_question(question_id):
    try:
      question = Question.query.get(question_id)
      if not question:
        abort(404)
      question.delete()
      return jsonify({
        'success': True,
        'deleted': question_id,
      })
    except Exception:
      abort(422)

  
  # Create an endpoint to POST a new question, which will require
  # the question and answer text, category, and difficulty score.
  @app.route('/questions', methods=['POST'])
  def create_question():
    if not request.method == 'POST':
      abort(405)
    body = request.get_json()
    question = body.get('question')
    answer = body.get('answer')
    category = body.get('category')
    difficulty = body.get('difficulty')
    if not (question and answer and category and difficulty):
      abort(422)
    try:
      new_question_data = Question(
        question,
        answer,
        category,
        difficulty
      )
      new_question_data.insert()
      results = Question.query.order_by(Question.id).all()
      selection = get_pagination(request, results)
      return jsonify({
        'success': True,
        'questions': selection,
      })
    except Exception:
      abort(422)

  # Create a POST endpoint to get questions based on a search term.
  # It should return any questions for whom the search term is a substring of the question. 
  @app.route('/questions/search', methods=['POST'])
  def search_questions():
    if not request.method == 'POST':
      abort(405)
    body = request.get_json()
    search_term = body.get('searchTerm', None)
    try:
      categories = Category.query.order_by(Category.type).all()
      results = Question.query.filter(Question.question.ilike(f'%{search_term}%')).all()
      selection = get_pagination(request, results)
      return jsonify({
        'success': True,
        'status': 200,
        'questions': selection,
        'total_questions': len(results),
        'categories': {
          c.id: c.type for c in categories
        },
      })
    except:
      abort(422)

  # Create a GET endpoint to get questions based on category.
  @app.route('/categories/<int:category_id>/questions', methods=['GET'])
  def get_questions_by_category(category_id):
    results = Question.query.filter(Question.category == category_id).all()
    questions = get_pagination(request, results)
    if len(questions) == 0:
      abort(404)
    return jsonify({
      'success': True,
      'questions': questions,
      'total_questions': len(questions),
      'current_category': category_id,
    })
  
  # Create a POST endpoint to get questions to play the quiz. 
  # This endpoint should take category and previous question parameters 
  # and return a random questions within the given category, 
  # if provided, and that is not one of the previous questions. 
  '''
  TEST: In the "Play" tab, after a user selects "All" or a category,
  one question at a time is displayed, the user is allowed to answer
  and shown whether they were correct or not. 
  '''
  @app.route('/quizzes', methods=['POST'])
  def play_quiz():
    try:
      body = request.get_json()
      previous_questions = body.get('previous_questions', None)
      quiz_category = body.get('quiz_category', None)
      if not previous_questions:
        # if the first question in quiz
        if int(quiz_category['id']) > 0:
          # if category selected
          result = Question.query.filter(Question.category == str(quiz_category['id'])).all()
        else:
          # if no category selected
          result = Question.query.all()
      else:
        # if not the first question in quiz
        if int(quiz_category['id']) > 0:
          # if category selected
          result = Question.query.filter(Question.category == str(quiz_category['id'])).filter(Question.id.notin_(previous_questions)).all()
        else:
          # if no category selected
          result = Question.query.filter(Question.id.notin_(previous_questions)).all()
      questions = [q.format() for q in result]
      question = questions[random.randint(0, len(questions))]
      return jsonify({
        'success': True,
        'question': question
      })
    except Exception:
      abort(422)

  # Error Handlers
  #----------------------------------------------------------------------------#

  # Create error handlers for all expected errors including 404 and 422. 
  
  @app.errorhandler(400)
  def bad_request(e):
    return jsonify({
      'success': False,
      'error': 400,
      'message': 'Bad Request'
    }), 400

  @app.errorhandler(404)
  def resource_not_found(e):
    return jsonify({
      'success': False,
      'error': 404,
      'message': 'Resource Not Found'
    }), 404

  @app.errorhandler(405)
  def method_not_allowed(e):
    return jsonify({
      'success': False,
      'error': 405,
      'message': 'Method Not Allowed'
    }), 405

  @app.errorhandler(422)
  def unprocessable(e):
    return jsonify({
      'success': False,
      'error': 422,
      'message': 'Unprocessable'
    }), 422

  @app.errorhandler(500)
  def internal_server_error(e):
    return jsonify({
      'success': False,
      'error': 500,
      'message': 'Internal Server Error'
    }), 500

  return app

    