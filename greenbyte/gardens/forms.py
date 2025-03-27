from flask_wtf import FlaskForm
from wtforms import StringField, SubmitField, TextAreaField, SelectField
from wtforms.validators import DataRequired, Length, ValidationError
from greenbyte.models import Garden

class GardenForm(FlaskForm):
    name = StringField('Garden Name', 
                      validators=[DataRequired(), 
                                Length(min=2, max=100)])
    location = StringField('Location', 
                         validators=[Length(max=200)])
    submit = SubmitField('Create Garden')

    def validate_name(self, name):
        garden = Garden.query.filter_by(name=name.data).first()
        if garden:
            raise ValidationError('That garden name is already taken. Please choose a different one.')
        


class ZoneForm(FlaskForm):
    name = StringField('Zone Name', 
                       validators=[DataRequired(), 
                                   Length(min=2, max=100)])
    garden = SelectField('Garden', 
                         coerce=int, 
                         validators=[DataRequired()])
    submit = SubmitField('Add Zone')

    def __init__(self, user_gardens, *args, **kwargs):
        super(ZoneForm, self).__init__(*args, **kwargs)
        # Populate the garden dropdown with gardens the user is part of
        self.garden.choices = [(garden.id, garden.name) for garden in user_gardens]

