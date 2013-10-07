from django.contrib.auth.models import Group
from guardian.shortcuts import assign_perm, remove_perm
from guardian.shortcuts import get_perms

class ClassGroupPermissions(object):
    administrator = "administrator"
    teacher = "teacher"
    student = "student"
    parent = "parent"
    none = "none"

    PERMISSION_LEVELS = {
        administrator: 4,
        teacher: 3,
        student: 2,
        parent: 1,
        none: 0
    }

    def __init__(self, cg):
        self.cg = cg

    def get_group(self, name):
        group, created = Group.objects.get_or_create(name="{0}_{1}_{2}".format("classgroup", self.cg.name, name))
        return group

    def get_teacher_group(self):
        return self.get_group(self.teacher)

    def get_student_group(self):
        return self.get_group(self.student)

    def get_administrator_group(self):
        return self.get_group(self.administrator)

    def get_parent_group(self):
        return self.get_group(self.parent)

    def setup(self):
        admin_group = self.get_administrator_group()
        self.grant_administrator_permissions(admin_group)

        parent_group = self.get_parent_group()
        self.grant_student_permissions(parent_group)

        student_group = self.get_student_group()
        self.grant_student_permissions(student_group)

        teacher_group = self.get_teacher_group()
        self.grant_teacher_permissions(teacher_group)

    def delete(self):
        groups = [self.get_administrator_group(), self.get_parent_group(), self.get_teacher_group(), self.get_student_group()]
        for g in groups:
            g.delete()

    def grant_student_permissions(self, group):
        pass

    def grant_teacher_permissions(self, group):
        self.grant_student_permissions(group)
        assign_perm("change_classgroup", group, self.cg)

    def grant_administrator_permissions(self, group):
        self.grant_teacher_permissions(group)
        assign_perm("delete_classgroup", group, self.cg)

    def check_is_student(self, user):
        return self.get_student_group() in user.groups.all()

    def check_is_teacher(self, user):
        return self.get_teacher_group() in user.groups.all()

    def check_is_administrator(self, user):
        return self.get_administrator_group() in user.groups.all()

    def check_is_parent(self, user):
        return self.get_parent_group() in user.groups.all()

    def get_access_level(self, user):
        if self.check_is_administrator(user):
            return self.administrator
        elif self.check_is_teacher(user):
            return self.teacher
        elif self.check_is_student(user):
            return self.student
        elif self.check_is_parent(user):
            return self.parent
        else:
            return self.none

    @property
    def groups(self):
        return [self.get_student_group(), self.get_teacher_group(), self.get_parent_group(), self.get_administrator_group()]

    def remove_all_access(self, user):
        for group in self.groups:
            user.groups.remove(group)

    def assign_access_level(self, user, access_level):
        self.remove_all_access(user)

        if access_level == self.administrator:
            user.groups.add(self.get_administrator_group())
            user.groups.add(self.get_teacher_group())
            user.groups.add(self.get_student_group())
        elif access_level == self.teacher:
            user.groups.add(self.get_teacher_group())
            user.groups.add(self.get_student_group())
        elif access_level == self.student:
            user.groups.add(self.get_student_group())
        elif access_level == self.parent:
            user.groups.add(self.get_student_group())

    def remove_perms(self, permission_name, obj):
        levels = [self.parent, self.administrator, self.teacher, self.student]
        for l in levels:
            group = getattr(self, "get_{0}_group".format(l))()
            remove_perm(permission_name, group, obj)

    @classmethod
    def access_level(cls, cg, user):
        cg_perm = cls(cg)
        return cg_perm.get_access_level(user)

    @classmethod
    def is_teacher(cls, cg, user):
        cg_perm = cls(cg)
        return cg_perm.check_is_teacher(user) or cg.owner == user

    @classmethod
    def is_administrator(cls, cg, user):
        cg_perm = cls(cg)
        return cg_perm.check_is_administrator(user) or cg.owner == user

    @classmethod
    def is_student(cls, cg, user):
        cg_perm = cls(cg)
        return cg_perm.check_is_student(user) or cg.owner == user

    @classmethod
    def assign_perms(cls, cg, obj, permission_name, level):
        cg_perm = cls(cg)
        cg_perm.remove_perms(permission_name, obj)
        group = getattr(cg_perm, "get_{0}_group".format(level))()
        assign_perm(permission_name, group, obj)

    @classmethod
    def get_permission_level(cls, cg, obj, permission_name):
        cg_perm = cls(cg)
        groups = [
            [cls.parent, cg_perm.get_parent_group()],
            [cls.student, cg_perm.get_student_group()],
            [cls.teacher, cg_perm.get_teacher_group()],
            [cls.administrator, cg_perm.get_administrator_group()],
        ]

        for g in groups:
            if permission_name in get_perms(g[1], obj):
                return g[0]
        return cls.student
