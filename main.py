import os

import requests
from flask import Flask, render_template, redirect, url_for
from flask_bootstrap import Bootstrap5
from flask_sqlalchemy import SQLAlchemy
from flask_wtf import FlaskForm
from sqlalchemy import Integer, String, Float
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column
from wtforms import StringField, SubmitField
from wtforms.validators import DataRequired

api_key = os.environ['API_KEY']
api_token = os.environ['API_TOKEN']

app = Flask(__name__)
app.config['SECRET_KEY'] = os.environ['SECRET_KEY']
app.config["SQLALCHEMY_DATABASE_URI"] = "sqlite:///movies.db"
Bootstrap5(app)


# CREATE DB
class Base(DeclarativeBase):
    pass


db = SQLAlchemy(model_class=Base)
db.init_app(app)


class Movie(db.Model):   # Creating Database and schema
    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    title: Mapped[str] = mapped_column(String(250), nullable=False, unique=True)
    img_url: Mapped[str] = mapped_column(String(250), nullable=False, unique=True)
    year: Mapped[int] = mapped_column(Integer, nullable=False)
    rating: Mapped[float] = mapped_column(Float, nullable=True)
    review: Mapped[str] = mapped_column(String(250), nullable=True)
    description: Mapped[str] = mapped_column(String(500), nullable=False)
    ranking: Mapped[int] = mapped_column(Integer, nullable=True)


with app.app_context():
    db.create_all()


class MovieForm(FlaskForm):
    rating = StringField('Your Rating out of 10')
    review = StringField('Your Review')
    submit = SubmitField('Submit')


class AddMovieForm(FlaskForm):
    movie = StringField("Enter The Movie Title", validators=[DataRequired()])
    submit = SubmitField('Submit')


@app.route("/")
def home():
    movies = db.session.execute(db.select(Movie).order_by(Movie.rating.desc())).scalars().all()
    rating_list = []
    for movie in movies:
        rating_list.append(movie)
    with app.app_context():
        for i in range(len(rating_list)):
            movie = rating_list[i]
            movie.ranking = i + 1
        db.session.commit()
    return render_template("index.html", movies=movies)


@app.route("/add", methods=["GET", "POST"])
def add():
    form = AddMovieForm()
    if form.validate_on_submit():
        search_url = "https://api.themoviedb.org/3/search/movie"
        title = form.movie.data
        response = requests.get(search_url, params={"api_key": api_key, "query": title})
        data = response.json()["results"]
        return render_template("select.html", movies=data)
    return render_template("add.html", form=form)


@app.route("/find/<int:movie_id>", methods=["GET", "POST"])
def find(movie_id):
    link_url = f"https://api.themoviedb.org/3/movie/{movie_id}"
    link_request = requests.get(link_url, params={"api_key": api_key})
    response = link_request.json()
    new_movie = Movie(
        id=movie_id,
        title=response["title"],
        year=response["release_date"].split("-")[0],
        img_url=f"https://image.tmdb.org/t/p/w500{response['poster_path']}",
        description=response["overview"]
    )
    db.session.add(new_movie)
    db.session.commit()
    return redirect(url_for("edit", movie_id=movie_id))


@app.route("/edit/<int:movie_id>", methods=["GET", "POST"])
def edit(movie_id):
    form = MovieForm()
    with app.app_context():
        movie = db.session.execute(db.select(Movie).where(Movie.id == movie_id)).scalar()
        if form.validate_on_submit():
            try:
                movie.rating = float(form.rating.data)
            except ValueError:
                movie.rating = movie.rating
            finally:
                movie.review = form.review.data
                db.session.commit()
            return redirect(url_for("home"))
    return render_template("edit.html", movie=movie, form=form)


@app.route("/delete/<int:movie_id>", methods=["GET", "POST"])
def delete(movie_id):
    with app.app_context():
        movie = db.session.execute(db.select(Movie).where(Movie.id == movie_id)).scalar()
        db.session.delete(movie)
        db.session.commit()
    return redirect("/")


if __name__ == '__main__':
    app.run(debug=True, port=3000)
