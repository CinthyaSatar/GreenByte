import os
import secrets
from PIL import Image
from flask import Blueprint, abort, render_template, flash, redirect, url_for, request, current_app, jsonify
from greenbyte.models import Post, PostImage, Tag, Comment
from greenbyte.posts.forms import PostForm, CommentForm
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

@posts.route("/post/<int:postId>", methods=['GET', 'POST'])
def post(postId):
    post = Post.query.get_or_404(postId)
    form = CommentForm()

    # Get all top-level comments (no parent_id)
    comments = Comment.query.filter_by(post_id=postId, parent_id=None).order_by(Comment.date_posted.desc()).all()

    print(f"Request method: {request.method}")
    if request.method == 'POST':
        print(f"Form data: {request.form}")
        print(f"Form validation: {form.validate()}")
        if form.errors:
            print(f"Form errors: {form.errors}")

    if form.validate_on_submit() and current_user.is_authenticated:
        print("Form validated successfully, creating comment")
        comment = Comment(
            content=form.content.data,
            post_id=postId,
            user_id=current_user.id,
            parent_id=form.parent_id.data if form.parent_id.data else None
        )
        db.session.add(comment)
        db.session.commit()
        flash('Your comment has been posted!', 'success')
        return redirect(url_for('posts.post', postId=postId))
    else:
        print("Form validation failed or user not authenticated")

    return render_template("page_post.html", post=post, form=form, comments=comments)

@posts.route("/post/<int:post_id>/like", methods=['POST'])
@login_required
def like_post(post_id):
    post = Post.query.get_or_404(post_id)
    if post.like(current_user):
        db.session.commit()
        return jsonify({'success': True, 'count': post.like_count})
    return jsonify({'success': False, 'message': 'Post already liked'}), 400

@posts.route("/post/<int:post_id>/unlike", methods=['POST'])
@login_required
def unlike_post(post_id):
    post = Post.query.get_or_404(post_id)
    if post.unlike(current_user):
        db.session.commit()
        return jsonify({'success': True, 'count': post.like_count})
    return jsonify({'success': False, 'message': 'Post not liked'}), 400

@posts.route("/post/<int:post_id>/like_status", methods=['GET'])
@login_required
def post_like_status(post_id):
    post = Post.query.get_or_404(post_id)
    return jsonify({
        'is_liked': post.is_liked_by(current_user),
        'count': post.like_count
    })

@posts.route("/comment/<int:comment_id>/reply", methods=['POST'])
@login_required
def reply_comment(comment_id):
    parent_comment = Comment.query.get_or_404(comment_id)
    post_id = parent_comment.post_id
    form = CommentForm()

    if form.validate_on_submit():
        reply = Comment(
            content=form.content.data,
            post_id=post_id,
            user_id=current_user.id,
            parent_id=comment_id
        )
        db.session.add(reply)
        db.session.commit()
        flash('Your reply has been posted!', 'success')

    return redirect(url_for('posts.post', postId=post_id))

@posts.route("/comment/<int:comment_id>/delete", methods=['POST'])
@login_required
def delete_comment(comment_id):
    comment = Comment.query.get_or_404(comment_id)
    post_id = comment.post_id

    if comment.author != current_user:
        abort(403)

    db.session.delete(comment)
    db.session.commit()
    flash('Your comment has been deleted!', 'success')

    return redirect(url_for('posts.post', postId=post_id))



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

    return render_template("edit_post.html", form=form, legend="Update Post", post=post)



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

    return render_template("add_page_post.html", form=form, legend="Create Post")


@posts.route("/post/<int:postId>/delete", methods=['GET', 'POST'] )
@login_required
def deletePost(postId):
    post = Post.query.get_or_404(postId)
    if post.author != current_user:
        abort(403)
    db.session.delete(post)
    db.session.commit()
    flash("Your post has been deleted!", "success")

    return redirect(url_for('main.index'))


@posts.route("/post/image/<int:image_id>/delete", methods=['GET', 'POST'])
@login_required
def delete_image(image_id):
    # Get the image
    image = PostImage.query.get_or_404(image_id)
    post_id = request.args.get('post_id', 0, type=int)

    # Check if the post exists and belongs to the current user
    post = Post.query.get_or_404(post_id)
    if post.author != current_user:
        abort(403)

    # Delete the image file from the filesystem
    try:
        image_path = os.path.join(current_app.root_path, 'static/post_pics', image.image_file)
        if os.path.exists(image_path):
            os.remove(image_path)
    except Exception as e:
        # Log the error but continue (we still want to remove the database record)
        print(f"Error deleting image file: {e}")

    # Delete the image record from the database
    db.session.delete(image)
    db.session.commit()

    flash("Image has been removed from your post!", "success")
    return redirect(url_for('posts.updatePost', postId=post_id))


