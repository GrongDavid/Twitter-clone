"""User model tests."""

# run these tests like:
#
#    python -m unittest test_user_model.py


import os
from unittest import TestCase

from models import db, User, Message, Follows

# BEFORE we import our app, let's set an environmental variable
# to use a different database for tests (we need to do this
# before we import our app, since that will have already
# connected to the database

os.environ['DATABASE_URL'] = "postgresql:///warbler-test"


# Now we can import app

from app import app

# Create our tables (we do this here, so we only create the tables
# once for all tests --- in each test, we'll delete the data
# and create fresh new clean test data

db.create_all()


class UserModelTestCase(TestCase):
    """Test views for messages."""

    def setUp(self):
        """Create test client, add sample data."""

        User.query.delete()
        Message.query.delete()
        Follows.query.delete()

        user1 = User.signup('user1', 'testemail1@gmail.com', 'abc123', None)
        user1.id = 1

        user2 = User.signup('user2', 'testemail2@gmail.com', 'abc123', None)
        user2.id = 2

        db.session.commit()

        u1 = User.query.get(1)
        u2 = User.query.get(2)

        self.u1 = u1

        self.u2 = u2

        self.client = app.test_client()
    
    def tearDown(self):
        down = super().tearDown()
        db.session.rollback()
        return down

    def test_user_model(self):
        """Does basic model work?"""

        u = User(
            email="test@test.com",
            username="testuser",
            password="HASHED_PASSWORD"
        )

        db.session.add(u)
        db.session.commit()

        # User should have no messages & no followers
        self.assertEqual(len(u.messages), 0)
        self.assertEqual(len(u.followers), 0)

    def test_follows(self):
        self.u1.following.append(self.u2)
        db.session.commit()

        # User 2 should be following none and have 1 follower
        self.assertEqual(len(self.u2.following), 0)
        self.assertEqual(len(self.u2.followers), 1)

        # User 1 should have no followers but be following 1
        self.assertEqual(len(self.u1.followers), 0)
        self.assertEqual(len(self.u1.following), 1)

        self.assertEqual(self.u2.followers[0].id, self.u1.id)
        self.assertEqual(self.u1.following[0].id, self.u2.id)

    def test_is_following(self):
        self.u1.following.append(self.u2)
        db.session.commit()

        # User 1 should be following user 2
        self.assertTrue(self.u1.is_following(self.u2))
        self.assertFalse(self.u2.is_following(self.u1))
        

    def test_is_followed_by(self):
        self.u1.following.append(self.u2)
        db.session.commit()

        # Similar to test_is_following but using is_followed_by
        self.assertTrue(self.u2.is_followed_by(self.u1))
        self.assertFalse(self.u1.is_followed_by(self.u2))

    def test_signup(self):
        user = User.signup("user3", "testemail3@gmail.com", "abc123", None)
        user.id = 3
        db.session.commit()

        user = User.query.get(3)
    
        self.assertEqual(user.username, "user3")
        self.assertEqual(user.email, "testemail3@gmail.com")

        # Should not be equal as password should be encrypted
        self.assertNotEqual(user.password, "abc123")

    def test_authentication(self):
        u = User.authenticate(self.u1.username, "abc123")
        self.assertEqual(u.id, self.u1.id)
    
    def test_wrong_username(self):
        self.assertFalse(User.authenticate("wrong", "abc123"))

    def test_wrong_password(self):
        self.assertFalse(User.authenticate(self.u1.username, "wrong"))

