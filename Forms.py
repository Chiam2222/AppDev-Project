from wtforms import (
    Form,
    StringField,
    PasswordField,
    validators,
    ValidationError,
    SelectField,
)
from wtforms.fields.html5 import EmailField
from flask_login import current_user

from User import User


MINIMUM_PASSWORD_LENGTH = 6

MINIMUM_USERNAME_LENGTH = 4
MAXIMUM_USERNAME_LENGTH = 20
USERNAME_PATTERN = r"^[\w]+$"  # only letters, digits and underscores


def does_username_exist(form, field):
    user = User.get_by_username(field.data)
    if user is not None:
        raise ValidationError("Username already exists.")
    return True  # not necessary to return True but just do it anyways


def username_field(extra_validators=None):
    if extra_validators is None:
        extra_validators = []

    return StringField("Username", [
        validators.Length(min=MINIMUM_USERNAME_LENGTH, max=MAXIMUM_USERNAME_LENGTH),
        validators.Regexp(USERNAME_PATTERN),
        validators.DataRequired(),
        *extra_validators
    ], render_kw={
        "minlength": MINIMUM_USERNAME_LENGTH,
        "maxlength": MAXIMUM_USERNAME_LENGTH,
        "pattern": USERNAME_PATTERN,
        "title": "Username must only contain letters, numbers and underscores"
    })


def password_field(extra_validators=None, label="Password", optional=False, placeholder=""):
    if extra_validators is None:
        extra_validators = []

    return PasswordField(label, [
        validators.Length(min=MINIMUM_PASSWORD_LENGTH),
        (optional and validators.Optional() or validators.DataRequired()),
        *extra_validators
    ], render_kw={"minlength": MINIMUM_PASSWORD_LENGTH, "placeholder": placeholder})


# to do: set field messages/titles

class LoginForm(Form):
    username = username_field()
    password = password_field()


class RegistrationForm(Form):
    username = username_field([does_username_exist])
    email = EmailField("Email", [validators.Email(), validators.DataRequired()])
    password = password_field([
        validators.EqualTo("confirm_password", message="Passwords must match")
    ])
    confirm_password = PasswordField("Confirm Password")


def does_username_exist_except_current():
    def validator(form, field):
        if field.data == current_user.username:
            return False
        return does_username_exist(form, field)
    return validator


class UpdateProfileForm(Form):
    username = username_field([does_username_exist_except_current()])
    email = EmailField("Email", [validators.Email(), validators.DataRequired()])
    new_password = password_field(label="New Password", optional=True, placeholder="Optional")


def search_field(max_characters):
    return StringField("q", [validators.Length(min=1, max=max_characters)], render_kw={"maxlength": str(max_characters)})


class SearchGymForm(Form):
    q = search_field(40)

def cardholder_name_field():
    return StringField("Name (As shown on the card)", [
        validators.Length(min=2, max=26),
        validators.DataRequired()
    ])


def card_details_field():
    return StringField("Card Number", [
        validators.Length(min=16, max=16),
        validators.DataRequired()
    ], render_kw={"placeholder": "0000 0000 0000 0000"})


def expiry_date_field():
    return StringField("Expiry Date", [
        validators.Length(min=4, max=4),
        validators.Regexp(r"^\d+$"),  # numbers only
        validators.DataRequired()
    ], render_kw={"placeholder":"MMDD"})


def cvv_field():
    return StringField("CVV", [
        validators.Length(min=3, max=3),
        validators.Regexp(r"^\d+$"),  # numbers only
        validators.DataRequired()
    ], render_kw={"placeholder":"123"})


class MembershipCheckoutForm(Form):
    tier_choice = SelectField("Tier", choices=[('Silver','Silver',),('Gold','Gold')])
    cardholder_name = cardholder_name_field()
    card_details = card_details_field()
    expiry_date = expiry_date_field()
    cvv = cvv_field()


class MembershipUpdateForm(Form):
    will_renew = SelectField("Do you want to cancel", choices=[('yes','Yes'),('no','No')])


class GymCheckoutForm(Form):
    cardholder_name = cardholder_name_field()
    card_details = card_details_field()
    expiry_date = expiry_date_field()
    cvv = cvv_field()
