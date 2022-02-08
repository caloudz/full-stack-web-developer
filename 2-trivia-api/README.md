# Full Stack API Final Project

## Full Stack Trivia

This application has the following functionality:

1. Display questions - both all questions and by category. Questions should show the question, category and difficulty rating by default and can show/hide the answer.
2. Delete questions.
3. Add questions and require that they include question and answer text.
4. Search for questions based on a text query string.
5. Play the quiz game, randomizing either all questions or within a specific category.

## About the Stack

### Backend

The [./backend](https://github.com/udacity/FSND/blob/master/projects/02_trivia_api/starter/backend/README.md) directory contains a partially completed Flask and SQLAlchemy server.

### Frontend

The [./frontend](https://github.com/udacity/FSND/blob/master/projects/02_trivia_api/starter/frontend/README.md) directory contains a complete React frontend to consume the data from the Flask server. 

## Installing Dependencies

### Node and NPM

This project depends on NodeJS and Node Package Manager (NPM). You may download and install Node (the download includes NPM) from [https://nodejs.com/en/download](https://nodejs.org/en/download/).

This project uses NPM to manage software dependencies. NPM relies on the `package.json` file which is located in the `frontend` folder. In Terminal, run:

```bash
npm install
```

## Running the App

### Running Backend

```bash
export FLASK_APP=flaskr
export FLASK_ENV=development
flask run
```

## Running Frontend in Dev Mode

```bash
npm start
```

Open [http://localhost:3000](http://localhost:3000) to view in browser. The page will automatically reload when changes are made.