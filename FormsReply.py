from wtforms import Form, TextAreaField, validators

class CreateReplyField(Form):
    reply = TextAreaField('', [validators.Optional()])
