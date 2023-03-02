from app import app, db, login_manager
from app.database import User, Pet, Task
from flask import render_template, request, redirect, url_for
from flask_login import login_user, logout_user, current_user, login_required
from sqlalchemy import desc
from werkzeug.security import generate_password_hash, check_password_hash
from datetime import datetime, timedelta
import pytz
import json
import os


@login_manager.user_loader
def load_user(user_id):
    return User.query.get(int(user_id))


# ユーザー登録ページ
@app.route('/signup', methods=['GET', 'POST'])
def sign_up():
    if request.method == 'POST':
        user_data = User(
            username=request.form['username'],
            email=request.form['email'],
            password=generate_password_hash(
                request.form['password'], method='sha256'),
        )

        # フォームが空
        if user_data.username.strip() == '' or user_data.email.strip() == '' or user_data.password.strip() == '':
            return render_template(
                'signup.html',
                page_style='css/form.css',
                page_title='Sign Up',
                error_message='Please fill in all the fields.'
            )

        # ユーザーが既に存在する
        elif User.query.filter_by(email=user_data.email).first():
            return render_template(
                'signup.html',
                page_style='css/form.css',
                page_title='Sign Up',
                error_message='This email is already registered.'
            )

        # ユーザー登録成功
        else:
            db.session.add(user_data)
            db.session.commit()
            return redirect(url_for('make_pet'))

    else:
        return render_template(
            'signup.html',
            page_style='css/form.css',
            page_title='Sign Up',
        )


# ログインページ
@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        email = request.form['email']
        password = request.form['password']
        user = User.query.filter_by(email=email).first()

        # ユーザーが存在しない
        if user is None:
            return render_template(
                'login.html',
                page_style='css/form.css',
                page_title='Login',
                error_message='This email is not registered.'
            )

        # パスワードが正しくない
        elif check_password_hash(user.password, password) == False:
            return render_template(
                'login.html',
                page_style='css/form.css',
                page_title='Login',
                error_message='Password is incorrect.'
            )

        # ログイン成功
        elif check_password_hash(user.password, password):
            login_user(user, remember=True)
            return redirect(url_for('main'))

        # その他のエラー
        else:
            return render_template(
                'login.html',
                page_style='css/form.css',
                page_title='Login',
                error_message='Please check your login details and try again.'
            )

    else:
        return render_template(
            'login.html',
            page_style='css/form.css',
            page_title='Login'
        )


# ログアウト
@app.route('/logout')
@login_required
def logout():
    logout_user()
    return redirect(url_for('login'))


# メインページ
@app.route('/', methods=['GET', 'POST'])
@login_required
def main():
    user = User.query.filter_by(id=current_user.id).first()
    pet = Pet.query.filter_by(
        user_id=current_user.id).order_by(desc(Pet.id)).first()
    tasks = Task.query.filter_by(user_id=current_user.id).all()

    # ペットが存在しない場合はペット作成ページにリダイレクト
    if pet is None:
        return redirect(url_for('make_pet'))

    else:
        # 最後のタスク完了が1日以上前の場合はタスクストリークをリセット
        if user.last_task_date is not None and datetime.now(user.last_task_date.tzinfo) > user.last_task_date + timedelta(days=1):
            user.task_strike = 0

        # タスクの期限が過ぎている場合はhpを減らす
        for task in tasks:
            if task.limit is not None and datetime.now(task.limit.tzinfo) > task.limit + timedelta(seconds=1) and task.status is None:
                pet.hp -= 50
                task.status = 'failed'

        # ペットのhpが0以下の場合は死亡状態にする
        if pet.hp <= 0:
            pet.hp = 0
            pet.status = 'dead'

        db.session.commit()

        # ペット画像のパスを取得
        pet_list = json.load(open('app/static/pet_list.json', 'r'))
        pet_image_path = ''
        for pet_data in pet_list:
            if pet_data['type'] == pet.type:
                pet_image_path = os.path.join('img/pets/', pet_data['image'])
                break

        return render_template(
            'main.html',
            page_style='css/main.css',
            user=user, pet=pet, tasks=tasks, pet_image_path=pet_image_path
        )


# ペット作成ページ
@app.route('/make-pet', methods=['GET', 'POST'])
@login_required
def make_pet():
    current_user_pet = Pet.query.filter_by(
        user_id=current_user.id).order_by(desc(Pet.id)).first()

    # ペットが既に存在する場合はメインページにリダイレクト
    if current_user_pet:
        if current_user_pet.status == 'alive':
            return redirect(url_for('main'))

    pet_list = json.load(open('app/static/pet_list.json', 'r'))

    if request.method == 'POST':
        pet_type = request.form['pet_type']
        pet_name = request.form['pet_name']

        # フォームが空
        if pet_name.strip() == '':
            return render_template(
                'makePet.html',
                page_style='css/form.css',
                page_title='Make Pet',
                pets=pet_list,
                error_message='Please fill in all the fields.'
            )

        # ペット作成成功
        else:
            pet_data = Pet(
                user_id=current_user.id,
                type=pet_type,
                name=pet_name,
            )
            db.session.add(pet_data)
            db.session.commit()
            return redirect(url_for('main'))

    else:
        return render_template(
            'makePet.html',
            page_style='css/form.css',
            page_title='Make Pet',
            pets=pet_list
        )


# タスク作成ページ
@app.route('/new-task', methods=['GET', 'POST'])
@login_required
def new_task():
    if request.method == 'POST':
        name = request.form['name']
        limit = request.form['limit']
        if limit:
            limit = datetime.strptime(limit, '%Y-%m-%dT%H:%M')
        else:
            limit = None

        # フォームが空
        if name.strip() == '' or limit == None:
            return render_template(
                'newTask.html',
                page_style='css/form.css',
                page_title='New Task',
                error_message='Please fill in all the fields.'
            )

        # 期限が現在時刻より前
        elif limit < datetime.now(limit.tzinfo):
            return render_template(
                'newTask.html',
                page_style='css/form.css',
                page_title='New Task',
                error_message='Limit date must be after now.'
            )

        # タスク作成成功
        else:
            task_data = Task(
                user_id=current_user.id,
                name=name,
                limit=limit
            )
            db.session.add(task_data)
            db.session.commit()
            return redirect(url_for('main'))

    else:
        return render_template(
            'newTask.html',
            page_style='css/form.css',
            page_title='New Task',
        )


# タスク完了
@app.route('/change-task-status/<int:task_id>', methods=['GET', 'POST'])
@login_required
def change_task_status(task_id):
    user = User.query.filter_by(id=current_user.id).first()
    task = Task.query.filter_by(id=task_id).first()
    pet = Pet.query.filter_by(
        user_id=current_user.id).order_by(desc(Pet.id)).first()

    # 通常タスク
    if task.status == None:
        task.status = 'done'
        pet.xp += 20
        # タスクストリーク
        if user.last_task_date == None or user.last_task_date <= datetime.now(user.last_task_date.tzinfo) - timedelta(days=1):
            user.task_streak += 1
            pet.hp = 100
            user.last_task_date = datetime.now(pytz.timezone('Asia/Tokyo'))

    # 期限切れタスク
    elif task.status == 'failed':
        task.status = 'done'
        pet.xp += 20

    # もとに戻す
    else:
        task.status = None
        pet.xp -= 20
        if pet.xp < 0:
            pet.xp = 0

        # レベルダウン
        if pet.xp < pet.next_xp - 100 - (pet.level - 2) * 20 and pet.level > 1:
            pet.level -= 1
            pet.next_xp -= 100 + (pet.level) * 20

    # レベルアップ
    if pet.xp >= pet.next_xp and pet.status != 'dead':
        pet.level += 1
        pet.next_xp += 100 + (pet.level - 1) * 20

    db.session.commit()
    return redirect(url_for('main'))


# タスク編集ページ
@app.route('/edit-task/<int:task_id>', methods=['GET', 'POST'])
@login_required
def edit_task(task_id):
    task = Task.query.filter_by(id=task_id).first()

    if request.method == 'POST':
        name = request.form['name']
        limit = request.form['limit']
        if limit:
            limit = datetime.strptime(limit, '%Y-%m-%dT%H:%M')
        else:
            limit = None

        # フォームが空
        if name.strip() == '' or limit == None:
            return render_template(
                'editTask.html',
                page_style='css/form.css',
                page_title='Edit Task',
                task=task,
                error_message='Please fill in all the fields.'
            )

        # 期限が現在時刻より前
        elif limit < datetime.now(limit.tzinfo):
            return render_template(
                'newTask.html',
                page_style='css/form.css',
                page_title='New Task',
                error_message='Limit date must be after now.'
            )

        # タスク編集成功
        else:
            task.name = name
            task.limit = limit
            db.session.commit()
            return redirect(url_for('main'))

    else:
        return render_template(
            'editTask.html',
            page_style='css/form.css',
            page_title='Edit Task',
            task=task
        )


# タスク削除
@app.route('/delete-task/<int:task_id>', methods=['GET'])
@login_required
def delete_task(task_id):
    task = Task.query.filter_by(id=task_id).first()
    db.session.delete(task)
    db.session.commit()
    return redirect(url_for('main'))
