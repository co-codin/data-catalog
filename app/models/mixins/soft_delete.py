from sqlalchemy_easy_softdelete.mixin import generate_soft_delete_mixin_class
from sqlalchemy_easy_softdelete.hook import IgnoredTable
from datetime import datetime

class SoftDeleteMixin(generate_soft_delete_mixin_class()):
    deleted_at: datetime