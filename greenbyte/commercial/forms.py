from flask_wtf import FlaskForm
from wtforms import StringField, TextAreaField, SubmitField
from wtforms.validators import DataRequired, Length, Email, Optional, URL
from greenbyte.models import Farm

class FarmForm(FlaskForm):
    name = StringField('Farm Name', 
                      validators=[DataRequired(), Length(min=2, max=100)])
    location = StringField('Location', 
                         validators=[Length(max=100)])
    description = TextAreaField('Description',
                              validators=[Optional(), Length(max=1000)])
    
    # Business information
    business_name = StringField('Business Name',
                              validators=[Optional(), Length(max=100)])
    tax_id = StringField('Tax ID',
                       validators=[Optional(), Length(max=50)])
    phone = StringField('Phone',
                      validators=[Optional(), Length(max=20)])
    email = StringField('Email',
                      validators=[Optional(), Email(), Length(max=120)])
    website = StringField('Website',
                        validators=[Optional(), URL(), Length(max=120)])
    
    submit = SubmitField('Save Farm')
