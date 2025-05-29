from extensions import db
from datetime import datetime
from sqlalchemy import func
from werkzeug.security import generate_password_hash, check_password_hash
from flask_login import UserMixin

class User(UserMixin, db.Model):
    __tablename__ = 'user'
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(80), unique=True, nullable=False)
    email = db.Column(db.String(120), unique=True, nullable=False)
    password_hash = db.Column(db.String(128))
    role = db.Column(db.String(50), nullable=False, default='user')
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    first_name = db.Column(db.String(80), nullable=True)
    last_name = db.Column(db.String(80), nullable=True)
    
    # Relations polymorphiques
    __mapper_args__ = {
        'polymorphic_identity': 'user',
        'polymorphic_on': role
    }
    
    def set_password(self, password):
        self.password_hash = generate_password_hash(password)
        
    def check_password(self, password):
        return check_password_hash(self.password_hash, password)

    def __repr__(self):
        return f'<User {self.username}>'

class Admin(User):
    __tablename__ = 'admin'
    __mapper_args__ = {
        'polymorphic_identity': 'admin',
    }
    
    def can_manage_tournaments(self):
        return True
    
    def can_manage_teams(self):
        return True

class Team(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(80), nullable=False)
    city = db.Column(db.String(80))
    founded_year = db.Column(db.Integer)
    tournament_id = db.Column(db.Integer, db.ForeignKey('tournament.id'), nullable=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    
    # Add a foreign key for the coach
    coach_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=True) # Coach can be optional initially
    
    # Relationships
    players = db.relationship('Player', backref='team', lazy=True, cascade='all, delete-orphan')
    home_matches = db.relationship('Match', foreign_keys='Match.home_team_id', backref='home_team', lazy=True)
    away_matches = db.relationship('Match', foreign_keys='Match.away_team_id', backref='away_team', lazy=True)
    
    # Define the relationship to the Coach (User) model
    coach = db.relationship('Coach', foreign_keys=[coach_id], backref=db.backref('team', uselist=False), uselist=False)

    def __repr__(self):
        return f'<Team {self.name}>'
    
    def get_stats(self):
        """Calculate team statistics"""
        stats = TeamStats.query.filter_by(team_id=self.id).first()
        if not stats:
            stats = TeamStats(team_id=self.id)
            db.session.add(stats)
            db.session.commit()
        return stats

    def get_available_players(self):
        """Retourne la liste des joueurs disponibles pour le prochain match"""
        return Player.query.filter_by(team_id=self.id, is_available=True).all()
    
    def select_players_for_match(self, match_id, player_ids):
        """Sélectionne les joueurs pour un match spécifique"""
        # Vérifier que tous les joueurs appartiennent à l'équipe
        players = Player.query.filter(
            Player.id.in_(player_ids),
            Player.team_id == self.id
        ).all()
        
        # Supprimer les sélections précédentes pour ce match et cette équipe
        PlayerMatchPerformance.query.filter(
            PlayerMatchPerformance.match_id == match_id,
            PlayerMatchPerformance.player_id.in_([p.id for p in self.players])
        ).delete(synchronize_session=False)

        # Créer les performances des joueurs pour le match
        for player in players:
            # S'assurer qu'une performance n'existe pas déjà pour ce joueur et ce match
            performance = PlayerMatchPerformance.query.filter_by(
                player_id=player.id,
                match_id=match_id
            ).first()
            
            if not performance:
                performance = PlayerMatchPerformance(
                    player_id=player.id,
                    match_id=match_id,
                    is_selected=True # Marquer comme sélectionné
                )
                db.session.add(performance)
            else:
                # Mettre à jour si déjà existant
                performance.is_selected = True
        
        db.session.commit()
        return players

class Coach(User):
    __tablename__ = 'coach'
    __mapper_args__ = {
        'polymorphic_identity': 'coach',
    }
    
    team_id = db.Column(db.Integer, db.ForeignKey('team.id'))
    
    def can_manage_team(self, team_id):
        return self.team_id == team_id
    
    def can_select_players(self, team_id):
        return self.team_id == team_id

class Referee(User):
    __tablename__ = 'referee'
    __mapper_args__ = {
        'polymorphic_identity': 'referee',
    }
    
    id = db.Column(db.Integer, db.ForeignKey('user.id'), primary_key=True)
    nationality = db.Column(db.String(50))
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

    def __repr__(self):
        return f'<Referee {self.first_name} {self.last_name}>'

class Tournament(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), nullable=False)
    description = db.Column(db.Text)
    start_date = db.Column(db.Date, nullable=False)
    end_date = db.Column(db.Date)
    max_teams = db.Column(db.Integer, default=16)
    status = db.Column(db.String(50), default='registration')
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    
    # Relationships
    teams = db.relationship('Team', backref='tournament', lazy=True, cascade='all, delete-orphan')
    matches = db.relationship('Match', backref='tournament', lazy=True, cascade='all, delete-orphan')

    def get_standings(self):
        """Calculate and return the standings for this tournament."""
        # Fetch TeamStats for all teams in this tournament
        # Order by points (desc), goal difference (desc), goals scored (desc)
        # Ensure TeamStats exists for all teams - create if not
        for team in self.teams:
            if not TeamStats.query.filter_by(team_id=team.id).first():
                db.session.add(TeamStats(team_id=team.id))
        db.session.commit() # Commit new TeamStats before querying

        standings = TeamStats.query.join(Team).filter(Team.tournament_id == self.id)
        standings = standings.order_by(
            TeamStats.points.desc(),
            TeamStats.difference_des_buts.desc(),
            TeamStats.goals_marques.desc()
        ).all()
        return standings

    def __repr__(self):
        return f'<Tournament {self.name}>'

class Player(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(80), nullable=False)
    position = db.Column(db.String(20))  # goalkeeper, defender, midfielder, forward
    jersey_number = db.Column(db.Integer)
    age = db.Column(db.Integer)
    nationality = db.Column(db.String(50))
    team_id = db.Column(db.Integer, db.ForeignKey('team.id'), nullable=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    is_available = db.Column(db.Boolean, default=True)  # Si le joueur est disponible pour jouer
    photo_filename = db.Column(db.String(255), nullable=True) # Add column for photo filename

    def __repr__(self):
        return f'<Player {self.name}>'
    
    def get_stats(self):
        """Calculate player statistics"""
        stats = PlayerStats.query.filter_by(player_id=self.id).first()
        if not stats:
            stats = PlayerStats(player_id=self.id)
            db.session.add(stats)
            db.session.commit()
        return stats

    def toggle_availability(self):
        """Change la disponibilité du joueur"""
        self.is_available = not self.is_available
        db.session.commit()
        return self.is_available

class Match(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    tournament_id = db.Column(db.Integer, db.ForeignKey('tournament.id'), nullable=False)
    home_team_id = db.Column(db.Integer, db.ForeignKey('team.id'), nullable=False)
    away_team_id = db.Column(db.Integer, db.ForeignKey('team.id'), nullable=False)
    match_date = db.Column(db.DateTime, nullable=False)
    venue = db.Column(db.String(100))
    home_score = db.Column(db.Integer, default=0)
    away_score = db.Column(db.Integer, default=0)
    status = db.Column(db.String(50), default='scheduled')
    round_number = db.Column(db.Integer, default=1)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

    # Add foreign key for the referee
    referee_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=True) # Referee assignment is optional

    # Define relationship to the Referee (User) model
    referee = db.relationship('Referee', backref='officiated_matches') # Use a backref for the referee's matches list

    def __repr__(self):
        return f'<Match {self.home_team.name} vs {self.away_team.name} on {self.match_date}>'
    
    @property
    def result_string(self):
        if self.status == 'completed':
            return f"{self.home_score} - {self.away_score}"
        return "vs"

# Rename MatchUpdate to MatchEvent
class MatchEvent(db.Model):
    __tablename__ = 'match_event' # Explicitly define table name for clarity
    id = db.Column(db.Integer, primary_key=True)
    match_id = db.Column(db.Integer, db.ForeignKey('match.id'), nullable=False)
    minute = db.Column(db.Integer)  # Match minute
    event_type = db.Column(db.String(50))  # goal, card, substitution, etc. # Renamed from update_type for clarity
    team_id = db.Column(db.Integer, db.ForeignKey('team.id'), nullable=True)
    player_id = db.Column(db.Integer, db.ForeignKey('player.id'), nullable=True)
    description = db.Column(db.Text) # More detailed description if needed
    timestamp = db.Column(db.DateTime, default=datetime.utcnow)
    
    # Relationships
    match = db.relationship('Match', backref='events') # Update backref to 'events'
    team = db.relationship('Team')
    player = db.relationship('Player')
    
    def to_dict(self):
        return {
            'id': self.id,
            'minute': self.minute,
            'type': self.event_type,
            'team': self.team.name if self.team else None,
            'player': self.player.name if self.player else None,
            'description': self.description,
            'timestamp': self.timestamp.isoformat(),
            'time': self.timestamp.strftime('%H:%M')
        }

class TeamStats(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    team_id = db.Column(db.Integer, db.ForeignKey('team.id'), nullable=False, unique=True)
    matches_played = db.Column(db.Integer, default=0)
    victoires = db.Column(db.Integer, default=0)
    nuls = db.Column(db.Integer, default=0)
    defaites = db.Column(db.Integer, default=0)
    goals_marques = db.Column(db.Integer, default=0)
    buts_encaisses = db.Column(db.Integer, default=0)
    difference_des_buts = db.Column(db.Integer, default=0)
    points = db.Column(db.Integer, default=0)
    carton_jaunes = db.Column(db.Integer, default=0)
    cartons_rouges = db.Column(db.Integer, default=0)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    # Relationship
    team = db.relationship('Team', backref='stats_detail', uselist=False)

    def __repr__(self):
        return f'<TeamStats for Team {self.team_id}>'

class PlayerStats(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    player_id = db.Column(db.Integer, db.ForeignKey('player.id'), nullable=False, unique=True)
    goals = db.Column(db.Integer, default=0)
    assists = db.Column(db.Integer, default=0)
    yellow_cards = db.Column(db.Integer, default=0)
    red_cards = db.Column(db.Integer, default=0)
    matches_played = db.Column(db.Integer, default=0)
    minutes_played = db.Column(db.Integer, default=0)
    shots = db.Column(db.Integer, default=0)
    shots_on_target = db.Column(db.Integer, default=0)
    passes = db.Column(db.Integer, default=0)
    pass_accuracy = db.Column(db.Float, default=0.0)
    tackles = db.Column(db.Integer, default=0)
    interceptions = db.Column(db.Integer, default=0)
    clean_sheets = db.Column(db.Integer, default=0)  # For goalkeepers
    saves = db.Column(db.Integer, default=0)  # For goalkeepers
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    # Relationship
    player = db.relationship('Player', backref='stats_record', uselist=False)
    
    def __repr__(self):
        return f'<PlayerStats for Player {self.player_id}>'

class PlayerMatchPerformance(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    player_id = db.Column(db.Integer, db.ForeignKey('player.id'), nullable=False)
    match_id = db.Column(db.Integer, db.ForeignKey('match.id'), nullable=False)
    goals = db.Column(db.Integer, default=0)
    assists = db.Column(db.Integer, default=0)
    yellow_cards = db.Column(db.Integer, default=0)
    red_cards = db.Column(db.Integer, default=0)
    minutes_played = db.Column(db.Integer, default=0)
    shots = db.Column(db.Integer, default=0)
    shots_on_target = db.Column(db.Integer, default=0)
    passes = db.Column(db.Integer, default=0)
    passes_completed = db.Column(db.Integer, default=0)
    tackles = db.Column(db.Integer, default=0)
    interceptions = db.Column(db.Integer, default=0)
    saves = db.Column(db.Integer, default=0)  # For goalkeepers
    rating = db.Column(db.Float, default=0.0)  # Match rating out of 10
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    is_selected = db.Column(db.Boolean, default=False)  # Si le joueur est sélectionné pour le match
    is_playing = db.Column(db.Boolean, default=False)   # Si le joueur est sur le terrain
    
    # Relationships
    player = db.relationship('Player', backref='match_performances')
    match = db.relationship('Match', backref='player_performances')
    
    def __repr__(self):
        return f'<PlayerMatchPerformance for Player {self.player_id} in Match {self.match_id}>'
