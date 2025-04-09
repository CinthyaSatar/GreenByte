from greenbyte import db
from run import app
from greenbyte.models import Post, PostImage

with app.app_context():
    posts = Post.query.all()
    print(f'Total posts: {len(posts)}')
    for post in posts[:3]:
        print(f'Post: {post.title}, Images: {len(post.images)}')
