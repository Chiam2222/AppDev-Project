from wtforms import Form, StringField, RadioField, SelectField, TextAreaField, validators, BooleanField
from wtforms.fields.html5 import EmailField

class CreateContactForm(Form):
    location = SelectField('LOCATION*', [validators.DataRequired()], choices=[('', 'Select a Region'), ('Central Singapore', 'Central Singapore'), ('North East', 'North East'), ('North West', 'North West'), ('South East', 'South East'), ('South West', 'South West')], default='')
    first_name = StringField('FIRST NAME*', [validators.Length(min=1, max=150), validators.DataRequired()], render_kw={"placeholder": "First Name"})
    last_name = StringField('LAST NAME*', [validators.Length(min=1, max=150), validators.DataRequired()], render_kw={"placeholder": "Last Name"})
    email = EmailField('EMAIL*', [validators.Length(min=1, max=150), validators.DataRequired()], render_kw={"placeholder": "Email"})
    phone = StringField('PHONE*', [validators.Length(min=8, max=8, message='Invalid Phone No. Length'), validators.Regexp(r"^\d+$", message='Invalid input'), validators.DataRequired()], render_kw={"placeholder": "Phone No."})
    category = SelectField('CATEGORY', [validators.Optional()], choices=[('', 'Select One'), ('Staff / Employee', 'Staff / Employee'), ('Club Maintenance & Equipment', 'Club Maintenance & Equipment'), ('Club Cleanliness', 'Club Cleanliness'), ('Membership Issues', 'Membership Issues'), ('General / Others', 'General / Others')], default='')
    message = TextAreaField('MESSAGE', [validators.Optional()])
