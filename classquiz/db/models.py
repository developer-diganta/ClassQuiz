#  This Source Code Form is subject to the terms of the Mozilla Public
#  License, v. 2.0. If a copy of the MPL was not distributed with this
#  file, You can obtain one at https://mozilla.org/MPL/2.0/.

import uuid
from datetime import datetime
from typing import Optional

import ormar
from pydantic import BaseModel, Json, validator
from enum import Enum
from . import metadata, database


class UserAuthTypes(Enum):
    LOCAL = "LOCAL"
    GOOGLE = "GOOGLE"
    GITHUB = "GITHUB"


class User(ormar.Model):
    """
    The user model in the database
    """

    id: uuid.UUID = ormar.UUID(primary_key=True, default=uuid.uuid4())
    email: str = ormar.String(unique=True, max_length=100)
    username: str = ormar.String(unique=True, max_length=100)
    password: Optional[str] = ormar.String(max_length=100, nullable=True)
    verified: bool = ormar.Boolean(default=False)
    verify_key: str = ormar.String(unique=True, max_length=100, nullable=True)
    created_at: datetime = ormar.DateTime(default=datetime.now())
    auth_type: UserAuthTypes = ormar.Enum(enum_class=UserAuthTypes, default=UserAuthTypes.LOCAL)
    google_uid: Optional[str] = ormar.String(unique=True, max_length=255, nullable=True)
    avatar: bytes = ormar.LargeBinary(max_length=25000, represent_as_base64_str=True)

    class Meta:
        tablename = "users"
        metadata = metadata
        database = database

    class Config:
        use_enum_values = True


class ApiKey(ormar.Model):
    key: str = ormar.String(max_length=48, min_length=48, primary_key=True)
    user: Optional[User] = ormar.ForeignKey(User)

    class Meta:
        tablename = "api_keys"
        metadata = metadata
        database = database


class UserSession(ormar.Model):
    """
    The user session model for user-sessions
    """

    id: uuid.UUID = ormar.UUID(primary_key=True, default=uuid.uuid4())
    user: Optional[User] = ormar.ForeignKey(User)
    session_key: str = ormar.String(unique=True, max_length=64)
    created_at: datetime = ormar.DateTime(default=datetime.now())
    ip_address: str = ormar.String(max_length=100, nullable=True)
    user_agent: str = ormar.String(max_length=255, nullable=True)
    last_seen: datetime = ormar.DateTime(default=datetime.now())

    class Meta:
        tablename = "user_sessions"
        metadata = metadata
        database = database


class ABCDQuizAnswer(BaseModel):
    right: bool
    answer: str
    color: str | None


class RangeQuizAnswer(BaseModel):
    min: int
    max: int
    min_correct: int
    max_correct: int


class QuizQuestionType(str, Enum):
    ABCD = "ABCD"
    RANGE = "RANGE"


class QuizQuestion(BaseModel):
    question: str
    time: str  # in Secs
    type: None | QuizQuestionType = QuizQuestionType.ABCD
    answers: list[ABCDQuizAnswer] | RangeQuizAnswer
    image: str | None = None

    @validator("answers")
    def answers_not_none_if_abcd_type(cls, v, values):
        if values["type"] == QuizQuestionType.ABCD and len(v) == 0:
            raise ValueError("Answers can't be none if type is ABCD")
        if values["type"] == QuizQuestionType.RANGE and type(v) != RangeQuizAnswer:
            raise ValueError("Answer must be from type RangeQuizAnswer if type is RANGE")
        return v


class QuizInput(BaseModel):
    public: bool = False
    title: str
    description: str
    cover_image: str | None
    background_color: str | None
    questions: list[QuizQuestion]


class Quiz(ormar.Model):
    id: uuid.UUID = ormar.UUID(primary_key=True, default=uuid.uuid4(), nullable=False, unique=True)
    public: bool = ormar.Boolean(default=False)
    title: str = ormar.String(max_length=100)
    description: str = ormar.String(max_length=300, nullable=True)
    created_at: datetime = ormar.DateTime(default=datetime.now())
    updated_at: datetime = ormar.DateTime(default=datetime.now())
    user_id: uuid.UUID = ormar.ForeignKey(User)
    questions: Json[list[QuizQuestion]] = ormar.JSON(nullable=False)
    imported_from_kahoot: Optional[bool] = ormar.Boolean(default=False, nullable=True)
    cover_image: Optional[str] = ormar.Text(nullable=True, unique=False)
    background_color: str | None = ormar.Text(nullable=True, unique=False)

    class Meta:
        tablename = "quiz"
        metadata = metadata
        database = database


class InstanceData(ormar.Model):
    instance_id: uuid.UUID = ormar.UUID(primary_key=True, default=uuid.uuid4(), nullable=False, unique=True)

    class Meta:
        tablename = "instance_data"
        metadata = metadata
        database = database


class Token(BaseModel):
    """
    For JWT
    """

    access_token: str
    token_type: str


class TokenData(BaseModel):
    """
    For JWT
    """

    email: str | None = None


class PlayGame(BaseModel):
    quiz_id: uuid.UUID | str
    description: str
    user_id: uuid.UUID
    title: str
    questions: list[QuizQuestion]
    game_id: uuid.UUID
    game_pin: str
    started: bool = False
    captcha_enabled: bool = False
    cover_image: str | None
    game_mode: str | None
    current_question: int = -1
    background_color: str | None


class GamePlayer(BaseModel):
    username: str
    sid: str


class GameAnswer2(BaseModel):
    username: str
    right: bool
    answer: str


class GameAnswer1(BaseModel):
    id: int
    answers: list[GameAnswer2]


class GameSession(BaseModel):
    admin: str
    game_id: str
    # players: list[GamePlayer | None]
    answers: list[GameAnswer1 | None]


class UpdatePassword(BaseModel):
    old_password: str
    new_password: str
