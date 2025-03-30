from flask import Blueprint, render_template, request
from greenbyte.models import Post

main = Blueprint('main', __name__)

@main.route("/")
def index():
    page = request.args.get('page', 1, type=int)
    posts = Post.query.order_by(Post.date_posted.desc()).paginate(page=page, per_page=5)
    
    for post in posts.items:
        # Format the read time
        post.formatted_date = post.date_posted.strftime('%B %d, %Y')
        post.formatted_read = f"{post.read_time} min read"
        
        # Get garden details
        if post.start_date:
            post.start_date_formatted = post.start_date.strftime('%B %Y')
            
    return render_template('index.html', 
                         posts=posts,
                         max=max,
                         min=min)  # Also add min since we're using both


@main.route("/calendar")
def calendar():
    return render_template('calendar.html', title='Calendar')

