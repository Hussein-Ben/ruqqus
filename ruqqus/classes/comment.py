from flask import *
import time
from sqlalchemy import *
from sqlalchemy.orm import relationship, deferred
from random import randint
import math
from .mix_ins import *
from ruqqus.helpers.base36 import *
from ruqqus.helpers.lazy import lazy
from ruqqus.__main__ import Base, db, cache
from .submission import Submission
from .votes import CommentVote
from .flags import CommentFlag
from .boards import Board

class Comment(Base, Age_times, Scores, Stndrd):

    __tablename__="comments"

    id = Column(Integer, primary_key=True)
    author_id = Column(Integer, ForeignKey("users.id"))
    body = Column(String(2000), default=None)
    parent_submission = Column(Integer, ForeignKey("submissions.id"))
    parent_fullname = Column(Integer) #this column is foreignkeyed to comment(id) but we can't do that yet as "comment" class isn't yet defined
    created_utc = Column(Integer, default=0)
    edited_utc = Column(Integer, default=0)
    is_banned = Column(Boolean, default=False)
    body_html = Column(String)
    distinguish_level=Column(Integer, default=0)
    is_deleted = Column(Boolean, default=False)
    is_approved = Column(Integer, default=0)
    approved_utc=Column(Integer, default=0)
    ban_reason=Column(String(256), default='')
    creation_ip=Column(String(64), default='')
    score_disputed=Column(Float, default=0)
    score_hot=Column(Float, default=0)
    score_top=Column(Integer, default=1)

    post=relationship("Submission", lazy="subquery")
    flags=relationship("CommentFlag", lazy="dynamic", backref="comment")
    author=relationship("User", lazy="subquery", primaryjoin="User.id==Comment.author_id")

    #These are virtual properties handled as postgres functions server-side
    #There is no difference to SQLAlchemy, but they cannot be written to
    ups = deferred(Column(Integer, server_default=FetchedValue()))
    downs=deferred(Column(Integer, server_default=FetchedValue()))
    age=Column(Integer, server_default=FetchedValue())
    is_public=Column(Boolean, server_default=FetchedValue())

    score=deferred(Column(Integer, server_default=FetchedValue()))
    

    rank_fiery=deferred(Column(Float, server_default=FetchedValue()))
    rank_hot=deferred(Column(Float, server_default=FetchedValue()))

    flag_count=deferred(Column(Integer, server_default=FetchedValue()))
    over_18=Column(Boolean, server_default=FetchedValue())

    board_id=Column(Integer, server_default=FetchedValue())
    
    

    def __init__(self, *args, **kwargs):
                   

        if "created_utc" not in kwargs:
            kwargs["created_utc"]=int(time.time())

        kwargs["creation_ip"]=request.remote_addr
            
        super().__init__(*args, **kwargs)
                
    def __repr__(self):

        return f"<Comment(id={self.id})"

    @property
    def fullname(self):
        return f"t3_{self.base36id}"

    @property
    def is_top_level(self):
        return self.parent_fullname.startswith("t2_")



    @property
    @lazy
    def board(self):

        if self.post:
            return self.post.board
        else:
            return None
    
    @property
    @lazy
    def parent(self):

        if not self.parent_submission:
            return None

        if self.is_top_level:
            return db.query(Submission).filter_by(id=self.parent_submission).first()
        else:
            return db.query(Comment).filter_by(id=base36decode(self.parent_fullname.split(sep="_")[1])).first()

    @property
    def children(self):

        return db.query(Comment).filter_by(parent_comment=self.id).all()

    @property
    def replies(self):

        if "replies" in self.__dict__:
            return self.__dict__["replies"]
        else:
            return db.query(Comment).filter_by(parent_fullname=self.fullname).all()

    @property
    def permalink(self):

        return f"/post/{self.post.base36id}/comment/{self.base36id}"

    @property
    @cache.memoize(timeout=60)
    def any_descendants_live(self):

        if self.replies==[]:
            return False

        if any([not x.is_banned and not x.is_deleted for x in self.replies]):
            return True

        else:
            return any([x.any_descendants_live for x in self.replies])
        

    def rendered_comment(self, v=None, render_replies=True, standalone=False, level=1):

        if self.is_banned or self.is_deleted:
            if v and v.admin_level>1:
                return render_template("single_comment.html", v=v, c=self, replies=self.replies, render_replies=render_replies, standalone=standalone, level=level)
                
            elif self.any_descendants_live:
                return render_template("single_comment_removed.html", c=self, replies=self.replies, render_replies=render_replies, standalone=standalone, level=level)
            else:
                return ""

        return render_template("single_comment.html", v=v, c=self, replies=self.replies, render_replies=render_replies, standalone=standalone, level=level)

    @property
    def active_flags(self):
        if self.is_approved:
            return 0
        else:
            return self.flag_count

    def visibility_reason(self, v):
        if self.author_id==v.id:
            return "this is your content."
        elif self.board.has_mod(v):
            return f"you are a guildmaster of +{self.board.name}."
        elif self.board.has_contributor(v):
            return f"you are an approved contributor in +{self.board.name}."
        elif self.parent.author_id==v.id:
            return "this is a reply to your content."
        elif v.admin_level >= 4:
            return "you are a Ruqqus admin."

    @property
    @cache.memoize(timeout=60)
    def score_fuzzed(self):
        
        k=0.01
        real = self.score_top
        a = math.floor(real * (1 - k))
        b = math.ceil(real * (1 + k))
        return random.randint(a, b)
        
class Notification(Base):

    __tablename__="notifications"

    id=Column(Integer, primary_key=True)
    user_id=Column(Integer, ForeignKey("users.id"))
    comment_id=Column(Integer, ForeignKey("comments.id"))
    read=Column(Boolean, default=False)

    #Server side computed values (copied from corresponding comment)
    created_utc=Column(Integer, server_default=FetchedValue())
    is_banned=Column(Boolean, server_default=FetchedValue())
    is_deleted=Column(Boolean, server_default=FetchedValue())

    def __repr__(self):

        return f"<Notification(id={self.id})"

    @property
    def comment(self):

        return db.query(Comment).filter_by(id=self.comment_id).first()

    @property
    def board(self):

        return db.query(Board).filter_by(id=self.board_id).first()
