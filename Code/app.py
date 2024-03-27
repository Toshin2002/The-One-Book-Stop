from flask import Flask, redirect , render_template , request, flash
from flask_sqlalchemy import SQLAlchemy
from datetime import date, timedelta
from sqlalchemy.orm import relationship

app=Flask(__name__)
# current_dir = os.path.abspath(os.path.dirname(__file__)) 
app.config['SQLALCHEMY_DATABASE_URI'] = "sqlite:///LMS.db"
app.secret_key = "super secret key"
db = SQLAlchemy(app)

security_code = "123"

class user_book(db.Model):
    __tablename__ = 'user_book'
    ID = db.Column(db.Integer, primary_key=True, autoincrement=True)
    userID = db.Column(db.Integer, db.ForeignKey('User.ID'), nullable=False)
    bookID = db.Column(db.Integer, db.ForeignKey('Book.ID'), nullable=False)

class Request(db.Model):
    __tablename__ = 'Request'
    ID = db.Column(db.Integer, primary_key=True, autoincrement=True)
    userID = db.Column(db.Integer, db.ForeignKey('User.ID'))
    bookID = db.Column(db.Integer, db.ForeignKey('Book.ID'))

class Feedback(db.Model):
    __tablename__ = 'Feedback'
    ID = db.Column(db.Integer, primary_key=True, autoincrement=True)
    userID = db.Column(db.Integer, db.ForeignKey('User.ID'), nullable=False)
    bookID = db.Column(db.Integer, db.ForeignKey('Book.ID'), nullable=False)
    feedback = db.Column(db.Text)

class User(db.Model):
    __tablename__ = 'User'
    ID = db.Column(db.Integer , primary_key=True,auto_increment=True)
    uname = db.Column(db.Text, unique=True, nullable= False)
    password = db.Column(db.Text, nullable= False)
    books = relationship(user_book,cascade="all,delete", backref='issued_books')
    book_requested = relationship(user_book,cascade="all,delete", backref='book_requested')

class Book(db.Model):
    __tablename__ = 'Book'
    ID = db.Column(db.Integer, primary_key=True)
    Name = db.Column(db.Text, nullable=False)
    Author = db.Column(db.Text, nullable=False)
    Content = db.Column(db.Text)
    IssueDate = db.Column(db.Text)
    ReturnDate = db.Column(db.Text)
    Section_ID = db.Column(db.Integer,db.ForeignKey('Section.ID'), nullable=False)
    issueing_users = relationship(user_book,cascade="all,delete", backref='issueing_user')
    user_requesting = relationship(Request,cascade="all,delete", backref='user_requesting')

class Section(db.Model):
    __tablename__ = 'Section'
    ID = db.Column(db.Integer , primary_key=True)
    Name = db.Column(db.Text, nullable=False)
    CreationDate = db.Column(db.Text, nullable=False)
    Description = db.Column(db.Text)
    sectional_books = relationship(Book, cascade="all,delete", backref='books_this_section')



@app.route('/',methods=['GET','POST'])
def home():
    if request.method == 'GET':
        curr_date = str(date.today())
        ret_books = Book.query.filter(Book.ReturnDate == curr_date).all()
        # ret_books = Book.query.filter_by(ReturnDate = curr_date).first()
        # print(ret_books.issueing_users)
        for book in ret_books:
            book.IssueDate = None
            book.ReturnDate = None
            user_books = user_book.query.filter_by(bookID = book.ID).first()
            db.session.delete(user_books) 
            db.session.commit()
        return render_template("home.html")
    else:
        return "Hello"


#############################               USER SIDE              ############################################



@app.route('/login',methods=['GET','POST'])
def login():
    if request.method == 'GET':
        return render_template("login.html",error="")
    
    if request.method == 'POST':
        error=None
        check = request.form
        search=User.query.filter_by(uname=check["uname"]).first()
        if search == None:
            error="Incorrect Username or password"

        else:
            if search.password == check['password']:
                user_books = user_book.query.filter_by(userID = search.ID).all()
                issued_books = []
                for i in user_books:
                    issued_books.append(Book.query.filter_by(ID = i.bookID).first())
                
                user_data = {
                    'user' : search,
                    'issued_books' : issued_books,
                    'msg': ""
                }

                return render_template('user_side/user_page.html',user_data=user_data)
            else:
                error="Incorrect Username or password"
            
        return render_template("login.html",error=error)
    
@app.route("/<userID>/user_page")
def user_page(userID):
    user = User.query.filter_by(ID = userID).first()
    user_books = user_book.query.filter_by(userID = user.ID).all()
    issued_books = []
    for i in user_books:
        issued_books.append(Book.query.filter_by(ID = i.bookID).first())
                
    user_data = {
        'user' : user,
        'issued_books' : issued_books,
        'msg': ""
        }
                
    return render_template('user_side/user_page.html',user_data=user_data)

@app.route("/<userID>/books/<bookID>/request")
def req(userID,bookID):

    check = Request.query.filter_by(userID=userID).filter_by(bookID=bookID).first()
    msg = ""
    if check == None:
        req = Request(userID=userID,bookID=bookID)
        db.session.add(req)
        db.session.commit()
        msg="Request sent! Kindly wait while the librarian approves it."
    else:
        msg="Request already sent! Please be patient"    


    user_books = user_book.query.filter_by(userID = userID).all()
    issued_books = []
    for i in user_books:
        issued_books.append(Book.query.filter_by(ID = i.bookID).first())
                
    user_data = {
        'user' : User.query.filter_by(ID = userID).first(),
        'issued_books' : issued_books,
        'msg': msg
    }

    return render_template('user_side/user_page.html',user_data=user_data)


@app.route('/<userID>/library',methods=['GET','POST'])
def library(userID):
    if request.method == 'GET':
        sections = Section.query.all()
        books = Book.query.filter_by(IssueDate = None).all()

        lib_data = {
            'user' : User.query.filter_by(ID = userID).first(),
            'sections' : sections,
            'books' : books,
            'post' : None
        }       

        return render_template('user_side/library.html',lib_data = lib_data)

        
    if request.method == 'POST':

        check = request.form

        if check["Selection"] == "Name":
            find = Book.query.filter_by(Name = check["Value"]).all()
        else:
            find = Book.query.filter_by(Author = check["Value"]).all()

        sections = Section.query.all()
        books = Book.query.filter_by(IssueDate = None).all()

        lib_data = {
            'user' : User.query.filter_by(ID = userID).first(),
            'sections' : sections,
            'books' : books,
            'post' : find
        } 
        if len(find)==0:
            lib_data['post'] = "No"
        print(lib_data['post'])
        return render_template('user_side/library.html',lib_data = lib_data)

@app.route('/<userID>/sectional/<sectionID>',methods=['GET','POST'])
def sectional_view(userID,sectionID):
    if request.method == 'GET':
        books = Book.query.filter_by(Section_ID = sectionID).filter_by(IssueDate = None).all()
        section = Section.query.filter_by(ID = sectionID).first()
        data ={
            'books' : books,
            'userID' : userID,
            'section' : section.Name
        }
        return render_template('user_side/sectional_user_view.html',data=data)
    
@app.route('/<userID>/<bookID>/return')
def return_book(userID,bookID):
    book = Book.query.filter_by(ID = bookID).first()
    book.IssueDate = None
    book.ReturnDate = None
    user_books = user_book.query.filter_by(bookID = book.ID).first()
    db.session.delete(user_books) 
    db.session.commit()

    user_books = user_book.query.filter_by(userID = userID).all()
    issued_books = []
    for i in user_books:
        issued_books.append(Book.query.filter_by(ID = i.bookID).first())
                
    user_data = {
        'user' : User.query.filter_by(ID = userID).first(),
        'issued_books' : issued_books,
        'msg': ""
    }

    return render_template('user_side/user_page.html',user_data=user_data)


@app.route('/<userID>/feedback',methods=['GET','POST'])
def feedback(userID):
    if request.method == 'POST':
        comment = request.form
        fb = Feedback(userID = userID, bookID = comment['bookID'], feedback = comment['feedback'] )
        db.session.add(fb)
        db.session.commit()

        return redirect("/" + str(userID) + "/user_page")        


#############################           ADMIN SIDE              ############################################



@app.route('/admin', methods=['GET','POST'])
def admin():
    if request.method == 'GET':
        return render_template("admin_login.html")
    
    if request.method == 'POST':
        check = request.form

        if check['code'] == security_code:
            reqs = Request.query.all()
            return render_template("admin.html",requests=reqs)
        
    return "Invalid Code"    



@app.route('/register',methods=['GET','POST'])
def register():
    if request.method == 'GET':
        return render_template("register.html")
    
    if request.method == 'POST':
        error=None
        new_member = request.form
        search = User.query.filter_by(uname=new_member["uname"]).first()
        if search is None:
            member = User(uname=new_member["uname"],password=new_member["pword"])
            db.session.add(member)
            db.session.commit()
            return redirect("/login")
        else :
            error = "User already exists"
            flash(error)
            return render_template("register.html")



#############################            USER HANDLING BY ADMIN              ############################################



@app.route('/users', methods=['GET','POST'])
def user_list():
    if request.method == 'GET':
        users = User.query.all()
        return render_template("users.html",users=users)
 
@app.route("/users/<userID>/delete", methods=['GET','POST'])
def del_user(userID):
    if request.method == 'GET':
        del_user = User.query.filter_by(ID = userID).first()
        db.session.delete(del_user)
        db.session.commit()

        users = User.query.all()
        return render_template("users.html",users=users)

@app.route("/users/<userID>/info",methods=['GET','POST'])
def user_books(userID):
    if request.method == 'GET':
        user = User.query.filter_by(ID = userID).first()
        user_books = user_book.query.filter_by(userID = userID).all()
        reqs = Request.query.filter_by(userID = userID).all()
        feedback = Feedback.query.filter_by(userID = userID).all()
        books = []
        for book in user_books:
            books.append(Book.query.filter_by(ID = book.bookID).first())

        data = {
            'user' : user,
            'books' : books,
            'reqs' : reqs,
            'feedback' : feedback
        
        }

        return render_template("books_by_user.html",data=data)    
    

@app.route("/<userID>/<bookID>/revoke")
def revoke(userID,bookID):
    book = Book.query.filter_by(ID = bookID).first()
    book.IssueDate = None
    book.ReturnDate = None

    user_books = user_book.query.filter_by(userID = userID).filter_by(bookID = bookID).first()
    db.session.delete(user_books)
    db.session.commit()

    return redirect("/users/"+str(userID)+"/info")

##################################          REQUEST HANDLING BY ADMIN           ###############################3                

@app.route("/admin/<userID>/<bookID>/issue")
def issue(userID,bookID):
    book = Book.query.filter_by(ID = bookID).first()
    
    issue_date = str(date.today())
    return_date = str(date.today() + timedelta(weeks=2))
    book.IssueDate = issue_date
    book.ReturnDate = return_date
    db.session.commit()

    issue = user_book(userID = userID, bookID=bookID)
    db.session.add(issue)
    db.session.commit()

    req = Request.query.filter_by(bookID=bookID).filter_by(userID=userID).first()
    db.session.delete(req)
    db.session.commit()

    reqs = Request.query.all()
    return render_template("admin.html",requests=reqs)
    


##################################          SECTION HANDLING BY ADMIN           ###############################3                


@app.route('/sections', methods=['GET','POST'])
def sections():
    if request.method == 'GET':
        sections=Section.query.all()
        return render_template("sections.html",sections=sections)
    
    if request.method == 'POST':
        return render_template("add_section.html")
    
@app.route('/create_section', methods=['GET','POST'])
def create_section():
    if request.method == 'GET':
        return "Not available"

    if request.method == 'POST':
        data = request.form
        check = Section.query.filter_by(ID = data["ID"]).first()
        if check is None:
            curr_date = str(date.today())
            section = Section(ID=data["ID"],Name=data['name'],CreationDate=curr_date,Description=data['description'])
            db.session.add(section)
            db.session.commit()
        else:
            return "A section with this id already exists."
        
        sections = Section.query.all()
        return render_template("sections.html",sections=sections)


@app.route('/section/<section_ID>/delete', methods=['GET','POST'])
def delete_section(section_ID):
    if request.method == 'GET':
        section = Section.query.filter_by(ID = section_ID).first()
        db.session.delete(section)
        db.session.commit()
        sections = Section.query.all()
        return render_template("sections.html",sections=sections)


#################################           Book Handling by Admin          #####################################

    
@app.route("/sections/<section_ID>",methods=['GET','POST'])
def section_info(section_ID):
    if request.method == 'GET':
        books = Book.query.filter_by(Section_ID = section_ID).all()
        info = {
            'books': books,
            'section': Section.query.filter_by(ID = section_ID).first()
        }
        return render_template('books_by_section.html',info=info)
    
    if request.method == 'POST':
        section = Section.query.filter_by(ID=section_ID).first()
        return render_template('add_book.html',section=section)
    

@app.route("/sections/<section_ID>/verify_book",methods=['GET','POST'])
def verify_book(section_ID):
    if request.method == 'POST':
        new_info = request.form
        check = Book.query.filter_by(ID=new_info["ID"]).first()
        if check is None:
            new_book = Book(ID=new_info["ID"],Name=new_info["Name"],Content=new_info["Content"],Author=new_info["Author"], Section_ID = section_ID)
            db.session.add(new_book)
            db.session.commit()
        else:
            return "Book with this ID already exists"
        
        books = Book.query.filter_by(Section_ID = section_ID).all()
        # print(books)
        info = {
            'books': books,
            'section':Section.query.filter_by(ID = section_ID).first()
        }
        return render_template('books_by_section.html',info=info)   
    
@app.route("/sections/<sectionID>/<bookID>/delete",methods=['GET','POST'])
def delete_book(sectionID,bookID):
    if request.method == 'GET':
        del_book = Book.query.filter_by(ID = bookID).first()
        db.session.delete(del_book)
        db.session.commit()
        
        books = Book.query.filter_by(Section_ID = sectionID).all()
        info = {
            'books': books,
            'section':Section.query.filter_by(ID = sectionID).first()
        }
        return render_template('books_by_section.html',info=info)  

#################################           Feedback Handling by Admin          #####################################

@app.route('/feedbacks',methods=['GET','POST'])
def admin_fb():
    if request.method == 'GET':
        feedbacks = Feedback.query.all()
        return render_template("feedbacks.html",feedbacks=feedbacks)
    
@app.route('/<fbID>/remove')
def remove_fb(fbID):
    fb = Feedback.query.filter_by(ID = fbID).first()
    db.session.delete(fb)
    db.session.commit()

    return redirect('/feedbacks')


if __name__ == '__main__':
    app.run(
        debug=True,
        host="0.0.0.0",
        port=8080
    )
