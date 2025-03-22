from flask import Blueprint
from flask import  render_template, request 
from greenbyte.models import Post



main = Blueprint('main', __name__)


@main.route("/")
def index( ):
    page = request.args.get('page', 1, type=int)
    posts = Post.query.order_by(Post.datePosted.desc()).paginate(page=page, per_page=5)
    return render_template("index.html", posts=posts)


