from flask_wtf import FlaskForm
from wtforms import (
    StringField, FloatField, SelectField, BooleanField, 
    DateTimeField, IntegerField, FormField, FieldList
)
from wtforms.validators import DataRequired, Email, Length, Optional, NumberRange
from greenbyte.models import Order

class ClientForm(FlaskForm):
    name = StringField('Client Name', 
                      validators=[DataRequired(), Length(min=2, max=100)])
    email = StringField('Email', 
                       validators=[DataRequired(), Email(), Length(max=120)])
    phone = StringField('Phone Number', 
                       validators=[Optional(), Length(max=20)])
    address = StringField('Address', 
                         validators=[Optional(), Length(max=255)])
    submit = SubmitField('Add Client')

class OrderItemForm(FlaskForm):
    plant_id = SelectField('Plant', coerce=int, validators=[DataRequired()])
    quantity = IntegerField('Quantity', 
                          validators=[DataRequired(), NumberRange(min=1)])
    price_per_unit = FloatField('Price per Unit', 
                               validators=[DataRequired(), NumberRange(min=0)])

class OrderForm(FlaskForm):
    client_id = SelectField('Client', coerce=int, validators=[DataRequired()])
    garden_id = SelectField('Garden', coerce=int, validators=[DataRequired()])
    status = SelectField('Status', 
                        choices=Order.VALID_STATUSES,
                        validators=[DataRequired()])
    recurring = BooleanField('Recurring Order')
    recurring_frequency = SelectField('Frequency',
                                    choices=[('', 'None')] + [(f, f) for f in Order.VALID_FREQUENCIES],
                                    validators=[Optional()])
    order_items = FieldList(FormField(OrderItemForm), min_entries=1)
    submit = SubmitField('Place Order')

    def __init__(self, user_gardens, *args, **kwargs):
        super(OrderForm, self).__init__(*args, **kwargs)
        # Populate garden choices with gardens where user has commercial access
        self.garden_id.choices = [(g.id, g.name) for g in user_gardens]

class DeliveryForm(FlaskForm):
    delivery_date = DateTimeField('Delivery Date', 
                                format='%Y-%m-%d %H:%M',
                                validators=[Optional()])
    status = SelectField('Status',
                        choices=[
                            ('Not Shipped', 'Not Shipped'),
                            ('Processing', 'Processing'),
                            ('In Transit', 'In Transit'),
                            ('Delivered', 'Delivered'),
                            ('Failed', 'Failed')
                        ],
                        validators=[DataRequired()])
    tracking_number = StringField('Tracking Number', 
                                validators=[Optional(), Length(max=50)])
    address = StringField('Delivery Address', 
                         validators=[DataRequired(), Length(max=255)])
    submit = SubmitField('Update Delivery')

class PaymentForm(FlaskForm):
    amount = FloatField('Amount', 
                       validators=[DataRequired(), NumberRange(min=0)])
    payment_method = SelectField('Payment Method',
                               choices=[
                                   ('Credit Card', 'Credit Card'),
                                   ('PayPal', 'PayPal'),
                                   ('Bank Transfer', 'Bank Transfer'),
                                   ('Cash', 'Cash')
                               ],
                               validators=[DataRequired()])
    status = SelectField('Status',
                        choices=[
                            ('Pending', 'Pending'),
                            ('Processing', 'Processing'),
                            ('Completed', 'Completed'),
                            ('Failed', 'Failed'),
                            ('Refunded', 'Refunded')
                        ],
                        validators=[DataRequired()])
    payment_date = DateTimeField('Payment Date', 
                               format='%Y-%m-%d %H:%M',
                               validators=[Optional()])
    submit = SubmitField('Process Payment')