import sqlite3
import json

class DatabaseManager:
    def __init__(self, dbFile):
        self.database = Database(dbFile)
        self.dbTeams = DbTeams(dbFile)
        self.dbUsers = DbUsers(dbFile)
        self.dbUserTasks = DbUserTasks(dbFile)
        self.dbTeamTasks = DbTeamTasks(dbFile)
        self.dbTopics = DbTopics(dbFile)
class Database:
    def __init__(self, dbFile):
        self.dbFile = dbFile
        self.createDatabase()

    def createDatabase(self):
        with sqlite3.connect(self.dbFile) as connection:
            cursor = connection.cursor()
            cursor.execute("""CREATE TABLE IF NOT EXISTS teams (
                id INTEGER PRIMARY KEY,
                creator TEXT,
                name TEXT,
                topics TEXT,
                members TEXT
            );""")
            cursor.execute("""CREATE TABLE IF NOT EXISTS users (
                id INTEGER PRIMARY KEY,
                tgId INTEGER,
                tgUsername TEXT,
                userPhoto TEXT,
                joinedTeam INTEGER,
                teamId INTEGER,
                userPos TEXT,
                userTasks TEXT
            );""")
            cursor.execute("""CREATE TABLE IF NOT EXISTS user_tasks (
                id INTEGER PRIMARY KEY,
                creator TEXT,
                taskName TEXT,
                taskDesc TEXT,
                taskPhoto TEXT,
                taskStatus TEXT
            );""")
            cursor.execute("""CREATE TABLE IF NOT EXISTS team_tasks (
                id INTEGER PRIMARY KEY,
                teamId INTEGER,
                creator TEXT,
                taskName TEXT,
                taskDesc TEXT,
                taskPhoto TEXT,
                taskStatus TEXT,
                taskTopicId INTEGER
            );""")
            cursor.execute("""CREATE TABLE IF NOT EXISTS topics (
                id INTEGER PRIMARY KEY,
                creator TEXT,
                topicName TEXT,
                topicPhoto TEXT,
                teamId INTEGER
            );""")
class DbTeams:
    def __init__(self, dbFile):
        self.dbFile = dbFile

    def addTeam(self, creator, name, topics=[], members=[]):
        with sqlite3.connect(self.dbFile) as connection:
            cursor = connection.cursor()
            cursor.execute("INSERT INTO teams (creator, name, topics, members) VALUES (?, ?, ?, ?);",
                           (creator, name, json.dumps(topics), json.dumps(members)))
            connection.commit()

    def getAllTeams(self):
        with sqlite3.connect(self.dbFile) as connection:
            cursor = connection.cursor()
            cursor.execute("SELECT * FROM teams")
            results = cursor.fetchall()
            teams = []
            for result in results:
                team = {
                    'id': result[0],
                    'creator': result[1],
                    'name': result[2],
                    'topics': json.loads(result[3]),
                    'members': json.loads(result[4])
                }
                teams.append(team)
            return teams
    def getTeamsByMemberTgId(self, tgId):
        teams_with_member = []
        all_teams = self.getAllTeams()
        for team in all_teams:
            if int(tgId) in team['members']:
                teams_with_member.append(team)
        return teams_with_member
    def addMemberToTeam(self, userId, teamId):
        with sqlite3.connect(self.dbFile) as connection:
            cursor = connection.cursor()
            cursor.execute("SELECT members FROM teams WHERE id = ?", (teamId,))
            members = cursor.fetchone()[0]
            if members:
                members_list = json.loads(members)
            else:
                members_list = []
            if userId not in members_list:
                members_list.append(userId)
                cursor.execute("UPDATE teams SET members = ? WHERE id = ?", (json.dumps(members_list), teamId))
                connection.commit()


class DbUsers:
    def __init__(self, dbFile):
        self.dbFile = dbFile
    def addUser(self, tgId, tgUsername, userPhoto, joinedTeam, teamId, userPos, userTasks=[]):
        with sqlite3.connect(self.dbFile) as connection:
            cursor = connection.cursor()
            cursor.execute("INSERT INTO users (tgId, tgUsername, userPhoto, joinedTeam, teamId, userPos, userTasks) VALUES (?, ?, ?, ?, ?, ?, ?);",
                        (tgId, tgUsername, userPhoto, joinedTeam, teamId, userPos, json.dumps(userTasks)))
            connection.commit()

    def userExists(self, tgId, tgUsername=None, userPhoto=None):
        with sqlite3.connect(self.dbFile) as connection:
            cursor = connection.cursor()
            cursor.execute("SELECT tgUsername, userPhoto FROM users WHERE tgId = ?", (tgId,))
            result = cursor.fetchone()
            # Если пользователя нет
            if result is None:
                return False
            # Проверяем изменения и обновляем при необходимости
            updated_data = {}
            if tgUsername is not None and result[0] != tgUsername:
                updated_data["tgUsername"] = tgUsername
            if userPhoto is not None and result[1] != userPhoto:
                updated_data["userPhoto"] = userPhoto
            if updated_data:
                set_clause = ", ".join(f"{key} = ?" for key in updated_data.keys())
                cursor.execute(f"UPDATE users SET {set_clause} WHERE tgId = ?", (*updated_data.values(), tgId))
                connection.commit()
            return True

    def getUserByTgId(self, tgId):
        query = "SELECT * FROM users WHERE tgId = ?"
        params = (tgId,)
        with sqlite3.connect(self.dbFile) as connection:
            cursor = connection.cursor()
            cursor.execute(query, params)
            result = cursor.fetchone()
            if result:
                # Возвращаем результат в виде словаря
                user = {
                    'id': result[0],
                    'tgId': result[1],
                    'tgUsername': result[2],
                    'userPhoto': result[3],
                    'JoinedTeam': result[4],
                    'TeamId': result[5],
                    'userPos': result[6],
                    'userTasks': json.loads(result[7])
                }
                return user
            else:
                return {'Data':'None'}
    def removeUserTask(self, tgId, taskId):
        """Удаляет задачу из списка задач пользователя по tgId"""
        with sqlite3.connect(self.dbFile) as connection:
            cursor = connection.cursor()
            cursor.execute("SELECT userTasks FROM users WHERE tgId = ?", (tgId,))
            user_data = cursor.fetchone()
            if user_data and user_data[0]:
                user_tasks = json.loads(user_data[0])
                if taskId in user_tasks:
                    user_tasks.remove(taskId)
                    cursor.execute("UPDATE users SET userTasks = ? WHERE tgId = ?", (json.dumps(user_tasks), tgId))
                    connection.commit()
                    return True
                else:
                    return False
            return False

class DbUserTasks:
    def __init__(self, dbFile):
        self.dbFile = dbFile

    def addUserTask(self, creator, taskName, taskDesc, taskPhoto, taskStatus):
        with sqlite3.connect(self.dbFile) as connection:
            cursor = connection.cursor()
            cursor.execute("INSERT INTO user_tasks (creator, taskName, taskDesc, taskPhoto, taskStatus) VALUES (?, ?, ?, ?, ?);",
                           (creator, taskName, taskDesc, taskPhoto, taskStatus))
            connection.commit()
            # Получите ID только что добавленной задачи
            new_task_id = cursor.lastrowid
            # Найдите пользователя с tgId = creator
            cursor.execute("SELECT userTasks FROM users WHERE tgId = ?", (creator,))
            user_data = cursor.fetchone()
            if user_data:
                user_tasks = json.loads(user_data[0]) if user_data[0] else []
                user_tasks.append(new_task_id)
                # Обновите поле userTasks в users с новым списком задач
                cursor.execute("UPDATE users SET userTasks = ? WHERE tgId = ?", (json.dumps(user_tasks), creator))
                connection.commit()
    def updateTaskStatusById(self, taskId, newStatus):
        with sqlite3.connect(self.dbFile) as connection:
            cursor = connection.cursor()
            cursor.execute("UPDATE user_tasks SET taskStatus = ? WHERE id = ?;", (newStatus, taskId))
            connection.commit()
    def getTasksByIds(self, task_ids):
        if not task_ids:
            return []
        ids_placeholders = ','.join(['?'] * len(task_ids))
        query = f"SELECT * FROM user_tasks WHERE id IN ({ids_placeholders})"
        with sqlite3.connect(self.dbFile) as connection:
            cursor = connection.cursor()
            cursor.execute(query, task_ids)
            results = cursor.fetchall()
            tasks = []
            for result in results:
                task = {
                    'id': result[0],
                    'creator': result[1],
                    'taskName': result[2],
                    'taskDesc': result[3],
                    'taskPhoto': result[4],
                    'taskStatus': result[5]
                }
                tasks.append(task)
            return tasks
    def getTaskById(self, taskId):
        with sqlite3.connect(self.dbFile) as connection:
            cursor = connection.cursor()
            cursor.execute("SELECT * FROM user_tasks WHERE id = ?", (taskId,))
            result = cursor.fetchone()
            if result:
                task = {
                    'id': result[0],
                    'creator': result[1],
                    'taskName': result[2],
                    'taskDesc': result[3],
                    'taskPhoto': result[4],
                    'taskStatus': result[5]
                }
                return task
            else:
                return None
    def deleteTaskById(self, taskId):
        with sqlite3.connect(self.dbFile) as connection:
            cursor = connection.cursor()
            cursor.execute("DELETE FROM user_tasks WHERE id = ?", (taskId,))
            connection.commit()

class DbTeamTasks:
    def __init__(self, dbFile):
        self.dbFile = dbFile

    def addTeamTask(self, teamId, creator, taskName, taskDesc, taskPhoto, taskStatus, taskTopicId):
        with sqlite3.connect(self.dbFile) as connection:
            cursor = connection.cursor()
            cursor.execute("INSERT INTO team_tasks (teamId, creator, taskName, taskDesc, taskPhoto, taskStatus, taskTopicId) VALUES (?, ?, ?, ?, ?, ?, ?);",
                           (teamId, creator, taskName, taskDesc, taskPhoto, taskStatus, taskTopicId))
            connection.commit()

class DbTopics:
    def __init__(self, dbFile):
        self.dbFile = dbFile

    def addTopic(self, creator, topicName, topicPhoto, teamId):
        with sqlite3.connect(self.dbFile) as connection:
            cursor = connection.cursor()
            cursor.execute("INSERT INTO topics (creator, topicName, topicPhoto, teamId) VALUES (?, ?, ?, ?);",
                           (creator, topicName, topicPhoto, teamId))
            connection.commit()
