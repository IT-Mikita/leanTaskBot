# Imports
import db
import config
import userMessages as UM
import userKeyboards as UK
import telebot

# Constants
COMMAND_LIST = ['/start']
DEFAULT_PHOTO_URL = "https://ih1.redbubble.net/image.1015554729.8766/st,small,507x507-pad,600x600,f8f8f8.jpg"
dbManager = db.DatabaseManager(dbFile=config.dbFilename)
bot = telebot.TeleBot(config.botToken, parse_mode='html')

def check_user(message):
    """
    Check if the user exists in the database. If not, add them.
    """
    tgId = message.from_user.id
    tgUsername = message.from_user.username
    tgPhoto = get_userPhoto(tgId=tgId)
    joinedTeam=True  # Placeholder for testing
    teamId = 1  # Placeholder for testing
    
    # Check if user exists in the database
    if not dbManager.dbUsers.userExists(tgId, tgUsername, tgPhoto):
        dbManager.dbUsers.addUser(
            tgId=tgId, 
            tgUsername=tgUsername,
            userPhoto=tgPhoto, 
            joinedTeam=joinedTeam, 
            teamId=teamId, 
            userPos='QA.Engineer', 
            userTasks=[]
        )
        if joinedTeam:
            dbManager.dbTeams.addMemberToTeam(tgId, teamId=teamId)

def get_userPhoto(tgId):
    """
    Fetch user photo from Telegram. Return a default photo URL if not found or there's an error.
    """
    try:
        photos = bot.get_user_profile_photos(tgId, limit=1)
        if photos.total_count > 0:
            photo = photos.photos[0][0]
            file_info = bot.get_file(photo.file_id)
            tgPhoto = f"https://api.telegram.org/file/bot{config.botToken}/{file_info.file_path}"
        else:
            tgPhoto = DEFAULT_PHOTO_URL
    except Exception:
        tgPhoto = DEFAULT_PHOTO_URL
    return tgPhoto

# Command handlers
@bot.message_handler(commands=['start'])
def send_user_welcome(message):
    """
    Send a welcome message to the user when the /start command is used.
    """
    check_user(message)
    bot.send_message(chat_id=message.chat.id, text=UM.welcome)

if __name__ == '__main__':
    bot.infinity_polling(timeout=20)
