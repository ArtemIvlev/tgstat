from datetime import datetime, timedelta
from sqlalchemy import func, desc, and_
from tgstats.database.models import PostComment, ChannelPost, CommentReaction
from collections import defaultdict
import pandas as pd

class CommentAnalytics:
    def __init__(self, db):
        self.db = db

    def get_top_commenters(self, channel_id, limit=10):
        """Получает список самых активных комментаторов"""
        top_users = self.db.query(
            PostComment.user_id,
            func.count(PostComment.id).label('comments_count')
        ).filter(
            PostComment.channel_id == channel_id
        ).group_by(
            PostComment.user_id
        ).order_by(
            desc('comments_count')
        ).limit(limit).all()

        return [{'user_id': user_id, 'comments_count': count} 
                for user_id, count in top_users]

    def get_most_commented_posts(self, channel_id, limit=10):
        """Получает список постов с наибольшим количеством комментариев"""
        top_posts = self.db.query(
            ChannelPost,
            func.count(PostComment.id).label('comments_count')
        ).join(
            PostComment, PostComment.post_id == ChannelPost.id
        ).filter(
            ChannelPost.channel_id == channel_id
        ).group_by(
            ChannelPost.id
        ).order_by(
            desc('comments_count')
        ).limit(limit).all()

        return [{
            'post_id': post.id,
            'message_id': post.message_id,
            'text': post.text[:100] + '...' if post.text and len(post.text) > 100 else post.text,
            'date': post.date,
            'views': post.views,
            'comments_count': count
        } for post, count in top_posts]

    def get_hourly_activity(self, channel_id, days=7):
        """Анализирует активность комментариев по часам"""
        since_date = datetime.utcnow() - timedelta(days=days)
        
        comments = self.db.query(
            PostComment
        ).filter(
            and_(
                PostComment.channel_id == channel_id,
                PostComment.date >= since_date
            )
        ).all()

        hourly_stats = defaultdict(int)
        for comment in comments:
            hour = comment.date.hour
            hourly_stats[hour] += 1

        return [{'hour': hour, 'comments_count': count} 
                for hour, count in sorted(hourly_stats.items())]

    def get_daily_activity(self, channel_id, days=30):
        """Анализирует активность комментариев по дням"""
        since_date = datetime.utcnow() - timedelta(days=days)
        
        comments = self.db.query(
            PostComment
        ).filter(
            and_(
                PostComment.channel_id == channel_id,
                PostComment.date >= since_date
            )
        ).all()

        df = pd.DataFrame([{
            'date': comment.date.date(),
            'count': 1
        } for comment in comments])

        if df.empty:
            return []

        daily_stats = df.groupby('date')['count'].sum().reset_index()
        return daily_stats.to_dict('records')

    def get_comment_length_stats(self, channel_id):
        """Анализирует длину комментариев"""
        comments = self.db.query(
            PostComment
        ).filter(
            PostComment.channel_id == channel_id
        ).all()

        lengths = [len(comment.text) if comment.text else 0 for comment in comments]
        
        if not lengths:
            return {
                'avg_length': 0,
                'min_length': 0,
                'max_length': 0,
                'total_comments': 0
            }

        return {
            'avg_length': sum(lengths) / len(lengths),
            'min_length': min(lengths),
            'max_length': max(lengths),
            'total_comments': len(lengths)
        }

    def get_channel_stats(self, channel_id):
        """Получает общую статистику по комментариям канала"""
        total_comments = self.db.query(
            func.count(PostComment.id)
        ).filter(
            PostComment.channel_id == channel_id
        ).scalar()

        total_commenters = self.db.query(
            func.count(func.distinct(PostComment.user_id))
        ).filter(
            PostComment.channel_id == channel_id
        ).scalar()

        posts_with_comments = self.db.query(
            func.count(func.distinct(PostComment.post_id))
        ).filter(
            PostComment.channel_id == channel_id
        ).scalar()

        total_posts = self.db.query(
            func.count(ChannelPost.id)
        ).filter(
            ChannelPost.channel_id == channel_id
        ).scalar()

        return {
            'total_comments': total_comments,
            'total_commenters': total_commenters,
            'posts_with_comments': posts_with_comments,
            'total_posts': total_posts,
            'comments_per_post': total_comments / total_posts if total_posts > 0 else 0,
            'engagement_rate': posts_with_comments / total_posts if total_posts > 0 else 0
        }

    def get_comment_reactions(self, channel_id):
        """Анализирует реакции на комментарии"""
        reactions = self.db.query(
            CommentReaction.reaction,
            func.sum(CommentReaction.count).label('total_count')
        ).join(
            PostComment, CommentReaction.comment_id == PostComment.id
        ).filter(
            PostComment.channel_id == channel_id
        ).group_by(
            CommentReaction.reaction
        ).order_by(
            desc('total_count')
        ).all()

        return [{
            'reaction': reaction,
            'count': count
        } for reaction, count in reactions]

    def get_top_reaction_users(self, channel_id, limit=10):
        """Получает список пользователей, которые чаще всего ставят реакции"""
        top_users = self.db.query(
            CommentReaction.user_id,
            func.count(CommentReaction.id).label('reactions_count')
        ).join(
            PostComment, CommentReaction.comment_id == PostComment.id
        ).filter(
            PostComment.channel_id == channel_id
        ).group_by(
            CommentReaction.user_id
        ).order_by(
            desc('reactions_count')
        ).limit(limit).all()

        return [{
            'user_id': user_id,
            'reactions_count': count
        } for user_id, count in top_users]

    def get_user_reaction_stats(self, channel_id):
        """Получает статистику по реакциям пользователей"""
        # Получаем количество уникальных пользователей, которые ставили реакции
        unique_reactors = self.db.query(
            func.count(func.distinct(CommentReaction.user_id))
        ).join(
            PostComment, CommentReaction.comment_id == PostComment.id
        ).filter(
            PostComment.channel_id == channel_id
        ).scalar() or 0

        # Получаем общее количество реакций
        total_reactions = self.db.query(
            func.count(CommentReaction.id)
        ).join(
            PostComment, CommentReaction.comment_id == PostComment.id
        ).filter(
            PostComment.channel_id == channel_id
        ).scalar() or 0

        return {
            'unique_reactors': unique_reactors,
            'total_reactions': total_reactions,
            'reactions_per_user': total_reactions / unique_reactors if unique_reactors > 0 else 0
        }

    def get_most_reacted_comments(self, channel_id, limit=10):
        """Получает комментарии с наибольшим количеством реакций"""
        comments = self.db.query(
            PostComment,
            func.count(CommentReaction.id).label('total_reactions')
        ).join(
            CommentReaction, PostComment.id == CommentReaction.comment_id
        ).filter(
            PostComment.channel_id == channel_id
        ).group_by(
            PostComment.id
        ).order_by(
            desc('total_reactions')
        ).limit(limit).all()

        result = []
        for comment, total_reactions in comments:
            # Получаем детальную информацию о реакциях
            reactions = self.db.query(
                CommentReaction.reaction,
                CommentReaction.user_id,
                func.count(CommentReaction.id).label('count')
            ).filter(
                CommentReaction.comment_id == comment.id
            ).group_by(
                CommentReaction.reaction,
                CommentReaction.user_id
            ).all()

            reaction_details = []
            for reaction, user_id, count in reactions:
                reaction_details.append({
                    'reaction': reaction,
                    'user_id': user_id,
                    'count': count
                })

            result.append({
                'comment_id': comment.id,
                'text': comment.text[:100] + '...' if comment.text and len(comment.text) > 100 else comment.text,
                'date': comment.date,
                'user_id': comment.user_id,
                'total_reactions': total_reactions,
                'reactions': reaction_details
            })

        return result

    def get_reaction_stats(self, channel_id):
        """Получает общую статистику по реакциям на комментарии"""
        total_reactions = self.db.query(
            func.sum(CommentReaction.count)
        ).join(
            PostComment, CommentReaction.comment_id == PostComment.id
        ).filter(
            PostComment.channel_id == channel_id
        ).scalar() or 0

        comments_with_reactions = self.db.query(
            func.count(func.distinct(CommentReaction.comment_id))
        ).join(
            PostComment, CommentReaction.comment_id == PostComment.id
        ).filter(
            PostComment.channel_id == channel_id
        ).scalar() or 0

        total_comments = self.db.query(
            func.count(PostComment.id)
        ).filter(
            PostComment.channel_id == channel_id
        ).scalar() or 0

        return {
            'total_reactions': total_reactions,
            'comments_with_reactions': comments_with_reactions,
            'total_comments': total_comments,
            'reactions_per_comment': total_reactions / total_comments if total_comments > 0 else 0,
            'reaction_rate': comments_with_reactions / total_comments if total_comments > 0 else 0
        } 