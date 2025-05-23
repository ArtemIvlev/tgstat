from sqlalchemy import Column, Integer, String, DateTime, JSON, ForeignKey, Text, Boolean, BigInteger, Index, Float, UniqueConstraint
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import relationship, foreign
from datetime import datetime

Base = declarative_base()

class ChannelStats(Base):
    __tablename__ = 'channel_stats'

    id = Column(Integer, primary_key=True)
    channel_id = Column(BigInteger, nullable=False)
    title = Column(String)
    username = Column(String)
    subscribers = Column(Integer)
    raw = Column(JSON)
    date = Column(DateTime, default=datetime.utcnow)

class ChannelParticipant(Base):
    __tablename__ = 'channel_participants'

    id = Column(Integer, primary_key=True)
    channel_id = Column(BigInteger, nullable=False)
    user_id = Column(BigInteger, nullable=False)
    first_name = Column(String)
    last_name = Column(String)
    username = Column(String)
    phone = Column(String)
    is_bot = Column(Boolean, default=False)
    raw = Column(JSON)
    date = Column(DateTime, default=datetime.utcnow)
    gender = Column(String)  # 'male', 'female', 'unknown'
    gender_confidence = Column(Float)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    left_at = Column(DateTime, nullable=True)  # Дата когда участник покинул канал

    __table_args__ = (
        Index('idx_channel_participants_channel_id', 'channel_id'),
        Index('idx_channel_participants_user_id', 'user_id'),
        UniqueConstraint('channel_id', 'user_id', name='uq_channel_participants_channel_user')
    )

class ChannelPost(Base):
    __tablename__ = 'channel_posts'

    id = Column(Integer, primary_key=True)
    channel_id = Column(BigInteger, nullable=False)
    message_id = Column(BigInteger, nullable=False)
    date = Column(DateTime)
    text = Column(Text, nullable=True)
    views = Column(Integer)
    forwards = Column(Integer)
    replies = Column(Integer, nullable=True)
    media_type = Column(String, nullable=True)
    raw = Column(JSON)

    # Связь с реакциями
    reactions = relationship("PostReaction", back_populates="post")
    comments = relationship("PostComment", back_populates="post")

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
    channel_id = Column(BigInteger, nullable=False)
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
    channel_id = Column(BigInteger, nullable=False)
    date = Column(DateTime, default=datetime.utcnow)
    total_comments = Column(Integer, default=0)
    active_users = Column(Integer, default=0)  # Количество активных пользователей в обсуждениях
    comments_per_post = Column(JSON)  # Количество комментариев к каждому посту
    top_commenters = Column(JSON)  # Топ комментаторов
    raw = Column(JSON)

class HourlyActivity(Base):
    """Модель для хранения почасовой статистики активности канала"""
    __tablename__ = 'hourly_activity'

    id = Column(Integer, primary_key=True)
    channel_id = Column(BigInteger, nullable=False)
    date = Column(DateTime, nullable=False)
    hour = Column(Integer, nullable=False)  # 0-23
    views = Column(Integer, default=0)
    forwards = Column(Integer, default=0)
    reactions = Column(Integer, default=0)
    posts_count = Column(Integer, default=0)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    def __repr__(self):
        return f"<HourlyActivity(channel_id={self.channel_id}, date={self.date}, hour={self.hour})>"

    # Индекс для быстрого поиска по дате и часу
    __table_args__ = (
        Index('idx_hourly_activity_date_hour', 'date', 'hour'),
    )

class PostComment(Base):
    __tablename__ = 'post_comments'

    id = Column(Integer, primary_key=True)
    channel_id = Column(BigInteger, nullable=False)
    post_id = Column(Integer, ForeignKey('channel_posts.id'), nullable=False)
    message_id = Column(BigInteger, nullable=False)  # ID комментария в Telegram
    user_id = Column(BigInteger, nullable=False)  # ID пользователя, оставившего комментарий
    text = Column(Text, nullable=True)
    date = Column(DateTime)
    views = Column(Integer, default=0)
    forwards = Column(Integer, default=0)
    likes = Column(Integer, default=0)  # Количество лайков
    raw = Column(JSON)  # Сырые данные комментария

    # Связи
    post = relationship("ChannelPost", back_populates="comments")
    reactions = relationship("CommentReaction", 
                           primaryjoin="foreign(PostComment.message_id)==CommentReaction.comment_id",
                           back_populates="comment")

    __table_args__ = (
        Index('idx_post_comments_channel_id', 'channel_id'),
        Index('idx_post_comments_post_id', 'post_id'),
        Index('idx_post_comments_user_id', 'user_id'),
        Index('idx_post_comments_date', 'date'),
    )

class CommentReaction(Base):
    """Реакции на комментарии"""
    __tablename__ = 'comment_reactions'

    id = Column(Integer, primary_key=True)
    comment_id = Column(BigInteger, nullable=False)
    user_id = Column(BigInteger, nullable=False)
    reaction = Column(String(32), nullable=False)  # Используем String для хранения эмодзи
    count = Column(Integer, default=1)  # Добавляем атрибут count
    date = Column(DateTime, nullable=False)

    comment = relationship("PostComment",
                         primaryjoin="foreign(PostComment.message_id)==CommentReaction.comment_id",
                         back_populates="reactions")

    __table_args__ = (
        Index('ix_comment_reactions_comment_id', 'comment_id'),
        Index('ix_comment_reactions_user_id', 'user_id'),
        Index('ix_comment_reactions_date', 'date'),
    )
