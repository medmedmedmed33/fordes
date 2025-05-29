from app import app
from extensions import db
from models import User, Admin, Coach, Referee, Tournament, Team, Player, Match
from werkzeug.security import generate_password_hash
from datetime import datetime, date
import random
import string

def generate_random_password(length=12):
    characters = string.ascii_letters + string.digits + string.punctuation
    return ''.join(random.choice(characters) for i in range(length))

def seed_users():
    print("Seeding users...")
    # Check if admin already exists to avoid creating duplicates
    if not Admin.query.first():
        admin_user = Admin(
            username='admin',
            email='admin@example.com',
            first_name='Super',
            last_name='Admin',
            role='admin'
        )
        admin_user.set_password('adminpassword') # TODO: Use a stronger password in production
        db.session.add(admin_user)
        print(" - Created Admin user")

    # Create some coaches
    coaches_data = [
        {'first_name': 'Walid', 'last_name': 'Regragui', 'email': 'walid.regragui@example.com'},
        {'first_name': 'Jamal', 'last_name': 'Sellami', 'email': 'jamal.sellami@example.com'},
        {'first_name': 'Faouzi', 'last_name': 'Benzarti', 'email': 'faouzi.benzarti@example.com'},
    ]

    for coach_data in coaches_data:
        if not User.query.filter_by(email=coach_data['email']).first():
            username_base = f"{coach_data['first_name'][0]}{coach_data['last_name']}".lower()
            username = f"{username_base}_{random.choices(string.digits, k=3)[0]}" # Simple unique username
            password = generate_random_password()
            coach_user = Coach(
                username=username,
                email=coach_data['email'],
                first_name=coach_data['first_name'],
                last_name=coach_data['last_name'],
                role='coach'
            )
            coach_user.set_password(password)
            db.session.add(coach_user)
            print(f" - Created Coach: {coach_user.username} with password {password}")

    # Create some referees
    referees_data = [
        {'first_name': 'Redouane', 'last_name': 'Jiyed', 'email': 'redouane.jiyed@example.com', 'nationality': 'Moroccan'},
        {'first_name': 'Samir', 'last_name': 'Guezzaz', 'email': 'samir.guezzaz@example.com', 'nationality': 'Moroccan'},
        {'first_name': 'Noureddine', 'last_name': 'El Jaafari', 'email': 'noureddine.eljaafari@example.com', 'nationality': 'Moroccan'},
        {'first_name': 'Adil', 'last_name': 'Zarrouk', 'email': 'adil.zarrouk@example.com', 'nationality': 'Moroccan'},
        {'first_name': 'Brahim', 'last_name': 'Bouzrou', 'email': 'brahim.bouzrou@example.com', 'nationality': 'Moroccan'},
        {'first_name': 'Jalal', 'last_name': 'Jayed', 'email': 'jalal.jayed@example.com', 'nationality': 'Moroccan'},
    ]

    for referee_data in referees_data:
        if not User.query.filter_by(email=referee_data['email']).first():
             username_base = f"{referee_data['first_name'][0]}{referee_data['last_name']}".lower()
             username = f"{username_base}_{random.choices(string.digits, k=3)[0]}" # Simple unique username
             password = generate_random_password()
             referee_user = Referee(
                 username=username,
                 email=referee_data['email'],
                 first_name=referee_data['first_name'],
                 last_name=referee_data['last_name'],
                 role='referee',
                 nationality=referee_data['nationality']
             )
             referee_user.set_password(password)
             db.session.add(referee_user)
             print(f" - Created Referee: {referee_user.username} with password {password}")

    db.session.commit()
    print("Users seeding complete.")

def seed_tournaments():
    print("Seeding tournaments...")
    if not Tournament.query.first():
        tournament = Tournament(
            name='Botola Pro 1',
            description='Top tier Moroccan football league',
            start_date=date(2024, 9, 1),
            end_date=date(2025, 6, 15),
            max_teams=16,
            status='registration'
        )
        db.session.add(tournament)
        db.session.commit()
        print(" - Created Tournament: Botola Pro 1")
    else:
        tournament = Tournament.query.first()
        print(f"Tournament '{tournament.name}' already exists.")

    print("Tournaments seeding complete.")
    return tournament

def seed_teams(tournament):
    print("Seeding teams...")
    teams_data = [
        {'name': 'Raja Club Athletic', 'city': 'Casablanca', 'founded_year': 1949},
        {'name': 'Wydad Athletic Club', 'city': 'Casablanca', 'founded_year': 1937},
        {'name': 'AS FAR', 'city': 'Rabat', 'founded_year': 1958},
        {'name': 'RS Berkane', 'city': 'Berkane', 'founded_year': 1958},
        {'name': 'FUS Rabat', 'city': 'Rabat', 'founded_year': 1946},
    ]

    coaches = Coach.query.all()
    assigned_coaches = set()

    for team_data in teams_data:
        team = Team.query.filter_by(name=team_data['name'], tournament_id=tournament.id).first()
        if not team:
            team = Team(
                name=team_data['name'],
                city=team_data['city'],
                founded_year=team_data['founded_year'],
                tournament_id=tournament.id
            )
            # Assign a random available coach
            available_coaches = [c for c in coaches if c.id not in assigned_coaches]
            if available_coaches:
                assigned_coach = random.choice(available_coaches)
                team.coach = assigned_coach
                assigned_coaches.add(assigned_coach.id)
                print(f" - Assigned coach {assigned_coach.username} to {team.name}")
            else:
                print(f" - No available coaches to assign to {team.name}")

            db.session.add(team)
            print(f" - Created Team: {team.name}")

    db.session.commit()
    print("Teams seeding complete.")

def seed_players(teams):
    print("Seeding players...")
    players_data = {
        'Raja Club Athletic': [
            {'name': 'Anas Zniti', 'position': 'Goalkeeper', 'jersey': 1},
            {'name': 'Abdeljalil Jbira', 'position': 'Defender', 'jersey': 3},
            {'name': 'Mohsine Moutouali', 'position': 'Midfielder', 'jersey': 10},
            {'name': 'Zakaria Hadraf', 'position': 'Forward', 'jersey': 7},
            {'name': 'Yassine Meriah', 'position': 'Defender', 'jersey': 4},
            {'name': 'Nahiri', 'position': 'Defender', 'jersey': 2},
            {'name': 'Benoun', 'position': 'Defender', 'jersey': 5},
            {'name': 'Ziyad', 'position': 'Midfielder', 'jersey': 8},
            {'name': 'Bouhra', 'position': 'Forward', 'jersey': 9},
            {'name': 'Haddad', 'position': 'Midfielder', 'jersey': 6},
        ],
        'Wydad Athletic Club': [
            {'name': 'Ahmed Reda Tagnaouti', 'position': 'Goalkeeper', 'jersey': 1},
            {'name': 'Yahya Attiat Allah', 'position': 'Defender', 'jersey': 2},
            {'name': 'Ayman El Hassouni', 'position': 'Midfielder', 'jersey': 10},
            {'name': 'Guy Mbenza', 'position': 'Forward', 'jersey': 9},
            {'name': 'Jabrane', 'position': 'Midfielder', 'jersey': 6},
            {'name': 'El Amloud', 'position': 'Defender', 'jersey': 3},
            {'name': 'Said', 'position': 'Defender', 'jersey': 4},
            {'name': 'Bouftini', 'position': 'Midfielder', 'jersey': 8},
            {'name': 'El Hachimi', 'position': 'Forward', 'jersey': 7},
            {'name': 'Benzerga', 'position': 'Defender', 'jersey': 5},
        ],
        'AS FAR': [
            {'name': 'Ayoub El Khaliqi', 'position': 'Goalkeeper', 'jersey': 1},
            {'name': 'Mohamed Bourouis', 'position': 'Defender', 'jersey': 4},
            {'name': 'Hamid Ahadad', 'position': 'Midfielder', 'jersey': 8},
            {'name': 'Reda Hajhouj', 'position': 'Forward', 'jersey': 9},
            {'name': 'Soufiane Rahimi', 'position': 'Forward', 'jersey': 7},
            {'name': 'Hamza Khabba', 'position': 'Forward', 'jersey': 11},
            {'name': 'Yahya Jabrane', 'position': 'Midfielder', 'jersey': 6},
            {'name': 'Badr Benoun', 'position': 'Defender', 'jersey': 3},
            {'name': 'Soufiane Chakla', 'position': 'Defender', 'jersey': 2},
            {'name': 'Yahya Attiat Allah', 'position': 'Defender', 'jersey': 5},
        ],
        'RS Berkane': [
            {'name': 'Hamza Akandouch', 'position': 'Goalkeeper', 'jersey': 1},
            {'name': 'Charki Bahri', 'position': 'Forward', 'jersey': 9},
            {'name': 'Hamza Lahmar', 'position': 'Midfielder', 'jersey': 8},
            {'name': 'Youssef Zghoudi', 'position': 'Defender', 'jersey': 4},
            {'name': 'Ismael Mokadem', 'position': 'Midfielder', 'jersey': 10},
            {'name': 'Hamza Regragui', 'position': 'Defender', 'jersey': 2},
            {'name': 'Yassine Mrabet', 'position': 'Defender', 'jersey': 3},
            {'name': 'Hamza El Moussaoui', 'position': 'Forward', 'jersey': 7},
            {'name': 'Younes Belhanda', 'position': 'Midfielder', 'jersey': 6},
            {'name': 'Hamza Semmoumy', 'position': 'Defender', 'jersey': 5},
        ],
        'FUS Rabat': [
            {'name': 'Mehdi Bellaroussi', 'position': 'Goalkeeper', 'jersey': 1},
            {'name': 'El Mehdi Karnass', 'position': 'Forward', 'jersey': 9},
            {'name': 'Hamza Khabba', 'position': 'Forward', 'jersey': 11},
            {'name': 'Yassine Mrabet', 'position': 'Defender', 'jersey': 4},
            {'name': 'Hamza Lahmar', 'position': 'Midfielder', 'jersey': 8},
            {'name': 'Youssef Zghoudi', 'position': 'Defender', 'jersey': 2},
            {'name': 'Ismael Mokadem', 'position': 'Midfielder', 'jersey': 10},
            {'name': 'Hamza Regragui', 'position': 'Defender', 'jersey': 3},
            {'name': 'Yassine Mrabet', 'position': 'Defender', 'jersey': 5},
            {'name': 'Hamza El Moussaoui', 'position': 'Forward', 'jersey': 7},
        ],
    }

    for team in teams:
        if team.name in players_data:
            for player_data in players_data[team.name]:
                if not Player.query.filter_by(name=player_data['name'], team_id=team.id).first():
                    player = Player(
                        name=player_data['name'],
                        position=player_data['position'],
                        jersey_number=player_data['jersey'],
                        age=random.randint(18, 35),
                        nationality='Moroccan',
                        team_id=team.id
                    )
                    db.session.add(player)
                    print(f" - Added player {player.name} ({player.position}) to {team.name}")
    db.session.commit()
    print("Players seeding complete.")

def seed_matches(tournament, teams):
    print("Seeding matches...")
    # Get all referees
    referees = Referee.query.all()
    if not referees:
        print("No referees available for match assignment")
        return

    # Create matches for the first round
    if len(teams) >= 2 and len(tournament.matches) == 0:
        # Create matches between all teams in the first round
        for i in range(0, len(teams)-1, 2):
            if i+1 < len(teams):
                # Assign a random referee
                referee = random.choice(referees)
                
                match = Match(
                    tournament_id=tournament.id,
                    home_team_id=teams[i].id,
                    away_team_id=teams[i+1].id,
                    match_date=datetime(2024, 9, 15 + i//2, 18, 0, 0),  # Spread matches over different days
                    venue='Stade Mohammed V',
                    round_number=1,
                    referee_id=referee.id,
                    status='scheduled'
                )
                db.session.add(match)
                print(f" - Created match: {teams[i].name} vs {teams[i+1].name} (Referee: {referee.first_name} {referee.last_name})")

    db.session.commit()
    print("Matches seeding complete.")

if __name__ == '__main__':
    with app.app_context():
        # Create database tables if they don't exist
        db.create_all()

        seed_users()
        tournament = seed_tournaments()
        # Only seed teams and players if a tournament was created or found
        if tournament:
            teams = Team.query.filter_by(tournament_id=tournament.id).all()
            # Only seed teams if there are less than max_teams in the tournament
            if len(teams) < tournament.max_teams:
                 seed_teams(tournament)
                 teams = Team.query.filter_by(tournament_id=tournament.id).all() # Refresh teams list

            seed_players(teams)
            seed_matches(tournament, teams)

        print("Database seeding complete.") 