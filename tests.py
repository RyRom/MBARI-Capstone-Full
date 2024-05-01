import requests

URL = "http://127.0.0.1:5000"

def test_get_by_id_dive():
    id = 2
    r = requests.get(f'{URL}/getDive/{id}')
    response = r.json()
    assert(r.status_code == 200)
    assert(response[0]['RovName'] == 'ROV2')
    
def test_get_by_id_expedition():
    id = 1001
    r = requests.get(f'{URL}/getExpedition/{id}')
    response = r.json()
    assert(r.status_code == 200)
    assert(response[0]['ShipName'] == 'Ship2')