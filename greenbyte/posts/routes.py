import os
import secrets
from PIL import Image
from flask import Blueprint, abort, render_template, flash, redirect, url_for, request, current_app
from greenbyte.models import Post, PostImage, Tag
from greenbyte.posts.forms import PostForm
from greenbyte import db
from flask_login import current_user, login_required


def save_picture(form_picture):
    """Save uploaded picture with a random name"""
    # Generate random filename to avoid collisions
    random_hex = secrets.token_hex(8)
    _, f_ext = os.path.splitext(form_picture.filename)
    picture_fn = random_hex + f_ext
    picture_path = os.path.join(current_app.root_path, 'static/post_pics', picture_fn)

    # Create directory if it doesn't exist
    os.makedirs(os.path.dirname(picture_path), exist_ok=True)

    # Resize image to save space and improve load times
    output_size = (1200, 1200)  # Max dimensions while preserving aspect ratio
    i = Image.open(form_picture)

    # Preserve aspect ratio
    i.thumbnail(output_size)

    # Save the picture
    i.save(picture_path)

    return picture_fn


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
    form = PostForm()
    if form.validate_on_submit():
        # Update post with form data
        post.title = form.title.data
        post.content = form.content.data
        post.category = form.category.data
        post.read_time = max(1, len(form.content.data.split()) // 200)  # Update read time

        # Update garden relationship if selected
        if form.garden_id.data and form.garden_id.data > 0:
            post.garden_id = form.garden_id.data
        else:
            post.garden_id = None

        # Handle tags if provided
        if form.tags.data:
            # Clear existing tags
            post.tags = []

            # Split tags by comma and strip whitespace
            tag_names = [tag.strip().lower() for tag in form.tags.data.split(',') if tag.strip()]

            # Process each tag
            for tag_name in tag_names:
                # Check if tag already exists
                tag = Tag.query.filter_by(name=tag_name).first()
                if not tag:
                    # Create new tag if it doesn't exist
                    tag = Tag(name=tag_name)
                    db.session.add(tag)
                    db.session.flush()

                # Add tag to post's tags
                post.tags.append(tag)
        else:
            # Clear all tags if the field is empty
            post.tags = []

        # Handle image upload if provided
        if form.images.data:
            # Save the image
            image_file = save_picture(form.images.data)

            # Create PostImage record
            post_image = PostImage(
                post_id=post.id,
                image_file=image_file,
                caption=f"Image for {post.title}",
                order=len(post.images)  # Add as the next image in order
            )
            db.session.add(post_image)

        # Commit all changes
        db.session.commit()
        flash("Your post has been updated!", "success")
        return redirect(url_for('posts.post', postId=post.id))
    elif request.method == "GET":
        form.title.data = post.title
        form.content.data = post.content
        form.category.data = post.category if hasattr(post, 'category') else 'General'
        form.garden_id.data = post.garden_id if post.garden_id else 0

        # Populate tags field
        if post.tags:
            form.tags.data = ', '.join([tag.name for tag in post.tags])

    return render_template("add_post.html", form=form, legend="Update Post")



@posts.route("/post/new", methods=['GET', 'POST'])
@login_required
def newPost():
    form = PostForm()
    if form.validate_on_submit():
        # Create the post with form data
        post = Post(
            title=form.title.data,
            content=form.content.data,
            category=form.category.data,
            author=current_user,
            read_time=max(1, len(form.content.data.split()) // 200)  # Estimate read time (1 min per 200 words)
        )

        # Add garden relationship if selected
        if form.garden_id.data and form.garden_id.data > 0:
            post.garden_id = form.garden_id.data

        # Save post to get an ID
        db.session.add(post)
        db.session.flush()

        # Handle tags if provided
        if form.tags.data:
            # Split tags by comma and strip whitespace
            tag_names = [tag.strip().lower() for tag in form.tags.data.split(',') if tag.strip()]

            # Process each tag
            for tag_name in tag_names:
                # Check if tag already exists
                tag = Tag.query.filter_by(name=tag_name).first()
                if not tag:
                    # Create new tag if it doesn't exist
                    tag = Tag(name=tag_name)
                    db.session.add(tag)
                    db.session.flush()

                # Add tag to post's tags
                post.tags.append(tag)

        # Handle image upload if provided
        if form.images.data:
            # Save the image
            image_file = save_picture(form.images.data)

            # Create PostImage record
            post_image = PostImage(
                post_id=post.id,
                image_file=image_file,
                caption=f"Image for {post.title}",
                order=0
            )
            db.session.add(post_image)

        # Commit all changes
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


