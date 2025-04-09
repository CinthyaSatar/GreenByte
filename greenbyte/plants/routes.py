from flask import Blueprint
from flask import abort, render_template, flash, redirect, url_for, request 
from greenbyte.models import Post
from greenbyte.posts.forms import PostForm
from greenbyte import db
from flask_login import current_user, login_required



posts = Blueprint('posts', __name__)

@posts.route("/post/<int:postId>" )
def post(postId):
    post = Post.query.get_or_404(postId)
    return render_template("post.html", post=post)

@posts.route("/post/<int:postId>/update", methods=['GET', 'POST'] )
@login_required
def updatePost(postId):
    post = Post.query.get_or_404(postId)
    if post.author != current_user:
        abort(403)
    form=PostForm()
    if form.validate_on_submit():
         post.title = form.title.data
         post.content = form.content.data
         db.session.commit()
         flash("Your post has been updated!", "success")
         return redirect(url_for('posts.post', postId=post.id))
    elif request.method == "GET": 
        form.title.data = post.title
        form.content.data = post.content

    return render_template("add_post.html", form=form, legend="Update Post")



@posts.route("/post/new", methods=['GET', 'POST'])
@login_required
def newPost():
    form = PostForm()
    if form.validate_on_submit():
        post = Post(title=form.title.data, content=form.content.data, author=current_user)
        db.session.add(post)
        db.session.commit()
        flash("Your post has been created!", "success")
        return redirect(url_for('main.index'))
    return render_template("add_post.html", form=form, legend="Create Post")


@posts.route("/post/<int:postId>/delete", methods=['POST'] )
@login_required
def deletePost(postId):
    post = Post.query.get_or_404(postId)
    if post.author != current_user:
        abort(403)
    db.session.delete(post)
    db.session.commit()
    flash("Your post has been deleted!", "success")

    return redirect(url_for('main.index'))


