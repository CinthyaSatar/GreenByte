from flask import render_template, flash, redirect, url_for, request, jsonify
from greenbyte import db
from greenbyte.commercial import commercial
from greenbyte.models import Client, Order, OrderItem, Delivery, Payment
from flask_login import current_user, login_required
import json
from datetime import datetime

@commercial.route("/commercial/dashboard")
@login_required
def dashboard():
    """Commercial Dashboard page."""
    return render_template('commercial/dashboard.html', title='Commercial Dashboard')

@commercial.route("/commercial/clients")
@login_required
def clients():
    """Client Management page."""
    return render_template('commercial/clients_updated.html', title='Client Management')

@commercial.route("/commercial/products")
@login_required
def products():
    """Product Management page."""
    return render_template('commercial/products.html', title='Product Management')

@commercial.route("/commercial/orders")
@login_required
def orders():
    """Order Management page."""
    return render_template('commercial/orders.html', title='Order Management')

@commercial.route("/commercial/deliveries")
@login_required
def deliveries():
    """Delivery Management page."""
    return render_template('commercial/deliveries.html', title='Delivery Management')

@commercial.route("/commercial/invoices")
@login_required
def invoices():
    """Invoice Management page."""
    return render_template('commercial/invoices.html', title='Invoice Management')
