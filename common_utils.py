import gspread
from oauth2client.service_account import ServiceAccountCredentials
import openai
from dotenv import load_dotenv
import os

# 공통 상수
SERVICE_ACCOUNT_FILE = 'google_service_account.json'
SCOPE = ['https://spreadsheets.google.com/feeds', 'https://www.googleapis.com/auth/drive']

load_dotenv()
OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")
client = openai.OpenAI(api_key=OPENAI_API_KEY)

def get_gsheet(sheet_name):
    creds = ServiceAccountCredentials.from_json_keyfile_name(SERVICE_ACCOUNT_FILE, SCOPE)
    client_gs = gspread.authorize(creds)
    sheet = client_gs.open(sheet_name).sheet1
    return sheet 