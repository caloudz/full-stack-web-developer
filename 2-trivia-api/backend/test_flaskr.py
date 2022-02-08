import os
import unittest
import json
from flask_sqlalchemy import SQLAlchemy

from flaskr import create_app
from models import setup_db, Question, Category


class TriviaTestCase(unittest.TestCase):
    """This class represents the trivia test case"""

    def setUp(self):
        """Define test variables and initialize app."""
        self.app = create_app()
        self.client = self.app.test_client
        self.database_name = "trivia_test"
        self.database_path = "postgresql://{}/{}".format('localhost:5432', self.database_name)
        setup_db(self.app, self.database_path)

        # binds the app to the current context
        with self.app.app_context():
            self.db = SQLAlchemy()
            self.db.init_app(self.app)
            # create all tables
            self.db.create_all()
    
    def tearDown(self):
        """Executed after reach test"""
        pass

    # General
    #----------------------------------------------------------------------------#
    
    def test_get_endpoint_fail(self):
        """
        Endpoint does not exist.
        /question does not exist - the correct endpoint is plural: /questions.
        """
        res = self.client().get('/question')
        data = json.loads(res.data)
        self.assertEqual(res.status_code, 404)
        self.assertEqual(data['error'], 404)
        self.assertEqual(data['success'], False)
        self.assertEqual(data['message'], 'Resource Not Found')

    # /categories GET
    #----------------------------------------------------------------------------#

    def test_get_categories_success(self):
        """
        GET request for all available categories.
        """
        res = self.client().get('/categories')
        data = json.loads(res.data)
        self.assertEqual(res.status_code, 200)
        self.assertEqual(data['success'], True)
        self.assertTrue(data['categories'])

    # /questions GET
    #----------------------------------------------------------------------------#

    def test_get_questions_success(self):
        """
        GET request for all questions from all categories.
        JSON body should not have any impact.
        """
        res = self.client().get('/questions?page=1')
        data = json.loads(res.data)
        self.assertEqual(res.status_code, 200)
        self.assertTrue(data['success'], True)
        self.assertTrue(len(data['categories']))
        self.assertTrue(data['total_questions'])
        self.assertTrue(len(data['questions']) <= 10)
        self.assertTrue(len(data['questions']) <= data['total_questions'])

    def test_get_questions_paginated_fail(self):
        """
        GET request for all questions from all categories for a page that is out of range.
        """
        res = self.client().get('/questions?page=99999')
        data = json.loads(res.data)
        self.assertEqual(res.status_code, 404)
        self.assertEqual(data['success'], False)
        self.assertEqual(data['message'], 'Resource Not Found')

    # /questions DELETE
    #----------------------------------------------------------------------------#
    def test_delete_question_success(self):
        """
        DELETE a question.
        """
        q = Question(
            question = 'What is your quest?',
            answer='To seek the Holy Grail!',
            difficulty=1,
            category=1
        )
        q.insert()
        q_id = q.id
        res = self.client().delete('/questions/{}'.format(q_id))
        data = json.loads(res.data)
        self.assertEqual(res.status_code, 200)
        self.assertEqual(data['success'], True)
        self.assertEqual(data['deleted'], int(q_id))

    def test_delete_question_not_exist_fail(self):
        """
        Fail to DELETE a non-existing question.
        """
        res = self.client().delete(f'/questions/99999')
        data = json.loads(res.data)
        self.assertEqual(res.status_code, 422)
        self.assertEqual(data['error'], 422)
        self.assertEqual(data['success'], False)
        self.assertEqual(data['message'], 'Unprocessable')

    # /questions POST
    #----------------------------------------------------------------------------#

    def test_create_question_method_fail(self):
        """
        Fail to POST new question due to unauthorized method.
        """
        res = self.client().patch('/questions')
        data = json.loads(res.data)
        self.assertEqual(res.status_code, 405)
        self.assertEqual(data['success'], False)
        self.assertEqual(data['message'], 'Method Not Allowed')

    def test_create_question_missing_fields_fail(self):
        """
        Fail to POST new question due to missing fields.
        In this case we dont send the JSON key category.
        """
        test_json = {
            'question': '',
            'answer': None,
            'category': None,
            'difficulty': None
        }
        res = self.client().post('/questions', json=test_json)
        data = json.loads(res.data)
        self.assertEqual(res.status_code, 422)
        self.assertEqual(data['success'], False)
        self.assertEqual(data['message'], 'Unprocessable')

    def test_create_question_success(self):
        """
        POST a new question.
        """
        test_json = {
            'question': 'How do you write tests?',
            'answer': 'Thorough',
            'category': 1,
            'difficulty': 5
        }
        res = self.client().post('/questions', json=test_json)
        data = json.loads(res.data)
        self.assertEqual(res.status_code, 200)
        self.assertTrue(data['success'])
        self.assertTrue(data['questions'])

    # Search question
    #----------------------------------------------------------------------------#

    def test_search_questions_method_fail(self):
        """
        Fail to search with a search term due to unauthorized method.
        """
        test_json = {
            'searchTerm' : 'hanks',
        } 
        res = self.client().patch('/questions/search', json=test_json)
        data = json.loads(res.data)
        self.assertEqual(res.status_code, 405)
        self.assertEqual(data['success'], False)
        self.assertEqual(data['message'], 'Method Not Allowed')

    def test_search_questions_success(self):
        """
        Successfully search with a search term.
        """
        test_json = {
            'searchTerm' : 'hanks',
        } 
        res = self.client().post('/questions/search', json=test_json)
        data = json.loads(res.data)
        self.assertEqual(res.status_code, 200)
        self.assertEqual(data['success'], True)
        self.assertTrue(data['total_questions'])
        self.assertTrue(len(data['questions']))
        self.assertTrue(len(data['questions'] )<= 10)
        self.assertTrue(len(data['questions']) <= data['total_questions'])

    # /categories/<string:category_id>/questions GET
    #----------------------------------------------------------------------------#

    def test_get_questions_by_category_success(self):
        """
        Get all questions from category ID 1.
        """
        res = self.client().get('/categories/1/questions')
        data = json.loads(res.data)
        self.assertEqual(res.status_code, 200)
        self.assertTrue(data['success'], True)
        self.assertTrue(data['total_questions'])
        self.assertTrue(len(data['questions']) <= 10)
        self.assertTrue(len(data['questions']) <= data['total_questions'])
        self.assertEqual(data['current_category'], 1)

    def test_get_questions_by_category_fail(self):
        """
        Fail to get all questions from a non-existent category.
        """
        res = self.client().get('/categories/99999/questions')
        data = json.loads(res.data)
        self.assertEqual(res.status_code, 404)
        self.assertEqual(data['success'], False)
        self.assertEqual(data['message'], 'Resource Not Found')

    # /quizzes POST
    #----------------------------------------------------------------------------#

    def test_play_quiz_category_first_success(self):
        """
        Play quiz with all questions of a certain category, first question.
        """
        test_json = {
            'previous_questions': [],
            'quiz_category': {
                'id': 1,
                'type': 'Science'
            }
        }
        res = self.client().post('/quizzes', json=test_json)
        data = json.loads(res.data)
        self.assertEqual(res.status_code, 200)
        self.assertTrue(data['success'], True)

    def test_play_quiz_category_subsequent_success(self):
        """
        Play quiz with all questions of a certain category, not first question.
        """
        test_json = {
            'previous_questions': [5, 10],
            'quiz_category': {
                'id': 1,
                'type': 'Science'
            }
        }
        res = self.client().post('/quizzes', json=test_json)
        data = json.loads(res.data)
        self.assertEqual(res.status_code, 200)
        self.assertTrue(data['success'], True)
        self.assertTrue(data['question']['question'])

    def test_play_quiz_method_fail(self):
        """
        Fail to play due to unauthorized method.
        """
        res = self.client().get('/quizzes')
        data = json.loads(res.data)
        self.assertEqual(res.status_code, 405)
        self.assertEqual(data['error'], 405)
        self.assertEqual(data['success'], False)
        self.assertEqual(data['message'], 'Method Not Allowed')

# Make the tests conveniently executable
if __name__ == "__main__":
    unittest.main()