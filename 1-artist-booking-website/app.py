#----------------------------------------------------------------------------#
# Imports
#----------------------------------------------------------------------------#

import json
import dateutil.parser
import babel
from flask import Flask, render_template, request, Response, flash, redirect, url_for
from flask_moment import Moment
from flask_migrate import Migrate
from flask_sqlalchemy import SQLAlchemy
import logging
from logging import Formatter, FileHandler
from flask_wtf import Form
from forms import *
from config import SQLALCHEMY_DATABASE_URI
from models import *

#----------------------------------------------------------------------------#
# App Config
#----------------------------------------------------------------------------#

app = Flask(__name__)
moment = Moment(app)
app.config.from_object('config')
db = SQLAlchemy(app)
migrate = Migrate(app, db)

app.config['SQLALCHEMY_DATABASE_URI'] = SQLALCHEMY_DATABASE_URI
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False 

#----------------------------------------------------------------------------#
# Filters
#----------------------------------------------------------------------------#

def format_datetime(value, format='medium'):
  date = dateutil.parser.parse(value)
  if format == 'full':
      format="EEEE MMMM, d, y 'at' h:mma"
  elif format == 'medium':
      format="EE MM, dd, y h:mma"
  return babel.dates.format_datetime(date, format, locale='en')

app.jinja_env.filters['datetime'] = format_datetime

#----------------------------------------------------------------------------#
# Controllers
#----------------------------------------------------------------------------#

@app.route('/')
def index():
  # Bonus: Show Recent Listed Artists and Recently Listed Venues on the homepage,
  # returning results for Artists and Venues sorting by newly created.
  # Limit to the 10 most recently listed items.
  recent_artists = Artist.query.order_by(Artist.id.desc()).limit(10).all()
  recent_venues = Venue.query.order_by(Venue.id.desc()).limit(10).all()
  return render_template('pages/home.html', recent_artists = recent_artists, recent_venues = recent_venues)

#  Venues
#  ----------------------------------------------------------------

@app.route('/venues')
def venues():
  data = []
  try:
    areas = Venue.query.distinct(Venue.city, Venue.state).all()
    data = [
      dict(
        city = area.city, 
        state = area.state, 
        venues=[
          dict(
            id = venue.id,
            name = venue.name
            ) for venue in Venue.query.filter(Venue.city == area.city, Venue.state == area.state).all()
          ]
        ) for area in areas
      ]
    return render_template('pages/venues.html', areas=data);
  except:
    flash('Oops! An error occurred. Venues cannot be displayed.')
    return redirect(url_for('index'))

@app.route('/venues/search', methods=['POST'])
def search_venues():
  data = []
  try:
    search_term = request.form.get('search_term', '')
    search_results = Venue.query.filter(Venue.name.ilike(f'%{search_term}%')).all()
    for venue in search_results:
      data.append({
        "id": venue.id,
        "name": venue.name
      })
    response = {
      "data": data,
      "count": len(data)
    }
    return render_template('pages/search_venues.html', results=response, search_term=request.form.get('search_term', ''))
  except:
    flash('Oh no! An error occurred while searching.')
    return redirect(url_for('venues'))

@app.route('/venues/<int:venue_id>')
def show_venue(venue_id):
  # shows the venue page with the given venue_id
  venue = Venue.query.filter_by(id=venue_id).all()[0]
  data={
    "id": venue.id,
    "name": venue.name,
    "genres": venue.genres,
    "address": venue.address,
    "city": venue.city,
    "state": venue.state,
    "phone": venue.phone,
    "website_link": venue.website_link,
    "facebook_link": venue.facebook_link,
    "seeking_talent": venue.seeking_talent,
    "seeking_description": venue.seeking_description,
    "image_link": venue.image_link,
    "past_shows": [],
    "upcoming_shows": []
  }
  shows = db.session.query(Show, Artist).filter_by(venue_id=venue_id).join(Artist).all()
  for (show, artist) in shows:
    if (show.start_time < datetime.now()):
      add_to = "past_shows"
    else:
      add_to = "upcoming_shows"
    data[add_to].append({
      "artist_id": artist.id,
      "artist_name": artist.name,
      "artist_image_link": artist.image_link,
      "start_time": show.start_time.strftime("%m/%d/%Y, %H:%M:%S")
    })
  data["past_shows_count"] = len(data["past_shows"])
  data["upcoming_shows_count"] = len(data["upcoming_shows"])
  return render_template('pages/show_venue.html', venue=data)

#  Create Venue
#  ----------------------------------------------------------------

@app.route('/venues/create', methods=['GET'])
def create_venue_form():
  form = VenueForm(request.form, meta={'csrf': False})
  return render_template('forms/new_venue.html', form=form)

@app.route('/venues/create', methods=['POST'])
def create_venue_submission():
  try:
    form = VenueForm(request.form, meta={'csrf': False})
    if request.method == 'POST' and form.validate():
      venue = Venue(
        name = request.form['name'],
        city = request.form['city'],
        state = request.form['state'],
        address = request.form['address'],
        phone = request.form['phone'],
        genres = request.form.getlist('genres'), 
        facebook_link = request.form['facebook_link'],
        image_link = request.form['image_link'],
        website_link = request.form['website_link'],
        seeking_talent = True if 'seeking_talent' in request.form else False,
        seeking_description = request.form['seeking_description']
        )
      db.session.add(venue)
      db.session.commit()
      flash('Yay! Venue ' + request.form['name'] + ' was successfully listed!')
    else:
      response = "Oops! There are errors in the following fields: "
      for error in form.errors:
        response += error + ", "
      flash(response)
  except:
    db.session.rollback()
    flash('Oops! An error occurred. Venue ' + request.form['name'] + ' could not be listed.')
  finally:
    db.session.close()
  return render_template('pages/home.html')

@app.route('/venues/<venue_id>', methods=['DELETE'])
def delete_venue(venue_id):
  try:
    # delete the shows associated with the venue, then delete the venue itself
    Show.query.filter_by(venue_id = venue_id).delete()
    Venue.query.filter_by(id = venue_id).delete()
    db.session.commit()
    flash('Aw, goodbye. Venue ' + request.form['name'] + ' and its shows have been deleted.')
  except:
    flash('An error occurred when trying to delete the venue ' + request.form['name'] + '.')
    db.session.rollback()
    print(sys.exc_info())
  finally:
    db.session.close()
  return redirect(url_for('index'))

#  Artists
#  ----------------------------------------------------------------
@app.route('/artists')
def artists():
  data = []
  try:
    # query artists alphabetically
    artists = Artist.query.order_by(Artist.name.asc()).all()
    for artist in artists:
      data.append({
        "id": artist.id,
        "name": artist.name
      })
    return render_template('pages/artists.html', artists = data)
  except:
    flash('Oops! An error occurred. Artists cannot be displayed.')
    return redirect(url_for('index'))

@app.route('/artists/search', methods=['POST'])
def search_artists():
  data = []
  try:
    search_term = request.form.get('search_term', '')
    search = Artist.query.filter(Artist.name.ilike(f'%{search_term}%')).all()
    for artist in search:
      data.append({
        "id": artist.id,
        "name": artist.name
      })
    response={
      "data": data,
      "count": len(data)
    }
    return render_template('pages/search_artists.html', results=response, search_term=request.form.get('search_term', ''))
  except:
    flash('Oh no! An error occurred while searching.')
    return redirect(url_for('artists'))

@app.route('/artists/<int:artist_id>')
def show_artist(artist_id):
  # shows the artist page with the given artist_id
  artist = Artist.query.filter_by(id = artist_id).all()[0]
  data = {
    "id": artist.id,
    "name": artist.name,
    "genres": artist.genres,
    "city": artist.city,
    "state": artist.state,
    "phone": artist.phone,
    "website_link": artist.website_link,
    "facebook_link": artist.facebook_link,
    "seeking_venue": artist.seeking_venue,
    "seeking_description": artist.seeking_description,
    "image_link": artist.image_link,
    "past_shows": [],
    "upcoming_shows": []
  }
  shows = db.session.query(Show, Venue).filter_by(artist_id = artist_id).join(Venue).all()
  for (show, venue) in shows:
    if(show.start_time < datetime.now()):
      add_to = "past_shows"
    else:
      add_to = "upcoming_shows"
    data[add_to].append({
      "venue_id": venue.id,
      "venue_name": venue.name,
      "venue_image_link": venue.image_link,
      "start_time": show.start_time.strftime("%m/%d/%Y, %H:%M:%S")
    })
  data["past_shows_count"] = len(data["past_shows"])
  data["upcoming_shows_count"] = len(data["upcoming_shows"])
  return render_template('pages/show_artist.html', artist=data)

#  Create Artist
#  ----------------------------------------------------------------

@app.route('/artists/create', methods=['GET'])
def create_artist_form():
  form = ArtistForm(request.form, meta = {'csrf': False})
  return render_template('forms/new_artist.html', form=form)

@app.route('/artists/create', methods=['POST'])
def create_artist_submission():
  # called upon submitting the new artist listing form
  try:
    form = ArtistForm(request.form, meta = {'csrf': False})
    if request.method == 'POST' and form.validate():
      artist = Artist(
        name = request.form['name'],
        city = request.form['city'],
        state = request.form['state'],
        phone = request.form['phone'],
        genres = request.form.getlist('genres'),
        facebook_link = request.form['facebook_link'],
        image_link = request.form['image_link'],
        website_link = request.form['website_link'],
        seeking_venue =  True if 'seeking_venue' in request.form else False,
        seeking_description = request.form['seeking_description']
        )
      db.session.add(artist)
      db.session.commit()
      flash('Yay! Artist ' + request.form['name'] + ' was successfully listed!')
    else:
      response = "Oops! There are errors in the following fields: "
      for error in form.errors:
        response += error + ", "
      flash(response)
  except:
    db.session.rollback()
    flash('Oops! An error occurred. Artist ' + request.form['name'] + ' could not be listed.')
  finally:
    db.session.close()
  return render_template('pages/home.html')

@app.route('/artists/<artist_id>', methods=['DELETE'])
def delete_artist(artist_id):
  try:
    Show.query.filter_by(artist_id = artist_id).delete()
    Artist.query.filter_by(id = artist_id).delete()
    db.session.commit()
    flash('Aw, goodbye. Artist ' + request.form['name'] + ' and their shows have been deleted.')
  except:
    flash('An error occurred when trying to delete the artist ' + request.form['name'] + '.')
    db.session.rollback()
  finally:
    db.session.close()

  return redirect(url_for('index'))

#  Update
#  ----------------------------------------------------------------
@app.route('/artists/<int:artist_id>/edit', methods=['GET'])
def edit_artist(artist_id):
  # fetch data and pre-fill form with existing data
  artist = Artist.query.filter_by(id=artist_id).first_or_404()
  form = ArtistForm(obj=artist)
  return render_template('forms/edit_artist.html', form=form, artist=artist)

@app.route('/artists/<int:artist_id>/edit', methods=['POST'])
def edit_artist_submission(artist_id):
  form = ArtistForm(request.form)
  artist = Artist.query.first_or_404(artist_id)
  try:
    form.populate_obj(artist)
    db.session.commit()
    flash('Yay! Artist ' + request.form['name'] + ' was successfully updated!')
  except ValueError as e:
    db.session.rollback()
    flash(f'An error occurred in {form.name.data}. Error: {str(e)}')
  finally:
    db.session.close()
  return redirect(url_for('show_artist', artist_id=artist_id))
  
@app.route('/venues/<int:venue_id>/edit', methods=['GET'])
def edit_venue(venue_id):
  # fetch data and pre-fill form with existing data
  venue = Venue.query.filter_by(id = venue_id).first_or_404()
  form = VenueForm(obj=venue)
  return render_template('forms/edit_venue.html', form=form, venue=venue)

@app.route('/venues/<int:venue_id>/edit', methods=['POST'])
def edit_venue_submission(venue_id):
  form = VenueForm(request.form)
  venue = Venue.query.first_or_404(venue_id)
  try:
    form.populate_obj(venue)
    db.session.commit()
    flash('Yay! Venue ' + request.form['name'] + ' was successfully updated!')
  except ValueError as e:
    db.session.rollback()
    flash(f'An error occurred in {form.name.data}. Error: {str(e)}')
  finally:
    db.session.close()
  return redirect(url_for('show_venue', venue_id=venue_id))

#  Shows
#  ----------------------------------------------------------------

@app.route('/shows')
def shows():
  # displays list of shows at /shows
  data = []
  shows = db.session.query(Show, Venue, Artist).join(Venue).join(Artist).all()
  for (show, venue, artist) in shows:
    data.append({
      "venue_id": venue.id,
      "venue_name": venue.name,
      "artist_id": artist.id,
      "artist_name": artist.name,
      "artist_image_link": artist.image_link,
      "start_time": show.start_time.strftime("%m/%d/%Y, %H:%M:%S")
    })
  return render_template('pages/shows.html', shows=data)

@app.route('/shows/create')
def create_shows():
  # renders form
  form = ShowForm()
  return render_template('forms/new_show.html', form=form)

@app.route('/shows/create', methods=['POST'])
def create_show_submission():
  # called to create new shows in the db, upon submitting new show listing form
  try:
    form = ShowForm(request.form, meta={'csrf': False})
    if request.method == 'POST' and form.validate():
      show = Show(
        artist_id = form.artist_id.data,
        venue_id = form.venue_id.data,
        start_time = form.start_time.data
      )
      db.session.add(show)
      db.session.commit()
      flash('Yay! Show was successfully listed.')
    else:
      response = "Oops! There are errors in the following fields: "
      for error in form.errors:
        response += error + ", "
      flash(response)
  except:
    db.session.rollback()
    flash('Oops! An error occurred. Show could not be listed.')
  finally:
    db.session.close()
  return render_template('pages/home.html')

@app.errorhandler(404)
def not_found_error(error):
    return render_template('errors/404.html'), 404

@app.errorhandler(500)
def server_error(error):
    return render_template('errors/500.html'), 500

if not app.debug:
    file_handler = FileHandler('error.log')
    file_handler.setFormatter(
        Formatter('%(asctime)s %(levelname)s: %(message)s [in %(pathname)s:%(lineno)d]')
    )
    app.logger.setLevel(logging.INFO)
    file_handler.setLevel(logging.INFO)
    app.logger.addHandler(file_handler)
    app.logger.info('errors')

#----------------------------------------------------------------------------#
# Launch.
#----------------------------------------------------------------------------#

# Default port:
if __name__ == '__main__':
    app.run()

# Or specify port manually:
'''
if __name__ == '__main__':
    port = int(os.environ.get('PORT', 5000))
    app.run(host='0.0.0.0', port=port)
'''
