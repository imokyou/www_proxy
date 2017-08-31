# coding=utf8
from wtforms.validators import ValidationError

class Unique(object):
    def __init__(self, model, field, message=u'该内容已经存在。'):
        self.model = model
        self.field = field
        self.message = message

    def __call__(self, form, field):
        check = self.model.query.filter(self.field == field.data).first()
        if check:
            raise ValidationError(self.message)


class UnExists(object):
    def __init__(self, model, field, message=u'邮箱或密码错误。'):
        self.model = model
        self.field = field
        self.message = message

    def __call__(self, form, field):
        check = self.model.query.filter(self.field == field.data).count()
        if not check:
            raise ValidationError(self.message)
