# LowCal Recipes

LowCal Recipes is a website to keep track of your own low calorie recipes and create daily meal plans.

<ul>
<li>Home - Save recipes to your home page, and access by selecting which meal type recipe you would like to get</li>
![Index Page](../static/website_imgs/index.png)
<li>Recipes - you can search for recipes in the database, by searching for an ingredient and add them to your home page</li>
![Recipes Page](../static/website_imgs/recipes.png)
<li>Meal Planner - generate daily random meal plan, that shows recipes, calories per meal and calories for the day</li>
![Meal Plan Page](../static/website_imgs/mealplan.png)
<li>Add A Recipe - you can add your own recipe, that will add to your home page and overall database</li>
![Add Recipe Page](../static/website_imgs/add.png)
<li>My Account - you can view your account information and change your password</li>
![My Account Page](../static/website_imgs/myaccount.png)
</ul>


## Built With

* [Python](https://docs.python.org/3/) 
* [JavaScript](https://developer.mozilla.org/en-US/docs/Web/JavaScript) 
* [Flask](https://flask.palletsprojects.com/en/1.1.x/) 


## Authors

(https://github.com/marRozh)

## About the project

Create your account to which you can search and add already existing recipes, add your recipes and create a daily meal plan. 

#### Project architecture
```
|- app.py: Flask application file
|- helpers.py: Helper functions for app.py
|- local.db: Database containing all information on users and recipes
    |-static
      |-index.js: JavaScript for app.py
      |-style.css: CSS file
    |-templates: html files for all the website pages
```

## Credits

Icons made by Freepik, Smashicons, Becris from (www.flaticon.com)
Images made by (https://undraw.co/)