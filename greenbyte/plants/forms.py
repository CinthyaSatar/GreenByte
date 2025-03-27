from flask_wtf import FlaskForm
from wtforms import StringField, SubmitField, TextAreaField
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