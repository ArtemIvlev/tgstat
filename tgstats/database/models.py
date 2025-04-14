from sqlalchemy import Column, Integer, String, DateTime, JSON, ForeignKey, Text, Boolean
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import relationship
from datetime import datetime

Base = declarative_base()

class ChannelStats(Base):
    __tablename__ = 'channel_stats'

    id = Column(Integer, primary_key=True)
    channel_id = Column(Integer, nullable=False)
    title = Column(String)
    username = Column(String)
    subscribers = Column(Integer)
    raw = Column(JSON)
    date = Column(DateTime, default=datetime.utcnow)

class ChannelParticipant(Base):
    __tablename__ = 'channel_participants'

    id = Column(Integer, primary_key=True)
    channel_id = Column(Integer, nullable=False)
    user_id = Column(Integer, nullable=False)
    username = Column(String)
    first_name = Column(String)
    last_name = Column(String)
    phone = Column(String)
    raw = Column(JSON)
    date = Column(DateTime, default=datetime.utcnow)

class ChannelPost(Base):
    __tablename__ = 'channel_posts'

    id = Column(Integer, primary_key=True)
    channel_id = Column(Integer, nullable=False)
    message_id = Column(Integer, nullable=False)
    date = Column(DateTime)
    text = Column(Text, nullable=True)
    views = Column(Integer)
    forwards = Column(Integer)
    replies = Column(Integer, nullable=True)
    media_type = Column(String, nullable=True)
    raw = Column(JSON)

    # Связь с реакциями
    reactions = relationship("PostReaction", back_populates="post")

class PostReaction(Base):
    __tablename__ = 'post_reactions'

    id = Column(Integer, primary_key=True)
    post_id = Column(Integer, ForeignKey('channel_posts.id'), nullable=False)
    reaction = Column(String)
    count = Column(Integer, default=1)
    date = Column(DateTime, default=datetime.utcnow)

    # Связи
    post = relationship("ChannelPost", back_populates="reactions")

class ChannelActivity(Base):
    __tablename__ = 'channel_activity'

    id = Column(Integer, primary_key=True)
    channel_id = Column(Integer, nullable=False)
    date = Column(DateTime, default=datetime.utcnow)
    total_views = Column(Integer, default=0)
    total_forwards = Column(Integer, default=0)
    total_reactions = Column(Integer, default=0)
    posts_count = Column(Integer, default=0)
    active_hours = Column(JSON)  # Статистика активности по часам
    raw = Column(JSON)

class DiscussionStats(Base):
    __tablename__ = 'discussion_stats'

    id = Column(Integer, primary_key=True)
    channel_id = Column(Integer, nullable=False)
    date = Column(DateTime, default=datetime.utcnow)
    total_comments = Column(Integer, default=0)
    active_users = Column(Integer, default=0)  # Количество активных пользователей в обсуждениях
    comments_per_post = Column(JSON)  # Количество комментариев к каждому посту
    top_commenters = Column(JSON)  # Топ комментаторов
    raw = Column(JSON)
