import re
import string
import random
from datetime import datetime, timedelta
from application.services.mongo import MyDatabase

###################################################################

# form validator

###################################################################


class FormValidator:
    def validate_email(self, email: str) -> bool:
        """
        Validate an email address.

        Parameters:
            email (str): The email address to be validated.

        Returns:
            bool: True if the email address is valid; False otherwise.

        Criteria:
        - Must have a valid format with '@' and a top-level domain (TLD).
        - Local part (before '@') must not have spaces or start/end with a space.
        - Domain part (after '@') must not have consecutive dots or special characters.
        - Should not be empty and should contain both local and domain parts.

        Example:
            validate_email("john.doe@example.com") -> True
            validate_email("invalid.email") -> False
        """

        email_regex = r"^[A-Za-z0-9._%+-]+@[A-Za-z0-9-]+(\.[A-Za-z]{2,7})+$"
        if re.match(email_regex, email):
            return True
        return False

    def validate_password(self, password: str) -> bool:
        """
        Validate a password.

        Parameters:
            password (str): The password to be validated.

        Returns:
            bool: True if the password is valid; False otherwise.

        Criteria:
        - At least 8 characters long.
        - At least one uppercase letter.
        - At least one lowercase letter.
        - At least one number.
        - May include special characters.
        - No spaces allowed (leading or trailing).

        Example:
            validate_password("P@ssw0rd") -> True
            validate_password("short") -> False
            validate_password("Pwd 123") -> False
        """

        password_regex = r"^(?=.*[a-z])(?=.*[A-Z])(?=.*\d)(?!.*\s).{8,}$"
        if re.match(password_regex, password):
            return True
        return False

    def validate_username(self, username: str) -> bool:
        """
        Validate a username.

        Parameters:
            username (str): The username to be validated.

        Returns:
            bool: True if the username is valid; False otherwise.

        Criteria:
        - Must consist of letters (both uppercase and lowercase), numbers, hyphens, dots, and underscores.
        - Cannot contain special characters like '@', '#', '^', '~', spaces, or leading/trailing dashes, dots, or underscores.
        - Can be a mix of letters and numbers but should start with a letter.
        """
        username_regex = r"^[a-zA-Z0-9][a-zA-Z0-9.\-_]*[a-zA-Z0-9]$"
        if re.match(username_regex, username):
            return True
        return False

    def validate_blogname(self, blogname: str) -> bool:
        """Check if the blog name is not longer than 20 characters.

        Args:
            blogname (str): plain text blog name.

        Returns:
            bool: True if the blog name is valid.
        """
        blogname_regex = r"^.{1,20}$"
        if re.match(blogname_regex, blogname):
            return True
        return False


###################################################################

# uid generator

###################################################################


class UIDGenerator:
    def __init__(self, db_handler: MyDatabase) -> None:
        self._db_handler = db_handler

    def generate_comment_uid(self) -> str:
        """look into the comment database and give a unique id for new comment

        Returns:
            str: an unique comment uid string
        """

        alphabet = string.ascii_lowercase + string.digits
        while True:
            comment_uid = "".join(random.choices(alphabet, k=8))
            if not self._db_handler.comment.exists("comment_uid", comment_uid):
                return comment_uid

    def generate_post_uid(self) -> str:
        """look into the post database and give a unique id for new post

        Returns:
            str: an unique post uid string
        """
        alphabet = string.ascii_lowercase + string.digits
        while True:
            post_uid = "".join(random.choices(alphabet, k=8))
            if not self._db_handler.post_info.exists("post_uid", post_uid):
                return post_uid


###################################################################

# some other utility functions

###################################################################


def get_today(env):

    if env == "debug":
        today = datetime.now()
    elif env == "prod":
        today = datetime.now() + timedelta(hours=8)
    else:
        raise ValueError("Unknown enviroment argument.")
    return today


def switch_to_bool(switch_value: str | None) -> bool:
    """convert the return value of the bootstrap switch from the form into boolean.

    Args:
        switch_value (str | None): return value of switch checkbox from the form, possible values: "on" and None.

    Returns:
        bool: a boolean value.
    """
    if switch_value is None:
        return False
    return True


def string_truncate(text: str, max_len: int) -> str:
    """Truncate the input string to the given max len, with the trailing dot dot dot.

    If the input is shorter, nothing will be changed.

    Args:
        text (str): string to be truncated.
        max_len (int): shorten the string to this length at maximum (dot dot dot not included).

    Returns:
        str: truncated string.
    """
    if len(text) <= max_len:
        return text
    return f"{text[:max_len]}..."