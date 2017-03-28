from flask import Flask, render_template, request, session, redirect, url_for
from models import db, User, Place
from forms import SignupForm, LoginForm, AddressForm

app = Flask(__name__)

app.config['SQLALCHEMY_DATABASE_URI'] = 'postgresql://localhost/learningflask'
db.init_app(app)

app.secret_key = "development-key"

@app.route("/")
def index():
  # return render_template("index.html")
  return redirect( url_for('home') )

@app.route("/about")
def about():
  return render_template("about.html")


@app.route("/signup", methods=['GET', 'POST'])
def signup():


    # send user to home page if they're already logged in
    if 'email' in session:
        return redirect(url_for('home'))

    # get reference to the form object
    form = SignupForm()

    # user entering data
    if request.method == 'POST':
        # check form data is ok, if not reload the page
        if form.validate() is False:
            return render_template("signup.html", form=form)

        # form data is ok
        else:
            # add new user to database
            newuser = User(form.first_name, form.last_name, form.email, form.password)
            db.session.add(newuser)
            db.session.commit()

            # assigns a session to the user
            session['email'] = newuser.email

            return redirect( url_for('home') )

    elif request.method == 'GET':
        return render_template("signup.html", form=form)








@app.route("/home", methods=['GET', 'POST'])
def home():
    # if 'email' not in session:
    #     return redirect( url_for('login') )

    form = AddressForm()

    places = []
    my_coordinates = (37.4221, -122.0844)

    if request.method == 'POST':
        if form.validate() == False:
            return redirect( url_for('login') )

        else: 
            # get the address
            address = form.address.data


            # query for places around it
            p = Place()
            my_coordinates = p.address_to_latlng(address)
            places = p.query(address)
    
            # return those results
            return render_template( "home.html", form=form, my_coordinates=my_coordinates, places=places )
            

    elif request.method == 'GET':
        return render_template("home.html", form=form, my_coordinates=my_coordinates, places=places )



@app.route("/login", methods=['GET', 'POST'])
def login():
    if 'email' in session:
        return render_template('home.html')

    form = LoginForm()

    # so get happens when the details are right?
    if request.method == 'POST':
        if form.validate() is False:
            return render_template("login.html", form=form)

        else:
            # here's where you went wrong before...
            email = form.email.data
            password = form.password.data

            # ok this part is pretty cool but i'm sketchy on it
            user = User.query.filter_by(email=email).first()
            if user is not None and user.check_password(password): 
                # assigns a session to the user
                session['email'] = form.email.data
                return redirect( url_for('home') )

            else:
                return redirect( url_for('login') )

    elif request.method == 'GET':
        return render_template("login.html", form=form)


@app.route('/logout')
def logout():
    session.pop('email', None)
    return redirect( url_for( 'index' ) )


if __name__ == "__main__":
  app.run(debug=True)
