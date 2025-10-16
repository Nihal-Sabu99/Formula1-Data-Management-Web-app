from fastapi import FastAPI, Request
from fastapi.responses import HTMLResponse, RedirectResponse
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates
import google.oauth2.id_token
from google.auth.transport import requests
from google.cloud import firestore
import starlette.status as status

app=FastAPI()
firestore_db=firestore.Client()
firebase_request_adapter=requests.Request()
app.mount('/static',StaticFiles(directory='static'),name='static')
templates=Jinja2Templates(directory="templates")

# Creation of user
def getUser(user_token):
    user=firestore_db.collection('users').document(user_token['user_id'])
    if not user.get().exists:
        user_data={
            'driver_list':[],
            'team_list':[]
        }
        firestore_db.collection('users').document(user_token['user_id']).set(user_data)
    return user

# validation of user
def validateFirebaseToken(id_token):
    if not id_token:
        return None
    user_token=None
    try:
        user_token=google.oauth2.id_token.verify_firebase_token(id_token,firebase_request_adapter)
    except ValueError as err:
        print(str(err))
    return user_token

@app.get("/",response_class=HTMLResponse)
async def root(request:Request):
    id_token=request.cookies.get("token")
    error_message="No error here"
    user_token=validateFirebaseToken(id_token)
    
    # teams and drivers are retrived
    drivers=[]
    teams=[]
    if user_token:
        user=getUser(user_token)
        user_data=user.get().to_dict()
        for driver_ref in user_data.get('driver_list',[]):
            driver=driver_ref.get().to_dict()
            drivers.append(driver)
        for team_ref in user_data.get('team_list',[]):
            team=team_ref.get().to_dict()
            teams.append(team)

    # getting teams and drivers
    all_drivers=firestore_db.collection('drivers').stream()
    all_teams=firestore_db.collection('teams').stream()

    driver_list=[{'id':doc.id,**doc.to_dict()} for doc in all_drivers]
    team_list=[{'id':doc.id,**doc.to_dict()} for doc in all_teams]

    return templates.TemplateResponse('main.html',{
        'request':request,
        'user_token':user_token,
        'error_message':error_message,
        'user_info':user.get().to_dict() if user_token else None,
        'drivers':driver_list,
        'teams':team_list
    })

# driver list
@app.get("/drivers/all",response_class=HTMLResponse)
async def get_all_drivers(request: Request):
    drivers=firestore_db.collection('drivers').stream()
    driver_list=[{'id':doc.id,**doc.to_dict()} for doc in drivers]
    return templates.TemplateResponse('drivers.html',{
        'request':request,
        'drivers':driver_list
    })

# Team list
@app.get("/teams/all",response_class=HTMLResponse)
async def get_all_teams(request:Request):
    teams=firestore_db.collection('teams').stream()
    team_list=[{'id':doc.id,**doc.to_dict()} for doc in teams]
    return templates.TemplateResponse('teams.html',{
        'request':request,
        'teams':team_list
    })

# adding driver
@app.get("/add-driver",response_class=HTMLResponse)
async def addDriverForm(request:Request):
    id_token=request.cookies.get("token")
    user_token=validateFirebaseToken(id_token)
    if not user_token:
        return RedirectResponse('/')
    return templates.TemplateResponse('add_driver.html',{
        'request':request,
        'user_token':user_token
    })

# form submission for driver
@app.post("/add-driver",response_class=RedirectResponse)
async def addDriver(request:Request):
    id_token=request.cookies.get("token")
    user_token=validateFirebaseToken(id_token)
    if not user_token:
        return RedirectResponse('/')
    
    form=await request.form()
    driver_name=form['name']

    # same driver name
    existing_driver=firestore_db.collection('drivers').where('name','==',driver_name).get()
    if existing_driver:
        return RedirectResponse('/?error=Driver+with+this+name+already+exists',status_code=status.HTTP_302_FOUND)

    driver_data = {
        'name':driver_name,
        'age':int(form['age']),
        'total_pole_positions':int(form['total_pole_positions']),
        'total_race_wins':int(form['total_race_wins']),
        'total_points_scored':int(form['total_points_scored']),
        'total_world_titles':int(form['total_world_titles']),
        'total_fastest_laps':int(form['total_fastest_laps']),
        'team': form['team']
    }

    driver_ref=firestore_db.collection('drivers').document()
    driver_ref.set(driver_data)

    user=getUser(user_token)
    user_data = user.get().to_dict()
    user_data['driver_list'].append(driver_ref)  # Manually append driver reference
    user.update({'driver_list': user_data['driver_list']})

    return RedirectResponse('/',status_code=status.HTTP_302_FOUND)

# form for adding team
@app.get("/add-team",response_class=HTMLResponse)
async def addTeamForm(request:Request):
    id_token=request.cookies.get("token")
    user_token=validateFirebaseToken(id_token)
    if not user_token:
        return RedirectResponse('/')
    return templates.TemplateResponse('add_team.html',{
        'request':request,
        'user_token':user_token
    })

# team submission
@app.post("/add-team",response_class=RedirectResponse)
async def addTeam(request:Request):
    id_token=request.cookies.get("token")
    user_token=validateFirebaseToken(id_token)
    if not user_token:
        return RedirectResponse('/')
    
    form=await request.form()
    team_name=form['name']

    # Team same name
    existing_team=firestore_db.collection('teams').where('name','==',team_name).get()
    if existing_team:
        return RedirectResponse('/?error=Team+with+this+name+already+exists',status_code=status.HTTP_302_FOUND)

    team_data={
        'name':team_name,
        'year_founded':int(form['year_founded']),
        'total_pole_positions':int(form['total_pole_positions']),
        'total_race_wins':int(form['total_race_wins']),
        'total_constructor_titles':int(form['total_constructor_titles']),
        'previous_season_finish':int(form['previous_season_finish'])
    }

    team_ref=firestore_db.collection('teams').document()
    team_ref.set(team_data)

    user = getUser(user_token)
    user_data = user.get().to_dict()
    user_data['team_list'].append(team_ref)
    user.update({'team_list': user_data['team_list']})

    return RedirectResponse('/',status_code=status.HTTP_302_FOUND)
