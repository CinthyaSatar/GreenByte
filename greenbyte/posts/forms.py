from flask_wtf import FlaskForm
from flask_wtf.file import FileField, FileAllowed
from wtforms import StringField, SubmitField, TextAreaField, SelectField, IntegerField, BooleanField, HiddenField
from wtforms.validators import DataRequired, Length, Optional
from greenbyte.models import Garden, Tag, Comment
from flask_login import current_user
from greenbyte import db

class CommentForm(FlaskForm):
    content = TextAreaField('Comment', validators=[DataRequired(), Length(min=1, max=1000)])
    parent_id = HiddenField('Parent Comment ID')
    submit = SubmitField('Post Comment')


class PostForm(FlaskForm):
    title = StringField('Title', validators=[DataRequired(), Length(min=3, max=100)])
    content = TextAreaField('Content', validators=[DataRequired(), Length(min=10)])
    category = SelectField('Category', choices=[
        ('Vegetables', 'Vegetables'),
        ('Herbs', 'Herbs'),
        ('Flowers', 'Flowers'),
        ('Fruits', 'Fruits'),
        ('Indoor Plants', 'Indoor Plants'),
        ('Succulents', 'Succulents'),
        ('General', 'General')
    ], validators=[DataRequired()])
    garden_id = SelectField('Link to Garden (Optional)', coerce=int, validators=[Optional()])
    tags = StringField('Tags (comma separated)', validators=[Optional()],
                     description='Add tags to help others find your post (e.g., tomatoes, organic, beginner)')
    images = FileField('Add Photos (Optional)', validators=[
        FileAllowed(['jpg', 'jpeg', 'png'], 'Images only!')
    ])
    submit = SubmitField('Post!')

    def __init__(self, *args, **kwargs):
        super(PostForm, self).__init__(*args, **kwargs)
        # Populate garden choices
        self.garden_id.choices = [(0, 'None')] + [
            (garden.id, garden.name) for garden in Garden.query.filter(
                Garden.members.any(id=current_user.id)
            ).all()
        ]
