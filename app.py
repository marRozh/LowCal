import os
import random

from flask import Flask, render_template, redirect, session, jsonify, flash, request, make_response
from flask_session import Session
from tempfile import mkdtemp
from werkzeug.exceptions import default_exceptions, HTTPException, InternalServerError
from werkzeug.security import check_password_hash, generate_password_hash

#from werkzeug.middleware.proxy_fix import ProxyFix
#from cachelib.file import FileSystemCache

from helpers import login_required, apology

import sqlite3
con = sqlite3.connect("lowcal.db", check_same_thread=False)
con.row_factory = sqlite3.Row
db = con.cursor()

app = Flask(__name__)

# Ensure responses aren't cached
@app.after_request
def after_request(response):
    response.headers["Cache-Control"] = "no-cache, no-store, must-revalidate"
    response.headers["Expires"] = 0
    response.headers["Pragma"] = "no-cache"
    return response

# Configure session to use filesystem (instead of signed cookies)
app.config["SESSION_FILE_DIR"] = mkdtemp()
app.config["SESSION_PERMANENT"] = False
app.config["SESSION_TYPE"] = "filesystem"
Session(app)

@app.route("/register", methods=["GET", "POST"])
def register():
    session.clear()
    if request.method == "GET":
        return render_template("register.html")
    else:
        name = request.form.get("name")
        email = request.form.get("email")
        if not name or not email:
            return apology("Please enter your name and email", 403)
        db.execute("SELECT * FROM users WHERE email=:email", {"email": email})
        rows = db.fetchall()
        if len(rows) > 0:
            return apology("Username already exists", 403)
        password = generate_password_hash(request.form.get("password"))
        if not request.form.get("password"):
            return apology("Please enter a password", 403)
        if (request.form.get("password") != request.form.get("repeat-password")):
            return apology("Passwords do not match", 403)
        db.execute("INSERT INTO users (hash, name, email) VALUES (:password, :name, :email)", {"password": password, "name": name, "email": email})
        con.commit()
        return redirect("/login")


@app.route("/login", methods=["GET", "POST"])
def login():
    session.clear()
    if request.method == "GET":
        return render_template("login.html")
    else:
        email = request.form.get("email")
        if not email:
            return apology("Please enter your email", 403)
        password = request.form.get("password")
        if not password:
            return apology("Please enter your Password", 403)

        db.execute("SELECT * FROM users WHERE email=:email", {"email": email})
        rows = db.fetchall()

        if len(rows) != 1 or not check_password_hash(rows[0]["hash"], password):
            return apology("Invalid User Name and/or Password", 403)
        
        session["user_id"] = rows[0]["id"]

        return redirect("/")

@app.route("/logout")
def logout():
    session.clear()
    return redirect("/")

@app.route("/", methods=["GET", "POST"])
@login_required
def index():
    if request.method == "GET":
        db.execute("SELECT * FROM user_recipe WHERE user_id=:id", {'id': session["user_id"]})
        rows = db.fetchall()
        if not rows:
            return render_template("emptyindex.html")
        else:
            return render_template("index.html")
    else:
        meal = request.form.get("meal")
        db.execute("SELECT * FROM user_recipe WHERE user_id=:id AND category LIKE :meal", {'id': session["user_id"], 'meal': meal})
        rows = db.fetchall()
        count = 0
        for row in rows:
            count += 1
        if count == 0:
            return apology("You don't have any recipes saved under this category", 403)
        else: 
            return render_template("index.html", rows=rows)

@app.route("/recipes", methods=["GET", "POST"])
@login_required
def recipes():
    if request.method =="GET":
        return render_template("recipes.html")
    else:
        search = request.form.get("recipe-search")
        print(search)
        session['search'] = search
        db.execute("SELECT * FROM recipe WHERE name LIKE ?", ('%' + search + '%',))
        rows = db.fetchall()
        if not rows:
            message = "Sorry, there are no recipes with this ingredient, yet!"
            return render_template("recipes.html", message=message)
        else:
            return render_template("recipes.html", rows=rows)


@app.route("/like", methods=["GET", "POST"])
@login_required
def like():
    if request.method == "POST":
        recid = request.form.get("recipes-like")
        db.execute("SELECT * FROM recipe WHERE rec_id=:id", {'id': recid})
        idrows = db.fetchall()

        db.execute("SELECT rec_id FROM user_recipe WHERE rec_id=:id AND user_id=:userid", {'id': recid, "userid": session["user_id"]})
        existing = db.fetchall()

        search = session.get('search', None)
        db.execute("SELECT * FROM recipe WHERE name LIKE ?", ('%' + search + '%',))
        rows = db.fetchall()

        if not existing:
            db.execute("INSERT INTO user_recipe (rec_id, name, cal_per_rec, category, servings, prep_time, rec_text, ingredients, user_id) VALUES (:rec_id, :name, :cal_per_rec, :category, :servings, :prep_time, :rec_text, :ingredients, :user_id)", {'rec_id': recid, 'name': idrows[0]["name"], 'cal_per_rec': idrows[0]["cal_per_rec"], 'category': idrows[0]["category"], 'servings': idrows[0]["servings"], 'prep_time': idrows[0]["prep_time"], 'rec_text': idrows[0]["rec_text"], 'ingredients': idrows[0]["ingredients"], 'user_id': session["user_id"]})
            con.commit()
            return render_template("recipes.html", rows=rows)
        else:
            return apology("You already saved this recipe", 403)


@app.route("/addrecipe", methods=["GET", "POST"])
@login_required
def addrecipe():
    if request.method == 'GET':
        return render_template("addrecipe.html")
    else:
        name = request.form.get("name")
        cals = request.form.get("cals")
        addcategory = request.form.getlist("addcategory")
        category = ', '.join(addcategory)
        servings = request.form.get("servings")
        time = request.form.get("time")
        recipe = request.form.get("recipe")
        ingredients = request.form.get("ingredients")

        if not name or not cals or not addcategory or not servings or not time or not recipe or not ingredients:
            return apology("Please fill in all of the fields", 403)
        else:
            db.execute("INSERT INTO recipe (name, cal_per_rec, category, servings, prep_time, rec_text, ingredients) VALUES (:name, :cal_per_rec, :category, :servings, :prep_time, :rec_text, :ingredients)", {'name': name, 'cal_per_rec': cals, 'category': category, 'servings': servings, 'prep_time': time, 'rec_text': recipe, 'ingredients': ingredients})
            con.commit()
            db.execute("SELECT rec_id FROM recipe WHERE name=:name", {'name': name})
            rows = db.fetchall()
            recid = rows[0]['rec_id']
            db.execute("INSERT INTO user_recipe (rec_id, name, cal_per_rec, category, servings, prep_time, rec_text, ingredients, user_id) VALUES (:rec_id, :name, :cal_per_rec, :category, :servings, :prep_time, :rec_text, :ingredients, :user_id)", {'rec_id': recid,'name': name, 'cal_per_rec': cals, 'category': category, 'servings': servings, 'prep_time': time, 'rec_text': recipe, 'ingredients': ingredients, 'user_id': session["user_id"]})
            con.commit()

            return render_template("addrecipe.html")

@app.route("/meals", methods=["GET", "POST"])
@login_required
def meals():
    if request.method == "GET":
        return render_template("meals.html")
    else:
        #Random Breakfast
        category = 'breakfast'
        db.execute("SELECT * FROM user_recipe WHERE user_id=:id AND category LIKE :cat", {"id": session["user_id"], "cat": ('%' + category + '%') })
        rows = db.fetchall()
        count = 0
        for row in rows:
            count += 1
        if count == 1:
            breakfast_name = rows[0]["name"]
            breakfast_total_cal = rows[0]["cal_per_rec"]
            breakfast_servings = rows[0]["servings"]
            breakfast_cal_per_serving = breakfast_total_cal / breakfast_servings
            breakfast_recipe = rows[0]["rec_text"]
            breakfast_ingredients = rows[0]["ingredients"]
        elif count > 1:
            random_num = random.randrange(0, count, 1)
            breakfast_name = rows[random_num]["name"]
            breakfast_total_cal = rows[random_num]["cal_per_rec"]
            breakfast_servings = rows[random_num]["servings"]
            breakfast_cal_per_serving = breakfast_total_cal / breakfast_servings
            breakfast_recipe = rows[random_num]["rec_text"]
            breakfast_ingredients = rows[random_num]["ingredients"]
        elif count == 0:
            return apology("You need to add more recipes", 403)

        #Random Snack1
        category = 'snack'
        db.execute("SELECT * FROM user_recipe WHERE user_id=:id AND category LIKE :cat", {"id": session["user_id"], "cat": ('%' + category + '%') })
        rows = db.fetchall()
        count = 0
        for row in rows:
            count += 1
        if count == 1:
            snack_one_name = rows[0]["name"]
            snack_one_total_cal = rows[0]["cal_per_rec"]
            snack_one_servings = rows[0]["servings"]
            snack_one_cal_per_serving = snack_one_total_cal / snack_one_servings
            snack_one_recipe = rows[0]["rec_text"]
            snack_one_ingredients = rows[0]["ingredients"]
        elif count > 1:
            random_num = random.randrange(0, count, 1)
            snack_one_name = rows[random_num]["name"]
            snack_one_total_cal = rows[random_num]["cal_per_rec"]
            snack_one_servings = rows[random_num]["servings"]
            snack_one_cal_per_serving = snack_one_total_cal / snack_one_servings
            snack_one_recipe = rows[random_num]["rec_text"]
            snack_one_ingredients = rows[random_num]["ingredients"]
        elif count == 0:
            return apology("You need to add more recipes", 403)

        #Random Lunch
        category = 'lunch'
        db.execute("SELECT * FROM user_recipe WHERE user_id=:id AND category LIKE :cat", {"id": session["user_id"], "cat": ('%' + category + '%') })
        rows = db.fetchall()
        count = 0
        for row in rows:
            count += 1
        if count == 1:
            lunch_name = rows[0]["name"]
            lunch_total_cal = rows[0]["cal_per_rec"]
            lunch_servings = rows[0]["servings"]
            lunch_cal_per_serving = lunch_total_cal / lunch_servings
            lunch_recipe = rows[0]["rec_text"]
            lunch_ingredients = rows[0]["ingredients"]
        elif count > 1:
            random_num = random.randrange(0, count, 1)
            lunch_name = rows[random_num]["name"]
            lunch_total_cal = rows[random_num]["cal_per_rec"]
            lunch_servings = rows[random_num]["servings"]
            lunch_cal_per_serving = lunch_total_cal / lunch_servings
            lunch_recipe = rows[random_num]["rec_text"]
            lunch_ingredients = rows[random_num]["ingredients"]
        elif count == 0:
            return apology("You need to add more recipes", 403)

        #Random Snack2
        category = 'snack'
        db.execute("SELECT * FROM user_recipe WHERE user_id=:id AND category LIKE :cat", {"id": session["user_id"], "cat": ('%' + category + '%') })
        rows = db.fetchall()
        count = 0
        for row in rows:
            count += 1
        if count == 1:
            snack_two_name = rows[0]["name"]
            snack_two_total_cal = rows[0]["cal_per_rec"]
            snack_two_servings = rows[0]["servings"]
            snack_two_cal_per_serving = snack_two_total_cal / snack_two_servings
            snack_two_recipe = rows[0]["rec_text"]
            snack_two_ingredients = rows[0]["ingredients"]
        elif count > 1:
            random_num = random.randrange(0, count, 1)
            snack_two_name = rows[random_num]["name"]
            snack_two_total_cal = rows[random_num]["cal_per_rec"]
            snack_two_servings = rows[random_num]["servings"]
            snack_two_cal_per_serving = snack_two_total_cal / snack_two_servings
            snack_two_recipe = rows[random_num]["rec_text"]
            snack_two_ingredients = rows[random_num]["ingredients"]
        elif count == 0:
            return apology("You need to add more recipes", 403)

        #Random Dinner
        category = 'dinner'
        db.execute("SELECT * FROM user_recipe WHERE user_id=:id AND category LIKE :cat", {"id": session["user_id"], "cat": ('%' + category + '%') })
        rows = db.fetchall()
        count = 0
        for row in rows:
            count += 1
        if count == 1:
            dinner_name = rows[0]["name"]
            dinner_total_cal = rows[0]["cal_per_rec"]
            dinner_servings = rows[0]["servings"]
            dinner_cal_per_serving = dinner_total_cal / dinner_servings
            dinner_recipe = rows[0]["rec_text"]
            dinner_ingredients = rows[0]["ingredients"]
        elif count > 1:
            random_num = random.randrange(0, count, 1)
            dinner_name = rows[random_num]["name"]
            dinner_total_cal = rows[random_num]["cal_per_rec"]
            dinner_servings = rows[random_num]["servings"]
            dinner_cal_per_serving = dinner_total_cal / dinner_servings
            dinner_recipe = rows[random_num]["rec_text"]
            dinner_ingredients = rows[random_num]["ingredients"]
        elif count == 0:
            return apology("You need to add more recipes", 403)

        #Random Snack3
        category = 'snack'
        db.execute("SELECT * FROM user_recipe WHERE user_id=:id AND category LIKE :cat", {"id": session["user_id"], "cat": ('%' + category + '%') })
        rows = db.fetchall()
        count = 0
        for row in rows:
            count += 1
        if count == 1:
            snack_three_name = rows[0]["name"]
            snack_three_total_cal = rows[0]["cal_per_rec"]
            snack_three_servings = rows[0]["servings"]
            snack_three_cal_per_serving = snack_three_total_cal / snack_three_servings
            snack_three_recipe = rows[0]["rec_text"]
            snack_three_ingredients = rows[0]["ingredients"]
        elif count > 1:
            random_num = random.randrange(0, count, 1)
            snack_three_name = rows[random_num]["name"]
            snack_three_total_cal = rows[random_num]["cal_per_rec"]
            snack_three_servings = rows[random_num]["servings"]
            snack_three_cal_per_serving = snack_three_total_cal / snack_three_servings
            snack_three_recipe = rows[random_num]["rec_text"]
            snack_three_ingredients = rows[random_num]["ingredients"]
        elif count == 0:
            return apology("You need to add more recipes", 403)

        total_cals_per_day = breakfast_cal_per_serving + snack_one_cal_per_serving + lunch_cal_per_serving + snack_two_cal_per_serving + dinner_cal_per_serving + snack_three_cal_per_serving
        return render_template("randommeals.html", snack_one_name=snack_one_name, snack_one_total_cal=snack_one_total_cal, snack_one_cal_per_serving=snack_one_cal_per_serving, snack_one_recipe=snack_one_recipe, snack_one_ingredients=snack_one_ingredients, breakfast_name=breakfast_name, breakfast_total_cal=breakfast_total_cal, breakfast_cal_per_serving=breakfast_cal_per_serving, breakfast_recipe=breakfast_recipe, breakfast_ingredients=breakfast_ingredients, lunch_name=lunch_name, lunch_total_cal=lunch_total_cal, lunch_cal_per_serving=lunch_cal_per_serving, lunch_recipe=lunch_recipe, lunch_ingredients=lunch_ingredients, snack_two_name=snack_two_name, snack_two_total_cal=snack_two_total_cal, snack_two_cal_per_serving=snack_two_cal_per_serving, snack_two_recipe=snack_two_recipe, snack_two_ingredients=snack_two_ingredients, dinner_name=dinner_name, dinner_total_cal=dinner_total_cal, dinner_cal_per_serving=dinner_cal_per_serving, dinner_recipe=dinner_recipe, dinner_ingredients=dinner_ingredients, snack_three_name=snack_three_name, snack_three_total_cal=snack_three_total_cal, snack_three_cal_per_serving=snack_three_cal_per_serving, snack_three_recipe=snack_three_recipe, snack_three_ingredients=snack_three_ingredients, total_cals_per_day=total_cals_per_day)

@app.route("/account", methods=["GET", "POST"])
@login_required
def account():
    if request.method == "GET":
        db.execute("SELECT * FROM users WHERE id=:user", {"user": session["user_id"]})
        rows = db.fetchall()
        email = rows[0]["email"]
        name = rows[0]["name"]
        return render_template("account.html", email=email, name=name)
    else:
        newpassword = generate_password_hash(request.form.get("newpassword"))
        newpassword1 = request.form.get("newpassword")
        newpassword2 = request.form.get("newpassword2")
        if newpassword1 != newpassword2:
            return apology("Passwords do not match", 403)
        elif not newpassword1:
            return apology("Please enter your Password", 403)
        elif not newpassword2:
            return apology("Please repeat your Password", 403)
        else:
            db.execute("UPDATE users SET hash=:password WHERE id=:user", {"password": newpassword, "user": session["user_id"]})
            con.commit()
            return redirect("/login")

