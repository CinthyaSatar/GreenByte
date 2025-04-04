
from flask_wtf import FlaskForm
from wtforms import (
    StringField,
    SubmitField,
    SelectField,
    IntegerField,
    DateField,
    FieldList,
    SelectMultipleField,
    widgets
)
from wtforms.validators import DataRequired, Length, ValidationError
from greenbyte.models import PlantDetail, User
from datetime import date

class GardenForm(FlaskForm):
    name = StringField('Garden Name',
                      validators=[DataRequired(), Length(min=2, max=100)])
    location = StringField('Location',
                         validators=[Length(max=100)])
    submit = SubmitField('Save Garden')  # Changed from 'Create Garden' to 'Save Garden'

class ZoneForm(FlaskForm):
    name = StringField('Zone Name',
                      validators=[DataRequired(),
                                Length(min=2, max=100)])
    plant_statuses = FieldList(StringField('Status'), min_entries=1)
    submit = SubmitField('Save Zone')

    def __init__(self, *args, **kwargs):
        super(ZoneForm, self).__init__(*args, **kwargs)
        # If no statuses are set (new form), populate with defaults
        if len(self.plant_statuses) <= 1:
            default_statuses = ['Seedling', 'Growing', 'Mature', 'Harvesting']
            # Clear existing entries
            while len(self.plant_statuses):
                self.plant_statuses.pop_entry()
            # Add default statuses
            for status in default_statuses:
                self.plant_statuses.append_entry(status)

    def load_zone_statuses(self, zone):
        """Load existing statuses from zone into the form"""
        # Clear existing entries
        while len(self.plant_statuses):
            self.plant_statuses.pop_entry()

        # Add current zone statuses
        for status in zone.get_plant_statuses():
            self.plant_statuses.append_entry(status)

class PlantForm(FlaskForm):
    plant_detail_id = SelectField('Plant Type',
                                coerce=int,
                                validators=[DataRequired()])
    variety_id = SelectField('Variety',
                           coerce=int,
                           validators=[DataRequired()],
                           validate_choice=False)
    quantity = IntegerField('Quantity',
                          validators=[DataRequired()])
    planting_date = DateField('Planting Date',
                            validators=[DataRequired()],
                            default=date.today)
    submit = SubmitField('Add Plant')

    def __init__(self, *args, **kwargs):
        super(PlantForm, self).__init__(*args, **kwargs)
        # Get all plant details and populate the choices
        plant_details = PlantDetail.query.order_by(PlantDetail.name).all()
        self.plant_detail_id.choices = [(0, 'Select a plant...')] + \
                                     [(plant.id, plant.name) for plant in plant_details]

        # Initialize variety choices with default option and special "new variety" option
        self.variety_id.choices = [(0, 'Select a variety...'), (-1, 'Add new variety...')]

        # If plant_detail_id is provided, populate varieties
        if 'plant_detail_id' in kwargs.get('data', {}):
            plant_detail = PlantDetail.query.get(kwargs['data']['plant_detail_id'])
            if plant_detail:
                self.variety_id.choices = [(0, 'Select a variety...')] + \
                                        [(v.id, v.name) for v in plant_detail.varieties] + \
                                        [(-1, 'Add new variety...')]

    def validate_plant_detail_id(self, field):
        if field.data == 0:
            raise ValidationError('Please select a plant type')

    def validate_variety_id(self, field):
        if field.data == 0:
            raise ValidationError('Please select a variety')

