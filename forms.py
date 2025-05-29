from flask_wtf import FlaskForm
from wtforms import StringField, TextAreaField, DateField, IntegerField, SelectField, SubmitField, PasswordField
from wtforms.validators import DataRequired, Length, NumberRange, Optional, Email, EqualTo, ValidationError
from wtforms.widgets import TextArea
from models import Tournament, Team, Coach, User
from wtforms_sqlalchemy.fields import QuerySelectField
from flask_wtf.file import FileField, FileAllowed, FileRequired

class TournamentForm(FlaskForm):
    name = StringField('Tournament Name', validators=[DataRequired(), Length(min=3, max=100)])
    description = TextAreaField('Description', widget=TextArea())
    start_date = DateField('Start Date', validators=[DataRequired()])
    end_date = DateField('End Date', validators=[Optional()])
    max_teams = IntegerField('Maximum Teams', validators=[DataRequired(), NumberRange(min=4, max=32)], default=16)
    submit = SubmitField('Create Tournament')

class TeamForm(FlaskForm):
    name = StringField('Team Name', validators=[DataRequired(), Length(min=2, max=80)])
    city = StringField('City', validators=[Optional(), Length(max=80)])
    founded_year = IntegerField('Founded Year', validators=[Optional(), NumberRange(min=1800, max=2025)])
    coach = QuerySelectField('Coach', query_factory=lambda: Coach.query.all(), get_label='username', allow_blank=True, blank_text='-- Select a Coach --', validators=[Optional()])
    submit = SubmitField('Register Team')

class PlayerForm(FlaskForm):
    name = StringField('Player Name', validators=[DataRequired(), Length(min=2, max=80)])
    position = SelectField('Position', choices=[
        ('goalkeeper', 'Goalkeeper'),
        ('defender', 'Defender'),
        ('midfielder', 'Midfielder'),
        ('forward', 'Forward')
    ], validators=[DataRequired()])
    jersey_number = IntegerField('Jersey Number', validators=[DataRequired(), NumberRange(min=1, max=99)])
    age = IntegerField('Age', validators=[Optional(), NumberRange(min=16, max=45)])
    nationality = StringField('Nationality', validators=[Optional(), Length(max=50)])
    photo = FileField('Player Photo', validators=[FileAllowed(['jpg', 'png'], 'Images only!')])
    submit = SubmitField('Add Player')

class MatchForm(FlaskForm):
    match_date = DateField('Match Date', validators=[DataRequired()])
    venue = StringField('Venue', validators=[Optional(), Length(max=100)])
    round_number = IntegerField('Round Number', validators=[DataRequired(), NumberRange(min=1)], default=1)
    submit = SubmitField('Schedule Match')

class ScoreForm(FlaskForm):
    home_score = IntegerField('Home Team Score', validators=[DataRequired(), NumberRange(min=0, max=20)])
    away_score = IntegerField('Away Team Score', validators=[DataRequired(), NumberRange(min=0, max=20)])
    submit = SubmitField('Update Score')

# Renamed and modified form for Admin to manage users
class UserForm(FlaskForm):
    first_name = StringField('Prénom', validators=[DataRequired(), Length(max=80)])
    last_name = StringField('Nom de famille', validators=[DataRequired(), Length(max=80)])
    username = StringField('Nom d\'utilisateur', validators=[Optional(), Length(min=4, max=80)])
    email = StringField('Adresse email', validators=[DataRequired(), Email(), Length(max=120)])
    role = SelectField('Rôle', choices=[('coach', 'Entraîneur'), ('referee', 'Arbitre'), ('admin', 'Admin')], validators=[DataRequired()])
    password = PasswordField('Nouveau mot de passe', validators=[Optional(), Length(min=6)])
    confirm_password = PasswordField('Confirmer le nouveau mot de passe', validators=[Optional(), EqualTo('password', message='Les mots de passe doivent correspondre.')])
    submit = SubmitField('Enregistrer l\'utilisateur')

class AssignRefereeForm(FlaskForm):
    referee = QuerySelectField('Referee', query_factory=lambda: User.query.filter_by(role='referee').all(), get_label='username', allow_blank=True, blank_text='-- Select a Referee --', validators=[Optional()])
    submit = SubmitField('Assign Referee')
