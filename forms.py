from flask_wtf import FlaskForm
from wtforms import StringField, DateField, SubmitField
from wtforms.validators import DataRequired

class TaskForm(FlaskForm):
    title = StringField('Title', validators=[DataRequired()])
    due_date = DateField('Due Date (YYYY-MM-DD)', format='%Y-%m-%d', validators=[DataRequired()])
    submit = SubmitField('Save')

class ListForm(FlaskForm):
    title = StringField('Title', validators=[DataRequired()])
    description = StringField('Decsription', validators=[DataRequired()])
    submit = SubmitField('Save')