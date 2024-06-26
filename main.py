from flask import Flask, session, render_template, url_for, redirect, request, jsonify
from flask_login import LoginManager, UserMixin, login_user, logout_user
from flask_swagger_ui import get_swaggerui_blueprint
from authlib.integrations.flask_client import OAuth
import requests, pyodbc

app = Flask(__name__)
app.secret_key = '!secret'
app.config.from_object('config')
oauth = OAuth(app)
login_manager = LoginManager()
login_manager.init_app(app)

#Google OAuth 2.0
CONF_URL = 'https://accounts.google.com/.well-known/openid-configuration'
oauth = OAuth(app)
oauth.register(
    name='google',
    server_metadata_url=CONF_URL,
    client_kwargs={
        'scope': 'openid profile email '
    }
)

#Pyodbc setup
SERVER = 'localhost'
DATABASE = 'master'
USERNAME = 'sa'
PASSWORD = 'yourStrong(!)Password'
URL = "http://127.0.0.1:5000"
connectionString = f'DRIVER={{ODBC Driver 17 for SQL Server}};SERVER={SERVER};DATABASE={DATABASE};UID={USERNAME};PWD={PASSWORD}'

#Swagger
SWAGGER_URL = '/api/docs'  # URL for exposing Swagger UI (without trailing '/')
API_URL = '/static/swagger.json'  # Our API url (can of course be a local resource)

# Call factory function to create our blueprint
swaggerui_blueprint = get_swaggerui_blueprint(
    SWAGGER_URL,  # Swagger UI static files will be mapped to '{SWAGGER_URL}/dist/'
    API_URL,
    config={  # Swagger UI config overrides
        'app_name': "Test application"
    },
)
app.register_blueprint(swaggerui_blueprint)

@app.route('/')
def home():
    #user = session.get('user')
    #return render_template('home.html', user=user)
    return 'Home'

@app.route('/login')
def login():
    redirect_uri = url_for('auth', _external=True)
    return oauth.google.authorize_redirect(redirect_uri)

@app.route('/auth')
def auth():
    token = oauth.google.authorize_access_token()
    userinfo = token['userinfo']
    session['user'] = userinfo['email']
    data = {"userEmail": str(session['user'])}
    requests.post(f'{URL}/post/newUser',json=data)
    connection = pyodbc.connect(connectionString)
    cursor = connection.cursor()
    cursor.execute("SELECT * FROM Users WHERE userEmail = ?", (str(session['user'])))
    user_data = cursor.fetchone()
    cursor.close()
    connection.close()
    user = User(user_data[0] , user_data[1] ,user_data[2]) 
    login_user(user)
    return redirect('/')

class User(UserMixin):
    def __init__(self, user_id, email, typeOfUser):
        self.id = user_id
        self.email = email
        self.typeOfUser = typeOfUser
        
@app.route('/logout')
def logout():
    logout_user()
    session.pop('user', None)
    return redirect('/')

@app.route('/get-all-expeditions', methods=['GET'])
def get_all_expeditions():
    # filtering sort order and sort field 
    sort_field = request.args.get('sortfield', default='ExpeditionID', type=str)
    sort_order = request.args.get('sortorder', default='asc', type=str).upper()

    valid_sort_fields = ['ExpeditionID', 'ShipName']
    if sort_field not in valid_sort_fields:
        return jsonify({'error': 'Invalid sort field'}), 400

    if sort_order not in ['ASC', 'DESC']:
        return jsonify({'error': 'Invalid sort order'}), 400

    try:
        with pyodbc.connect(connectionString) as conn:
            cursor = conn.cursor()
            query = f"SELECT * FROM Expedition ORDER BY [{sort_field}] {sort_order}"
            cursor.execute(query)
            rows = cursor.fetchall()

            columns = [column[0] for column in cursor.description]
            expeditions = [dict(zip(columns, row)) for row in rows]
            return jsonify(expeditions)
    except pyodbc.Error as e:
        return jsonify({'error': str(e)}), 500
    except Exception as e:
        return jsonify({'error': 'Internal server error'}), 500

 # filtering sort order and sort field 
@app.route('/get-all-dives', methods=['GET'])
def get_all_dives():
    sort_field = request.args.get('sortfield', default='DiveID', type=str)
    sort_order = request.args.get('sortorder', default='asc', type=str).upper()

    valid_sort_fields = ['DiveID', 'DiveStartDtg', 'DiveNumber', 'RovName']
    if sort_field not in valid_sort_fields:
        return jsonify({'error': 'Invalid sort field'}), 400

    if sort_order not in ['ASC', 'DESC']:
        return jsonify({'error': 'Invalid sort order'}), 400

    try:
        with pyodbc.connect(connectionString) as conn:
            cursor = conn.cursor()
            query = f"SELECT * FROM Dive ORDER BY [{sort_field}] {sort_order}"
            cursor.execute(query)
            rows = cursor.fetchall()

            columns = [column[0] for column in cursor.description]
            dives = [dict(zip(columns, row)) for row in rows]
            return jsonify(dives)
    except Exception as e:
        return jsonify({'error': 'Internal server error'}), 500
    
@app.route("/post/newUser", methods=['POST'])
def create_user():
    try:
        data = request.json
        userEmail = data['userEmail']
        connection = pyodbc.connect(connectionString)
        cursor = connection.cursor()
        cursor.execute("SELECT COUNT(*) FROM Users WHERE userEmail = ?", (userEmail))
        row_count = cursor.fetchone()[0]
        if row_count == 1:
            return jsonify({'message': 'User Already Exists '}), 200


        create_query = f"INSERT INTO Users (userEmail, typeOfUser) VALUES (?, ?)"
        cursor.execute(create_query, (userEmail, "user"))
        connection.commit()
        cursor.close()
        connection.close()
        
        return jsonify({'message': 'Created new user successfully'}), 200
    except Exception as e:
        return jsonify({'error': str(e)}), 500
    
@app.route('/getExpedition/<int:id>', methods=['GET'])
def get_by_id_expedition(id):
    try:
        
        connection = pyodbc.connect(connectionString)
        
        cursor = connection.cursor()
        
        select_query = f"SELECT * FROM Expedition WHERE ExpeditionID = ? "
        cursor.execute(select_query, id)
        
        columns = [column[0] for column in cursor.description]
        results = []
        rows = cursor.fetchall()
        cursor.close()
        connection.close()
        if rows:
            for row in rows:
                results.append(dict(zip(columns, row)))   
            return jsonify(results)
        else:
            return jsonify({'error': 'No entry matching this id'})
    except Exception as e:
        return jsonify({'error': str(e)}), 500
    
@app.route('/getDive/<int:id>', methods=['GET'])
def get_by_id_dive(id):
    try:
        
        connection = pyodbc.connect(connectionString)
        
        cursor = connection.cursor()
        
        select_query = f"SELECT * FROM Dive WHERE DiveID = ? "
        cursor.execute(select_query, id)
        
        columns = [column[0] for column in cursor.description]
        results = []
        rows = cursor.fetchall()
        cursor.close()
        connection.close()
        if rows:
            for row in rows:
                results.append(dict(zip(columns, row)))   
            return jsonify(results)
        else:
            return jsonify({'error': 'No entry matching this id'})
        
    except Exception as e:
        return jsonify({'error': str(e)}), 500
    
@app.route("/post/create_expedition", methods=['POST'])
def create_Expedition():
    try:
        data = request.json
        
        ExpeditionID = data['ExpeditionID']
        DeviceID = data['DeviceID']
        ShipName = data['ShipName']
        ShipSeqNum = data['ShipSeqNum']
        Purpose = data['Purpose']
        StatCode = data['StatCode']
        ExpdChiefScientist = data['ExpdChiefScientist']
        ExpdPrincipalInvestigator = data['ExpdPrincipalInvestigator']
        ScheduledStartDtg = data['ScheduledStartDtg']
        ScheduledEndDtg = data['ScheduledEndDtg']
        EquipmentDesc = data['EquipmentDesc']
        Participants = data['Participants']
        RegionDesc = data['RegionDesc']
        PlannedTrackDesc = data['PlannedTrackDesc']
        StartDtg = data['StartDtg']
        EndDtg = data['EndDtg']
        Accomplishments = data['Accomplishments']
        ScientistComments = data['ScientistComments']
        SciObjectivesMet = data['SciObjectivesMet']
        OperatorComments = data['OperatorComments']
        AllEquipmentFunctioned = data['AllEquipmentFunctioned']
        OtherComments = data['OtherComments']
        UpdatedBy = data['UpdatedBy']
        ismodified = data['ismodified']

        connection = pyodbc.connect(connectionString)

        cursor = connection.cursor()

        create_query = f"INSERT INTO Expedition (ExpeditionID, DeviceID, ShipName, ShipSeqNum, Purpose, StatCode, ExpdChiefScientist, ExpdPrincipalInvestigator, ScheduledStartDtg, ScheduledEndDtg, EquipmentDesc, Participants, RegionDesc, PlannedTrackDesc, StartDtg, EndDtg, Accomplishments, ScientistComments, SciObjectivesMet, OperatorComments, AllEquipmentFunctioned, OtherComments, UpdatedBy, ismodified) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?);"
        cursor.execute(create_query, (ExpeditionID, DeviceID, ShipName, ShipSeqNum, Purpose, StatCode, ExpdChiefScientist, ExpdPrincipalInvestigator, ScheduledStartDtg, ScheduledEndDtg, EquipmentDesc, Participants, RegionDesc, PlannedTrackDesc, StartDtg, EndDtg, Accomplishments, ScientistComments, SciObjectivesMet, OperatorComments, AllEquipmentFunctioned, OtherComments, UpdatedBy, ismodified))

        connection.commit()
        cursor.close()
        connection.close()

        return jsonify({'message': 'Created new expedition successfully'}), 200
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route("/post/create_dive", methods=['POST'])
def create_dive():
    try:
        data = request.json

        DiveID = data['DiveID']
        DeviceID = data['DeviceID']
        RovName = data['RovName']
        DiveNumber = data['DiveNumber']
        ExpeditionID_FK = data['ExpeditionID_FK']
        DiveStartDtg = data['DiveStartDtg']
        DiveEndDtg = data['DiveEndDtg']
        DiveChiefScientist = data['DiveChiefScientist']
        BriefAccomplishments = data['BriefAccomplishments']
        DiveStartTimecode = data['DiveStartTimecode']
        DiveEndTimecode = data['DiveEndTimecode']
        DiveLatMid = data['DiveLatMid']
        DiveLonMid = data['DiveLonMid']
        DiveDepthMid = data['DiveDepthMid']

        connection = pyodbc.connect(connectionString)

        cursor = connection.cursor()

        create_query = f"INSERT INTO Dive (DiveID, DeviceID, RovName, DiveNumber, ExpeditionID_FK, DiveStartDtg, DiveEndDtg, DiveChiefScientist, BriefAccomplishments, DiveStartTimecode, DiveEndTimecode, DiveLatMid, DiveLonMid, DiveDepthMid) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)"
        cursor.execute(create_query, (DiveID, DeviceID, RovName, DiveNumber, ExpeditionID_FK, DiveStartDtg, DiveEndDtg, DiveChiefScientist, BriefAccomplishments, DiveStartTimecode, DiveEndTimecode, DiveLatMid, DiveLonMid, DiveDepthMid))

        connection.commit()
        cursor.close()
        connection.close()
        
        return jsonify({'message': 'Created new dive successfully'}), 200
    except Exception as e:
        return jsonify({'error': str(e)}), 500
    
@app.route('/update/Expedition/<int:expedition_id>', methods=['PUT'])
def updateExpedition_data(expedition_id):
    try:
        
        data = request.json
        connection = pyodbc.connect(connectionString)
        cursor = connection.cursor()
        # Check if expedition_id exists in the database
        cursor.execute("SELECT COUNT(*) FROM Expedition WHERE ExpeditionID = ?", (expedition_id))
        row_count = cursor.fetchone()[0]
        if row_count == 0:
            return jsonify({'error': 'Invalid expedition_id '}), 400
        
        
        columns = []
        valueForColumn = []

        #Go Through json body(data) and append column name and the column updated data
        for colName, newValue in data.items():
            # Same as DatetimeGMT = ?
            columns.append(f"{colName} = ?")
            valueForColumn.append(newValue)

        valueForColumn.append(expedition_id)
        columnsToUpdate = ","
        columnsToUpdate = columnsToUpdate.join(columns)

        # Construct the update query dynamically
        update_query = f"UPDATE Expedition SET {columnsToUpdate} WHERE ExpeditionID = ?"

        cursor.execute(update_query, valueForColumn)
        connection.commit()

        cursor.close()
        connection.close()

        return jsonify({'message': ' Expedition Table Data updated successfully'}), 200
    except Exception as e:
        return jsonify({'error': str(e)}), 500
    
@app.route('/update/Dive/<int:dive_id>', methods=['PUT'])
def updateDive_data(dive_id):
    try:
        
        data = request.json
        connection = pyodbc.connect(connectionString)
        cursor = connection.cursor()

        # Check if expedition_id exists in the database
        cursor.execute("SELECT COUNT(*) FROM Dive WHERE DiveID = ?", (dive_id))
        row_count = cursor.fetchone()[0]
        if row_count == 0:
            return jsonify({'error': 'Invalid expedition_id '}), 400
        
        
        columns = []
        valueForColumn = []

        #Go Through json body(data) and append column name and the column updated data
        for colName, newValue in data.items():
            #Same as DatetimeGMT = ?
            columns.append(f"{colName} = ?")
            valueForColumn.append(newValue)

        valueForColumn.append(dive_id)
        columnsToUpdate = ","
        columnsToUpdate = columnsToUpdate.join(columns)

        update_query = f"UPDATE Dive SET {columnsToUpdate} WHERE DiveID = ?"

        cursor.execute(update_query, valueForColumn)
        connection.commit()

        cursor.close()
        connection.close()
        
        return jsonify({'message': 'Dive table Data updated successfully'}), 200
    except Exception as e:
        return jsonify({'error': str(e)}), 500
    
@app.route('/delete/Dive/<int:dive_id>', methods=['DELETE'])
def deleteDive_data(dive_id):
    try:
        connection = pyodbc.connect(connectionString)
        cursor = connection.cursor()
        delete_query = f"DELETE FROM Dive WHERE DiveID = ?"
        cursor.execute(delete_query, (dive_id,))
        connection.commit()
        cursor.close()
        connection.close()
        return jsonify({'message': 'Data deleted successfully'}), 200
    except Exception as e:
        return jsonify({'error': str(e)}), 500

if __name__ == '__main__':
    app.run(debug=True)