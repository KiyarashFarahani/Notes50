from cs50 import SQL
from flask import Flask, redirect, render_template, request, session
import string, random, glob
from flask_session import Session

app = Flask(__name__)

app.config["SESSION_PERMANENT"] = False
app.config["SESSION_TYPE"] = "filesystem"
Session(app)

ids_db = SQL("sqlite:///ids.db")
users_db = SQL("sqlite:///users.db")

url = "https://ide-1d3aad037e28438882427a2dc528f83d-8080.cs50.ws/"

def id_generator(size=6, chars=string.ascii_uppercase + string.digits):
    while (True):
        new_id = ''.join(random.choice(chars) for _ in range(size))
        temp = ids_db.execute("SELECT id from ids WHERE id = ?", new_id)
        if(temp == []):
            break
    return new_id

@app.route("/")
def main():

    if(session.get("username") == None):
        return render_template("welcome.html")
    else:
        return redirect("/application")


@app.route("/login", methods=["POST", "GET"])
def login():

    if(session.get("username") == None):
        return render_template("login.html")
    return redirect("/application")


@app.route("/signup", methods=["POST", "GET"])
def signup():

    if (request.referrer == url+"signup" or request.referrer == url+"signup?"):
        un = request.form.get("username")
        pw = request.form.get("password")
        empty = []
        q = users_db.execute("SELECT username From users WHERE username = ?", (un))
        if (q == empty):
            users_db.execute("INSERT INTO users (username, password) VALUES(?, ?)", un, pw)
            return redirect("/login")

        else:
            return render_template("signup.html", error_message = "True")
    else:
        return render_template("signup.html")


@app.route("/application", methods=["POST", "GET"])
def application():

    try:
        if (request.referrer == url+"application"):
            notesdb = SQL(session["sqlname"])
            old_id = request.form.get("formnoteid2")
            new_id = request.form.get("idinput")
            temp = ids_db.execute("SELECT * from ids WHERE id = ?", old_id)

            if(temp == []):
                data = notesdb.execute("SELECT * FROM notes WHERE id = ?", old_id)
                notesdb.execute("DELETE FROM notes WHERE id = ?", old_id)
                notesdb.execute("INSERT INTO notes (id, title, note) VALUES(?,?,?)", new_id, data[0]["title"], data[0]["note"])
                ids_db.execute("INSERT INTO ids (id) VALUES(?)",new_id)
                notes = notesdb.execute("SELECT * FROM notes;")
                return render_template("index.html", thenotes=reversed(notes), username=session["username"], theme = session["theme"], applied = 1)
            else:
                notes = notesdb.execute("SELECT * FROM notes;")
                return render_template("index.html", thenotes=reversed(notes), username=session["username"], theme = session["theme"], applied = 0)
        else:
            notesdb = SQL(session["sqlname"])
            notes = notesdb.execute("SELECT * FROM notes;")
            return render_template("index.html", thenotes=reversed(notes), username=session["username"], theme = session["theme"])

    except:
        un = request.form.get("username")
        pw = request.form.get("password")
        empty = []
        user = users_db.execute("SELECT username From users WHERE username = ?", (un))
        pas = users_db.execute("SELECT password From users WHERE username = ?", (un))

        if (user != empty and pas != empty):
            if (user[0]['username'] == un and pas[0]['password'] == pw):
                session["username"] = un
                dbname = un + ".db"
                sqlname = "sqlite:///" + dbname
                session["sqlname"] = sqlname
                session["theme"] = "blue"

                try:
                    notesdb = SQL(sqlname)
                except:
                    f= open(dbname,"w+")
                    notesdb = SQL(sqlname)

                try:
                    notes = notesdb.execute("SELECT * FROM notes")
                except:
                    notesdb.execute("CREATE TABLE notes (id TEXT, title TEXT, note TEXT);")
                    notes = notesdb.execute("SELECT * FROM notes;")
                return render_template("index.html", thenotes=reversed(notes), username=un, theme = session["theme"])

            else:
                return render_template("login.html", error_message="True")

        else:
            return render_template("login.html", error_message="True")


@app.route("/save", methods=["POST"])
def save():

    title = request.form.get("title")
    note = request.form.get("note")
    note_id = request.form.get("formnoteid")
    notesdb = SQL(session["sqlname"])
    username = session["username"]
    theme = request.form.get("themestatus")
    if (theme != ""):
        session["theme"] = theme

    if (title == "" and note == ""):
        return redirect("/application")

    else:
        empty = []
        i = notesdb.execute("SELECT id FROM notes WHERE id = ?", (note_id))

        if(i == empty):

            try:
                emptynote = notesdb.execute("SELECT * FROM notes WHERE note = ?", "")
                if (emptynote[0]["title"] == '' and emptynote[0]["note"] == ''):
                    getid = emptynote[0]["id"]
                    notesdb.execute("DELETE FROM notes WHERE id = ?", getid)
                    notesdb.execute("INSERT INTO notes (id, title, note) VALUES(?,?,?)",getid,title,note)
            except:
                newid = id_generator()
                notesdb.execute("INSERT INTO notes (id, title, note) VALUES(?,?,?)",newid,title,note)

        else:
            getid = notesdb.execute("SELECT id FROM notes WHERE id = ?", note_id)
            notesdb.execute("DELETE FROM notes WHERE id = ?", note_id)
            notesdb.execute("INSERT INTO notes (id, title, note) VALUES(?,?,?)",getid[0]["id"], title, note)

        return redirect("/application")


@app.route("/delete", methods=["POST"])
def delete():

    note_id = request.form.get("formnoteid")
    notesdb = SQL(session["sqlname"])
    notesdb.execute("DELETE FROM notes WHERE id = ?", note_id)
    return redirect("/application")


@app.route("/newnote")
def newnote():

    notesdb = SQL(session["sqlname"])
    newid = id_generator()
    notesdb.execute("INSERT INTO notes (id, title, note) VALUES(?,?,?)",newid,"","")
    return redirect("/application")


@app.route("/logout", methods=["POST", "GET"])
def logout():
    session.clear()
    return redirect("/")


@app.route("/<noteid>")
def showsharednote(noteid):

    for filename in glob.glob('*.db'):
        invalid = ["users.db","ids.db"]
        if (filename not in invalid):
            notesdb = SQL("sqlite:///"+filename)
            note = notesdb.execute("SELECT * FROM notes WHERE id = ?", noteid)
            if(note != []):
                return render_template("viewer.html", note = note[0], username = session["username"])
    return render_template("404error.html")


#Bye :)