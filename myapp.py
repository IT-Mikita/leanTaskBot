import os
import db
import config
from flask import Flask, request, jsonify, render_template, send_from_directory

# Configuration
app = Flask(__name__)
UPLOAD_FOLDER = 'uploads/'
ALLOWED_EXTENSIONS = {'png', 'jpg', 'jpeg', 'gif'}
app.config['UPLOAD_FOLDER'] = UPLOAD_FOLDER
dbManager = db.DatabaseManager(dbFile=config.dbFilename)

# Utility function to check allowed file extensions for image uploads
def allowed_file(filename):
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS

@app.route('/')
def index():
    """ Render the main index page. """
    return render_template('index.html')

@app.route('/team')
def team():
    """ Render the team page. """
    return render_template('teamIndex.html')

@app.route('/profile')
def profile():
    """ Render the profile page. """
    return render_template('profile.html')

@app.route('/createTask')
def createTask():
    """ Render the task creation page. """
    return render_template('createTask.html')

@app.route('/kanban')
def kanban():
    """ Render the kanban page. """
    return render_template('index.html')

@app.route('/createTask', methods=['POST'])
def createTaskPOST():
    """ Handle the POST request to create a task. """
    tgId = str(request.form.get('tgId'))
    taskTitle = request.form.get('taskTitle')
    taskDescription = request.form.get('taskDescription')
    taskStatus = request.form.get('taskStatus')
    taskImage = request.files.get('taskImage')

    filename = ''
    if taskImage and taskImage.filename != '' and allowed_file(taskImage.filename):
        filename = os.path.join(app.config['UPLOAD_FOLDER'], taskImage.filename)
        taskImage.save(filename)

    dbManager.dbUserTasks.addUserTask(
        creator=tgId,
        taskName=taskTitle,
        taskDesc=taskDescription,
        taskPhoto=filename,
        taskStatus=taskStatus
    )
    return jsonify(success=True)

@app.route('/getUserData', methods=['POST'])
def getUserData():
    """ Fetch user data by their Telegram ID. """
    tgId = str(request.json.get('tgId'))
    userData = dbManager.dbUsers.getUserByTgId(tgId)
    teamData = dbManager.dbTeams.getTeamsByMemberTgId(tgId=tgId)[0]
    tasksData = dbManager.dbUserTasks.getTasksByIds(userData['userTasks'])
    return jsonify(user=userData, team=teamData, tasks=tasksData)

@app.route('/updateTaskStatus', methods=['POST'])
def update_task_status():
    """ Update task status by task ID. """
    data = request.get_json()
    taskId = int(data.get('id'))
    newStatus = data.get('status')
    try:
        dbManager.dbUserTasks.updateTaskStatusById(taskId=taskId, newStatus=newStatus)
        return jsonify(success=True)
    except Exception:
        return jsonify(success=False, message='Task not found.')

@app.route('/getTask')
def get_task():
    """ Render a page for a specific task. """
    task_id = request.args.get('id')
    return render_template('showTask.html', task_id=task_id)

@app.route('/getUserTaskData', methods=['POST'])
def getUserTaskData():
    """ Fetch task data by user's Telegram ID and task ID. """
    tgId = str(request.json.get('tgId'))
    taskId = int(request.json.get('taskId'))
    userData = dbManager.dbUsers.getUserByTgId(tgId)
    taskData = dbManager.dbUserTasks.getTaskById(taskId=taskId)
    return jsonify(user=userData, task=taskData)

@app.route('/uploads/<filename>')
def uploaded_file(filename):
    """ Serve uploaded files. """
    return send_from_directory(app.config['UPLOAD_FOLDER'], filename)

@app.route('/deleteUserTask', methods=['POST'])
def deleteUserTask():
    """ Delete a user task by its ID. """
    tgId = str(request.json.get('tgId'))
    taskId = str(request.json.get('taskId'))
    taskData = dbManager.dbUserTasks.getTaskById(taskId=taskId)

    if taskData['taskPhoto']:
        os.remove(taskData['taskPhoto'])

    try:
        dbManager.dbUserTasks.deleteTaskById(taskId=taskId)
        dbManager.dbUsers.removeUserTask(tgId=tgId, taskId=taskId)
        return jsonify(success=True)
    except Exception:
        return jsonify(success=False, message='Task not found.')

if __name__ == "__main__":
    app.run(port=5000)
