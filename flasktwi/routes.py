from flask import render_template, url_for, flash, redirect, request, abort
from flasktwi import app, db, bcrypt
from flasktwi.forms import RegistrationForm, LoginForm, UpdateAccountForm, PostForm, ReplyForm
from flasktwi.models import Post, User, Like, Reply, followers
from flask_login import login_user, current_user, logout_user, login_required
from PIL import Image
import secrets
import os


@app.route('/')
def main_page():
    liked_status = []
    page = request.args.get('page', 1, type=int)
    posts = Post.query.order_by(Post.date_posted.desc()).paginate(page=page, per_page=5)
    if current_user.is_authenticated:
        for post in posts.items:
            check = Like.query.filter_by(user_id=current_user.id, post_id=post.id).first()
            if check:
                liked_status.append(check.post_id)


    return render_template('home.html', posts=posts, liked = liked_status, route="main_page")


@app.route('/home')
@login_required
def home():
    page = request.args.get('page', 1, type=int)
    if current_user.is_authenticated:
        posts = Post.query.filter_by(author=current_user).order_by(Post.date_posted.desc()).paginate(page=page, per_page=5)
        return render_template('home.html', posts=posts, image=current_user.image, route="home")
    else:
        return render_template('home.html', posts=posts, route='home')


@app.route('/register', methods=['GET', 'POST'])
def register():
    if current_user.is_authenticated:
        return redirect(url_for('home'))
    form = RegistrationForm()
    if form.validate_on_submit():
        hashed_pwd = bcrypt.generate_password_hash(form.password.data).decode('utf-8')
        user = User(username=form.username.data, email=form.email.data, password=hashed_pwd)
        db.session.add(user)
        db.session.commit()
        flash(f'Account created for {form.username.data}!', 'success')
        return redirect(url_for('login'))
    return render_template('register.html', title='Register', form=form)


@app.route('/login', methods=['POST', 'GET'])
def login():
    if current_user.is_authenticated:
        return redirect(url_for('home'))
    form = LoginForm()
    if form.validate_on_submit():
        user = User.query.filter_by(email=form.email.data).first()
        if user and bcrypt.check_password_hash(user.password, form.password.data):
            login_user(user, remember=form.remember.data)
            next_page = request.args.get('next')
            return redirect(next_page) if next_page else redirect(url_for('home'))
        else:
            flash(f'Wrong email or password', 'danger')
    return render_template('login.html', title='Login', form=form)


@app.route('/about')
def about():
    if current_user.is_authenticated:
        return render_template('about.html', title='About', image=current_user.image)
    else:
        return render_template('about.html', title='About')


@app.route('/logout')
def logout():
    logout_user()
    print(logout_user())
    return redirect(url_for('main_page'))


def save_picture(form_picture):
    random_hex = secrets.token_hex(8)
    _, f_ext = os.path.splitext(form_picture.filename)
    picture_fn = current_user.username + random_hex + f_ext
    picture_path = os.path.join(app.root_path, 'static/profile_pics', picture_fn)
    if f_ext == '.gif':
        form_picture.save(picture_path)
    else:
        output_size = (500, 500)
        i = Image.open(form_picture)
        i.thumbnail(output_size)
        i.save(picture_path)
    return picture_fn


def save_background(form_profile_background):
    random_hex = secrets.token_hex(8)
    _, f_ext = os.path.splitext(form_profile_background.filename)
    picture_fn = current_user.username + random_hex + f_ext
    picture_path = os.path.join(app.root_path, 'static/background_pics', picture_fn)
    form_profile_background.save(picture_path)
    return picture_fn


@app.route('/account', methods=['POST', 'GET'])
@login_required
def account():
    form = UpdateAccountForm()
    if form.validate_on_submit():
        if form.avatar.data:
            if current_user.image != 'default.png':
                os.remove(app.root_path+'/static/profile_pics/'+current_user.image)
            picture_file = save_picture(form.avatar.data)
            current_user.image = picture_file
        if form.profile_background.data:
            if current_user.profile_background != 'None':
                os.remove(app.root_path+'/static/background_pics/'+current_user.profile_background)
            picture_file = save_background(form.profile_background.data)
            current_user.profile_background = picture_file
        current_user.username = form.username.data
        current_user.email = form.email.data
        current_user.about = form.about.data
        db.session.commit()
        flash('Your account has been updated!', 'success')
        return redirect(url_for('account'))
    elif request.method == 'GET':
        form.username.data = current_user.username
        form.email.data = current_user.email
        form.about.data = current_user.about
    return render_template('account.html', title='Account', form=form)


@app.route('/post/new', methods=['POST', 'GET'])
@login_required
def new_post():
    form = PostForm()
    if form.validate_on_submit():
        if form.post_image.data:
            picture_file = save_background(form.post_image.data)
        else:
            picture_file = None
        post = Post(title=form.title.data, content=form.content.data, post_image=picture_file,author=current_user)
        db.session.add(post)
        db.session.commit()
        flash('Post has been created', 'success')
        return redirect(url_for('home'))
    return render_template('create_post.html', title='New Post', form=form, legend='New Post')


@app.route('/post/<int:post_id>')
def post(post_id):
    post = Post.query.get_or_404(post_id)
    reply = Reply.query.filter_by(post_id=post.id).all()
    return render_template('post.html', title=post.title, post=post, replyes=reply)


@app.route('/post/<int:post_id>/update', methods=['POST', 'GET'])
@login_required
def update_post(post_id):
    post = Post.query.get_or_404(post_id)
    if post.author != current_user:
        abort(403)
    form = PostForm()
    if form.validate_on_submit():
        if form.post_image.data:
            if post.post_image != None:
                os.remove(app.root_path+'/static/background_pics/'+post.post_image)
            picture_file = save_background(form.post_image.data)
            current_user.post_image = picture_file
        post.post_image = picture_file
        post.title = form.title.data
        post.content = form.content.data
        db.session.commit()
        flash('Post has been updated', 'success')
        return redirect(url_for('post', post_id=post.id))
    elif request.method == 'GET':
        form.title.data = post.title
        form.content.data = post.content
    return render_template('create_post.html', title='Update Post', form=form, legend='Update Post')


@app.route('/reply/<int:post_id>/<int:reply_id>/update', methods=['POST', 'GET'])
@login_required
def update_reply(reply_id, post_id):
    reply = Reply.query.get_or_404(reply_id)
    if reply.user_replied != current_user:
        abort(403)
    form = ReplyForm()
    if form.validate_on_submit():
        reply.reply = form.content.data
        db.session.commit()
        flash('Reply has been updated', 'success')
        return redirect(url_for('post', post_id=post_id))
    elif request.method == 'GET':
        form.content.data = reply.reply
    return render_template('reply_update.html', title='Update Post', form=form, legend='Update Post', reply=reply)


@app.route('/reply/<int:post_id>', methods=['POST', 'GET'])
@login_required
def reply(post_id):
    post = Post.query.get_or_404(post_id)
    form = ReplyForm()
    if form.validate_on_submit():
        replyes = Reply(post_id=post_id, user_id=current_user.id, reply=form.content.data)
        post.replies += 1
        db.session.add(replyes)
        db.session.commit()
        flash('Replyed', 'success')
        return redirect(url_for('post', post_id=post.id, reply=reply))
    return render_template('reply.html', form=form, legend='Reply to '+ post.author.username, reply=reply, post=post)


@app.route('/post/<int:post_id>/delete', methods=['POST'])
@login_required
def delete_post(post_id):
    post = Post.query.get_or_404(post_id)
    if post.author != current_user:
        abort(403)
    post.replies -= 1
    db.session.delete(post)
    db.session.commit()
    flash('Post has been deleted', 'success')
    return redirect(url_for('home'))


@app.route('/reply/<int:reply_id>/delete', methods=['POST'])
@login_required
def delete_reply(reply_id):
    reply = Reply.query.get_or_404(reply_id)
    post = reply.replied.id
    if reply.replied.author != current_user:
        abort(403)
    reply.replied.replies -= 1
    db.session.delete(reply)
    db.session.commit()
    flash('Reply has been deleted', 'success')
    return redirect(url_for('post', post_id=post))


@app.route('/user/<int:user_id>', methods=['GET'])
def user_page(user_id):
    user = User.query.get_or_404(user_id)
    followers_list_5 = user.followed.limit(5).all()
    followed_list_5 = user.followers.limit(5).all()
    followers_count = len(user.followed.all())
    followed_count = len(user.followers.all())
    if current_user == user.id:
        return url_for('account')
    else:
        return render_template('user.html', user=user, followers_list_5=followers_list_5, followed_list_5=followed_list_5, followers_count=followers_count, followed_count=followed_count)


@app.route('/post/<int:post_id>/like/')
def like(post_id):
    check = Post.query.get_or_404(post_id)
    query_param = request.args.get('reaction')
    post = Post.query.filter_by(id=post_id).first()
    likes_count = post.likes
    user_like = Like.query.filter_by(user_id=current_user.id, post_id=post_id).first()
    if user_like:
        increment = -1
    else:
        increment = 1
    if query_param == 'like':
        like = Like(post_id=post.id, user_id=current_user.id)
        db.session.add(like)
        likes_count += 1
        post.likes = likes_count
    elif query_param == 'dislike':
        delete_like = Like.query.filter_by(post_id=post.id, user_id=current_user.id).first()
        if delete_like is None:
            abort(404)
        db.session.delete(delete_like)
        likes_count -=1
        post.likes = likes_count
    else:
        abort(400)
    db.session.commit()
    data = { post_id : likes_count }
    return data


@app.route('/follow/<int:user_id>')
def follow(user_id):
    user = User.query.get_or_404(user_id)
    if user.id != current_user.id:
        if current_user.followed.filter(followers.c.followed_id == user.id).count() > 0:
            current_user.followed.remove(user)
            flash(f'You have been unfollowed user {user.username}!', 'success')
        else:
            current_user.followed.append(user)
            db.session.commit()
            flash(f'Now you are following user {user.username}!', 'success')
    else:
        flash("Sorry, you can't follow yourself", 'warning')
    return render_template('user.html', user=user)
