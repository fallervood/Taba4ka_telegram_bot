import httplib2
import apiclient
from oauth2client.service_account import ServiceAccountCredentials
import content
from content import Client

# Файл, полученный в Google Developer Console
CREDENTIALS_FILE = 'creds.json'
# ID Google Sheets документа (можно взять из его URL)
spreadsheet_clients = 'TOKEN_1'
spreadsheet_inventory = 'TOKEN_2'

# Авторизуемся и получаем service — экземпляр доступа к API
credentials = ServiceAccountCredentials.from_json_keyfile_name(
    CREDENTIALS_FILE,
    ['https://www.googleapis.com/auth/spreadsheets',
     'https://www.googleapis.com/auth/drive'])
httpAuth = credentials.authorize(httplib2.Http())
service = apiclient.discovery.build('sheets', 'v4', http=httpAuth)


# Читаем базу
def read_brands():
    values = service.spreadsheets().values().get(
        spreadsheetId=spreadsheet_inventory,
        range='A2:E1000',
        majorDimension='COLUMNS'
    ).execute()
    v = values.get('values')
    brands = []
    for i in range(0, len(v[0])):
        if int(v[4][i]) != 0:
            brands.append(v[0][i])
    return list(set(brands))

# read_brands()


def read_volumes(brand):
    values = service.spreadsheets().values().get(
        spreadsheetId=spreadsheet_inventory,
        range='A2:F1000',
        majorDimension='COLUMNS'
    ).execute()
    v = values.get('values')
    volumes = [[], []]
    sortedV = []
    for i in range(0, len(v[0])):
        if brand == v[0][i] and int(v[4][i]) != 0 and v[1][i].replace(' ', '') not in volumes[0]:
            volumes[0].append(v[1][i].replace(' ', ''))
            volumes[1].append(v[1][i] + " " + v[3][i] + " затяжек " + v[5][i] + " руб")
    # print(volumes)
    return volumes

# read_volumes('HQD')


def read_tastes(brandV):
    values = service.spreadsheets().values().get(
        spreadsheetId=spreadsheet_inventory,
        range='A2:D1000',
        majorDimension='COLUMNS'
    ).execute()
    v = values.get('values')
    tastes = []
    for i in range(0, len(v[0])):
        if str(brandV) == str(v[0][i] + " " + v[1][i].replace(" ", "")):
            tastes.append(v[2][i])
    return tastes

# read_tastes('MAXX')


def read_cost(volume):
    values = service.spreadsheets().values().get(
        spreadsheetId=spreadsheet_inventory,
        range='A2:F1000',
        majorDimension='COLUMNS'
    ).execute()
    v = values.get('values')
    cost = ''
    for i in range(0, len(v[0])):
        if volume in (v[0][i] + " " + v[1][i].replace(' ','')):
            cost = v[5][i]
            break
    return cost

# read_cost('HQD MAXX')


def write_client(user):
    values = service.spreadsheets().values().get(
        spreadsheetId=spreadsheet_clients,
        range='A1:C1000',
        majorDimension='COLUMNS'
    ).execute()
    v = values.get('values')
    try:
        if str(user.client_id) in v[0]:
            if user.name is not None and user.phone is not None:
                index = v[0].index(str(user.client_id))
                try:
                    print('Found id add data..')
                    v[1][index] = user.name
                    v[2][index] = user.phone
                except:
                    print('Found person. Deleting id.. Add data..')
                    v[0].pop(index)
                    v[0].sort()
                    v[0].append(user.client_id)
                    v[1].append(user.name)
                    v[2].append(user.phone)
        else:
            print("Writing id")
            v[0].append(user.client_id)
            v[1].append('-')
            v[2].append('-')
    except Exception as exp:
        print("Error with write client:", exp)

    # Запись
    service.spreadsheets().values().batchUpdate(
        spreadsheetId=spreadsheet_clients,
        body={
            "valueInputOption": "USER_ENTERED",
            "data": [
                {"range": 'A1:C1000',
                 "majorDimension": "COLUMNS",
                 "values": v}
            ]
        }
    ).execute()

# write_client(Client(client_id=1587111554, name='Dmitrii', phone='+79851616171', location=None, time=None))


def read_clients(id):
    values = service.spreadsheets().values().get(
        spreadsheetId=spreadsheet_clients,
        range='A1:C1000',
        majorDimension='COLUMNS'
    ).execute()
    v = values.get('values')
    try:
        a = False
        for i in range(0, len(v[0])):
            if str(id) == v[0][i]:
                a = True
                break
        return a
    except Exception as exp:
        print("Error in read_clients:", exp)

# read_clients(1587111554)


def read_client_info(id):
    values = service.spreadsheets().values().get(
        spreadsheetId=spreadsheet_clients,
        range='A1:C1000',
        majorDimension='COLUMNS'
    ).execute()
    v = values.get('values')
    user = Client(client_id=None, name=None, phone=None, location=None, time=None)
    for i in range(0, len(v[0])):
        if str(id) == v[0][i]:
            if v[1][i] == '-' or v[2][i] == '-':
                user = content.Client(client_id=v[0][i], name=None, phone=None, location=None, time=None)
            else:
                user = content.Client(client_id=v[0][i], name=v[1][i], phone=v[2][i], location=None, time=None)
            break
    return user

# print(type(read_client_info(1587111554).client_id))


def check_product(product):
    values = service.spreadsheets().values().get(
        spreadsheetId=spreadsheet_inventory,
        range='A2:E1000',
        majorDimension='COLUMNS'
    ).execute()
    v = values.get('values')
    count = ''
    for i in range(0, len(v[0])):
        if product.brand == str(v[0][i] + " " + v[1][i].replace(" ", "")) and v[2][i] == str(product.taste):
            count = v[4][i]
    return int(count)


def delete_offer(cart):
    values = service.spreadsheets().values().get(
        spreadsheetId=spreadsheet_inventory,
        range='A2:E1000',
        majorDimension='COLUMNS'
    ).execute()
    v = values.get('values')
    for i in range(0, len(v[0])):
        for j in range(0, len(cart.brand)):
            if cart.brand[j] == str(v[0][i] + " " + v[1][i].replace(" ", "")) and str(cart.taste[j]) == str(v[2][i]):
                v[4][i] = int(v[4][i]) - int(cart.count[j])
    # Запись
    service.spreadsheets().values().batchUpdate(
        spreadsheetId=spreadsheet_inventory,
        body={
            "valueInputOption": "USER_ENTERED",
            "data": [
                {"range": 'A2:E1000',
                 "majorDimension": "COLUMNS",
                 "values": v}
            ]
        }
    ).execute()
