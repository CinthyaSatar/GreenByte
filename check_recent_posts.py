from greenbyte import db
from run import app
from greenbyte.models import Post, PostImage

with app.app_context():
    posts = Post.query.order_by(Post.date_posted.desc()).limit(5).all()
    print(f'5 most recent posts:')
    for post in posts:
        print(f'Post: {post.title}, Images: {len(post.images)}, Date: {post.date_posted}')
