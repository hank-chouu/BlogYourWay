from bcrypt import checkpw, gensalt, hashpw
from flask import Blueprint, flash, redirect, render_template, request, session, url_for
from flask_login import current_user, login_required, logout_user

from blogyourway.helpers.common import string_truncate, switch_to_bool
from blogyourway.helpers.posts import create_post, paging, post_utils, update_post
from blogyourway.helpers.users import user_utils
from blogyourway.services.logging import logger, logger_utils
from blogyourway.services.mongo import mongodb

backstage = Blueprint("backstage", __name__, template_folder="../templates/backstage/")


@backstage.route("/", methods=["GET"])
@login_required
def backstage_root():
    return redirect(url_for("backstage.overview"))


@backstage.route("/overview", methods=["GET"])
@login_required
def overview():
    ###################################################################

    # status control / early returns

    ###################################################################

    logger_utils.backstage(username=current_user.username, tab="overview")

    ###################################################################

    # main actions

    ###################################################################

    user = mongodb.user_info.find_one({"username": current_user.username})
    user["created_at"] = user["created_at"].strftime("%b %d, %Y")

    ###################################################################

    # return page content

    ###################################################################

    return render_template(
        "overview.html",
        user=user,
        traffic={"labels": ["2024-01-01", "2024-01-02"], "data": [2, 1]},
        index_page_traffic={"/@test/loll": 3},
        total_pv=1,
        total_uv=2,
    )


@backstage.route("/posts", methods=["GET", "POST"])
@login_required
def post_control():
    ###################################################################

    # status control / early returns

    ###################################################################

    session["user_current_tab"] = "posts"
    logger_utils.backstage(username=current_user.username, tab="posts")

    ###################################################################

    # main actions

    ###################################################################

    current_page = request.args.get("page", default=1, type=int)
    user = mongodb.user_info.find_one({"username": current_user.username})

    if request.method == "POST":
        # logging for this is inside the create post function
        post_uid = create_post(request)
        logger.debug(f"post {post_uid} has been created.")
        flash("New post published successfully!", category="success")

    # query through posts
    # 20 posts for each page
    POSTS_EACH_PAGE = 20
    pagination = paging.setup(current_user.username, current_page, POSTS_EACH_PAGE)
    posts = post_utils.find_posts_with_pagination(
        username=current_user.username, page_number=current_page, posts_per_page=POSTS_EACH_PAGE
    )
    for post in posts:
        post["title"] = string_truncate(post["title"], 30)
        post["created_at"] = post["created_at"].strftime("%Y-%m-%d %H:%M:%S")
        post["views"] = format(post["views"], ",")
        comment_count = mongodb.comment.count_documents({"post_uid": post["post_uid"]})
        post["comments"] = format(comment_count, ",")

    logger_utils.pagination(tab="posts", num_of_posts=len(posts))

    ###################################################################

    # return page content

    ###################################################################

    return render_template("posts.html", user=user, posts=posts, pagination=pagination)


@backstage.route("/edit/posts/<post_uid>", methods=["GET"])
@login_required
def edit_post_get(post_uid):
    ###################################################################

    # status control / early returns

    ###################################################################

    logger_utils.backstage(username=current_user.username, tab="edit_post")

    ###################################################################

    # main actions

    ###################################################################

    user = mongodb.user_info.find({"username": current_user.username})
    target_post = post_utils.get_full_post(post_uid)
    target_post["tags"] = ", ".join(target_post["tags"])

    ###################################################################

    # return page content

    ###################################################################

    return render_template("edit-post.html", post=target_post, user=user)


@backstage.route("/edit/posts/<post_uid>", methods=["POST"])
@login_required
def edit_post_post(post_uid):
    ###################################################################

    # main actions

    ###################################################################

    update_post(post_uid, request)
    logger.debug(f"post {post_uid} is updated.")
    truncated_post_title = string_truncate(
        mongodb.post_info.find_one({"post_uid": post_uid}).get("title"), max_len=20
    )
    flash(f'Your post "{truncated_post_title}" has been updated!', category="success")

    ###################################################################

    # return page content

    ###################################################################

    return redirect(url_for("backstage.post_control"))


@backstage.route("/edit-featured", methods=["GET"])
@login_required
def edit_featured():
    ###################################################################

    # status control / early returns

    ###################################################################

    ###################################################################

    # main actions

    ###################################################################

    post_uid = request.args.get("uid")
    truncated_post_title = string_truncate(
        mongodb.post_info.find_one({"post_uid": post_uid}).get("title"), max_len=20
    )

    if request.args.get("featured") == "to_true":
        updated_featured_status = True
        flash(
            f'Your post "{truncated_post_title}" is now featured on the home page!',
            category="success",
        )

    else:
        updated_featured_status = False
        flash(
            f'Your post "{truncated_post_title}" is now removed from the home page!',
            category="success",
        )

    mongodb.post_info.update_values(
        filter={"post_uid": post_uid}, update={"featured": updated_featured_status}
    )
    logger.debug(
        f"featuring status for post {post_uid} is now set to {updated_featured_status}"
    )

    ###################################################################

    # return page content

    ###################################################################

    return redirect(url_for("backstage.post_control"))


@backstage.route("/edit-archived", methods=["GET"])
@login_required
def edit_archived():
    ###################################################################

    # status control / early returns

    ###################################################################

    ###################################################################

    # main actions

    ###################################################################

    post_uid = request.args.get("uid")
    truncated_post_title = string_truncate(
        mongodb.post_info.find_one({"post_uid": post_uid}).get("title"), max_len=20
    )
    if request.args.get("archived") == "to_true":
        updated_archived_status = True
        flash(f'Your post "{truncated_post_title}" is now archived!', category="success")
    else:
        updated_archived_status = False
        flash(
            f'Your post "{truncated_post_title}" is now restored from the archive!',
            category="success",
        )

    mongodb.post_info.update_values(
        filter={"post_uid": post_uid}, update={"archived": updated_archived_status}
    )
    logger.debug(f"archive status for post {post_uid} is now set to {updated_archived_status}")

    ###################################################################

    # return page contents

    ###################################################################

    if session["user_current_tab"] == "posts":
        return redirect(url_for("backstage.post_control"))

    elif session["user_current_tab"] == "archive":
        return redirect(url_for("backstage.archive_control"))


@backstage.route("/about", methods=["GET"])
@login_required
def about_control_get():
    ###################################################################

    # status control / early returns

    ###################################################################

    logger_utils.backstage(username=current_user.username, tab="about")

    ###################################################################

    # main actions

    ###################################################################

    user_info = mongodb.user_info.find_one({"username": current_user.username})
    user_about = mongodb.user_about.find_one({"username": current_user.username})
    user = user_info | user_about

    ###################################################################

    # return page content

    ###################################################################

    return render_template("edit-about.html", user=user)


@backstage.route("/about", methods=["POST"])
@login_required
def about_control_post():
    ###################################################################

    # main actions

    ###################################################################

    user_info = mongodb.user_info.find_one({"username": current_user.username})
    user_about = mongodb.user_about.find_one({"username": current_user.username})
    user = user_info | user_about

    form = request.form.to_dict()
    updated_info = {"profile_img_url": form["profile_img_url"], "short_bio": form["short_bio"]}
    updated_about = {"about": form["about"]}
    mongodb.user_info.update_values(filter={"username": user["username"]}, update=updated_info)
    mongodb.user_about.update_values(
        filter={"username": user["username"]}, update=updated_about
    )
    user.update(updated_info)
    user.update(updated_about)
    logger.debug(f"information for user {current_user.username} has been updated")
    flash("Information updated!", category="success")

    ###################################################################

    # return page content

    ###################################################################

    return render_template("edit-about.html", user=user)


@backstage.route("/archive", methods=["GET"])
@login_required
def archive_control():
    ###################################################################

    # status control / early returns

    ###################################################################

    session["user_current_tab"] = "archive"
    logger_utils.backstage(username=current_user.username, tab="archive")

    ###################################################################

    # main actions

    ###################################################################

    user = mongodb.user_info.find_one({"username": current_user.username})
    posts = post_utils.find_all_archived_posts_info(current_user.username)
    for post in posts:
        post["created_at"] = post["created_at"].strftime("%Y-%m-%d %H:%M:%S")
        post["views"] = format(post["views"], ",")
        comment_count = mongodb.comment.count_documents({"post_uid": post["post_uid"]})
        post["comments"] = format(comment_count, ",")

    logger_utils.pagination(tab="archive", num_of_posts=len(posts))

    ###################################################################

    # return page contents

    ###################################################################

    return render_template("archive.html", user=user, posts=posts)


@backstage.route("/delete/post", methods=["GET"])
@login_required
def delete_post():
    ###################################################################

    # status control / early returns

    ###################################################################

    post_uid = request.args.get("uid")

    ###################################################################

    # main actions

    ###################################################################

    truncated_post_title = string_truncate(
        mongodb.post_info.find_one({"post_uid": post_uid}).get("title"), max_len=20
    )
    mongodb.post_info.delete_one({"post_uid": post_uid})
    mongodb.post_content.delete_one({"post_uid": post_uid})
    logger.debug(f"post {post_uid} has been deleted")
    flash(f'Your post "{truncated_post_title}" has been deleted!', category="success")

    ###################################################################

    # return page contents

    ###################################################################

    return redirect(url_for("backstage.archive_control"))


@backstage.route("/social-links", methods=["GET"])
@login_required
def social_links_control_get():
    ###################################################################

    # status control / early returns

    ###################################################################

    logger_utils.backstage(username=current_user.username, tab="social-links")

    ###################################################################

    # main actions

    ###################################################################

    user = mongodb.user_info.find_one({"username": current_user.username})
    social_links = user["social_links"]

    ###################################################################

    # return page content

    ###################################################################

    return render_template("social-links.html", social_links=social_links, user=user)


@backstage.route("/social-links", methods=["POST"])
@login_required
def social_links_control_post():
    ###################################################################

    # main actions

    ###################################################################

    user = mongodb.user_info.find_one({"username": current_user.username})
    form = request.form.to_dict()
    form_values = list(form.values())

    updated_links = []
    for i in range(0, len(form_values), 2):
        updated_links.append({"platform": form_values[i + 1], "url": form_values[i]})
    mongodb.user_info.update_values(
        filter={"username": current_user.username}, update={"social_links": updated_links}
    )
    logger.debug(f"social links for {current_user.username} has been updated.")
    flash("Social Links updated!", category="success")

    ###################################################################

    # return page content

    ###################################################################

    return render_template("social-links.html", social_links=updated_links, user=user)


@backstage.route("/theme", methods=["GET", "POST"])
@login_required
def theme_control():
    ###################################################################

    # status control / early returns

    ###################################################################

    logger_utils.backstage(username=current_user.username, tab="theme")

    ###################################################################

    # main actions

    ###################################################################

    user = mongodb.user_info.find_one({"username": current_user.username})

    ###################################################################

    # return page contents

    ###################################################################

    return render_template("theme.html", user=user)


@backstage.route("/settings", methods=["GET"])
@login_required
def settings_control_get():
    ###################################################################

    # status control / early returns

    ###################################################################

    logger_utils.backstage(username=current_user.username, tab="settings")

    ###################################################################

    # main actions

    ###################################################################

    user = mongodb.user_info.find_one({"username": current_user.username})

    ###################################################################

    # return page contents

    ###################################################################

    return render_template("settings.html", user=user)


@backstage.route("/settings", methods=["POST"])
@login_required
def settings_control_post():
    ###################################################################

    # main actions

    ###################################################################

    general = request.form.get("general")
    change_pw = request.form.get("changepw")
    delete_account = request.form.get("delete-account")

    if general is not None:
        cover_url = request.form.get("cover_url")
        blogname = request.form.get("blogname")
        enable_changelog = switch_to_bool(request.form.get("changelog_enabled"))
        enable_portfolio = switch_to_bool(request.form.get("gallery_enabled"))

        mongodb.user_info.update_values(
            filter={"username": current_user.username},
            update={
                "cover_url": cover_url,
                "blogname": blogname,
                "changelog_enabled": enable_changelog,
                "gallery_enabled": enable_portfolio,
            },
        )
        logger.debug(f"general settings for {current_user.username} has been updated")
        flash("Update succeeded!", category="success")

    elif change_pw is not None:
        current_pw_input = request.form.get("current")
        encoded_current_pw_input = current_pw_input.encode("utf8")
        new_pw = request.form.get("new")

        user_creds = mongodb.user_creds.find_one({"username": current_user.username})
        user = mongodb.user_info.find_one({"username": current_user.username})
        encoded_valid_user_pw = user_creds["password"].encode("utf8")

        # check pw
        if not checkpw(encoded_current_pw_input, encoded_valid_user_pw):
            logger.debug("invalid old password when changing password.")
            flash("Current password is invalid. Please try again.", category="error")
            return render_template("settings.html", user=user)

        # update new password
        hashed_new_pw = hashpw(new_pw.encode("utf-8"), gensalt(12)).decode("utf-8")
        mongodb.user_creds.update_values(
            filter={"username": current_user.username}, update={"password": hashed_new_pw}
        )
        logger.debug(f"password for user {current_user.username} has been updated.")
        flash("Password update succeeded!", category="success")

    elif delete_account is not None:
        current_pw_input = request.form.get("delete-confirm-pw")
        encoded_current_pw_input = current_pw_input.encode("utf8")
        username = current_user.username
        user = mongodb.user_info.find_one({"username": username})
        user_creds = mongodb.user_creds.find_one({"username": username})
        encoded_valid_user_pw = user_creds["password"].encode("utf8")

        if not checkpw(encoded_current_pw_input, encoded_valid_user_pw):
            flash("Access denied, bacause password is invalid.", category="error")
            return render_template("settings.html", user=user)

        # deletion procedure
        logout_user()
        logger_utils.logout(request=request)
        user_utils.delete_user(username)
        flash("Account deleted successfully!", category="success")
        logger.debug(f"User {username} has been deleted.")
        return redirect(url_for("blog.register_get"))

    user = mongodb.user_info.find_one({"username": current_user.username})

    ###################################################################

    # return page content

    ###################################################################

    return render_template("settings.html", user=user)


@backstage.route("/logout", methods=["GET"])
@login_required
def logout():
    ###################################################################

    # main actions

    ###################################################################

    username = current_user.username
    print(current_user.email)
    logout_user()
    logger_utils.logout(request=request, username=username)

    ###################################################################

    # return page contents

    ###################################################################

    return redirect(url_for("blog.home", username=username))
